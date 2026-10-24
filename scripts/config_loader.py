#!/usr/bin/env python3
"""
config_loader.py — Carrega, valida e expõe a configuração central do pipeline.

Uso típico no pipeline:
    from scripts.config_loader import load_config, get_palette

    cfg = load_config()
    print(cfg.tts.voice)                       # voz vinda do YAML
    palette = get_palette(cfg.video.default_palette)
    print(palette.primary)

Uso via CLI (para inspeção/depuração):
    python scripts/config_loader.py            # imprime resumo
    python scripts/config_loader.py --palette dark-neon
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover
    print("❌ Dependência 'pyyaml' não instalada. Rode: pip install -r requirements.txt")
    sys.exit(1)


# Raiz do projeto = pasta pai de scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
PALETTES_PATH = PROJECT_ROOT / "config" / "palettes.json"

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
RESOLUTION_RE = re.compile(r"^\d+x\d+$")


class ConfigError(ValueError):
    """Erro de configuração inválida."""


# ---------------------------------------------------------------------------
# Estruturas tipadas
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PathsConfig:
    input_dir: str
    output_dir: str
    prompts_dir: str
    temp_dir: str


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int
    timeout_seconds: int


@dataclass(frozen=True)
class TTSConfig:
    provider: str
    voice: str
    rate: str
    volume: str
    pitch: str
    sample_rate: int


@dataclass(frozen=True)
class VideoConfig:
    default_palette: str
    resolution: str
    fps: int
    video_bitrate: str
    audio_bitrate: str
    subtitle_font: str
    subtitle_font_size: int


@dataclass(frozen=True)
class Palette:
    name: str
    primary: str
    accent: str
    text: str
    background: str


@dataclass(frozen=True)
class AppConfig:
    paths: PathsConfig
    llm: LLMConfig
    tts: TTSConfig
    video: VideoConfig
    resolutions: Dict[str, str] = field(default_factory=dict)
    palettes: Dict[str, Palette] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers de validação
# ---------------------------------------------------------------------------

def _require_mapping(data: Any, key: str, ctx: str) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError(f"[{ctx}] esperado objeto/dicionário, recebido {type(data).__name__}")
    return data


def _require(data: Dict[str, Any], field_name: str, ctx: str) -> Any:
    if field_name not in data:
        raise ConfigError(f"[{ctx}] campo obrigatório ausente: '{field_name}'")
    return data[field_name]


def _as_float(value: Any, ctx: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"[{ctx}] esperado número, recebido {value!r}")


def _as_int(value: Any, ctx: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"[{ctx}] esperado inteiro, recebido {value!r}")
    return value


def _validate_hex(color: str, ctx: str) -> str:
    if not isinstance(color, str) or not HEX_RE.match(color):
        raise ConfigError(f"[{ctx}] cor hexadecimal inválida: {color!r} (use #RRGGBB)")
    return color


def _validate_resolution(value: str, ctx: str) -> str:
    if not isinstance(value, str) or not RESOLUTION_RE.match(value):
        raise ConfigError(f"[{ctx}] resolução inválida: {value!r} (use LARGURAxALTURA, ex.: 1080x1920)")
    return value


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------

def _load_palettes(path: Path = PALETTES_PATH) -> Dict[str, Palette]:
    if not path.exists():
        raise ConfigError(f"Arquivo de paletas não encontrado: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"palettes.json inválido: {exc}") from exc

    if not isinstance(raw, dict) or not raw:
        raise ConfigError("palettes.json deve ser um objeto JSON não vazio")

    palettes: Dict[str, Palette] = {}
    required_keys = {"primary", "accent", "text", "background"}
    for name, entry in raw.items():
        if not isinstance(entry, dict):
            raise ConfigError(f"[palette:{name}] deve ser um objeto")
        missing = required_keys - entry.keys()
        if missing:
            raise ConfigError(f"[palette:{name}] chaves ausentes: {sorted(missing)}")
        palettes[name] = Palette(
            name=name,
            primary=_validate_hex(entry["primary"], f"palette:{name}.primary"),
            accent=_validate_hex(entry["accent"], f"palette:{name}.accent"),
            text=_validate_hex(entry["text"], f"palette:{name}.text"),
            background=_validate_hex(entry["background"], f"palette:{name}.background"),
        )
    return palettes


def load_config(
    config_path: Path = CONFIG_PATH,
    palettes_path: Path = PALETTES_PATH,
) -> AppConfig:
    """Carrega e valida config.yaml + palettes.json. Lança ConfigError se inválido."""
    if not config_path.exists():
        raise ConfigError(f"Arquivo de configuração não encontrado: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"config.yaml inválido: {exc}") from exc

    raw = _require_mapping(raw, "root", "root")

    paths_raw = _require_mapping(_require(raw, "paths", "root"), "paths", "paths")
    paths = PathsConfig(
        input_dir=str(_require(paths_raw, "input_dir", "paths")),
        output_dir=str(_require(paths_raw, "output_dir", "paths")),
        prompts_dir=str(_require(paths_raw, "prompts_dir", "paths")),
        temp_dir=str(_require(paths_raw, "temp_dir", "paths")),
    )

    llm_raw = _require_mapping(_require(raw, "llm", "root"), "llm", "llm")
    llm = LLMConfig(
        provider=str(_require(llm_raw, "provider", "llm")),
        model=str(_require(llm_raw, "model", "llm")),
        base_url=str(_require(llm_raw, "base_url", "llm")),
        temperature=_as_float(_require(llm_raw, "temperature", "llm"), "llm.temperature"),
        max_tokens=_as_int(_require(llm_raw, "max_tokens", "llm"), "llm.max_tokens"),
        timeout_seconds=_as_int(_require(llm_raw, "timeout_seconds", "llm"), "llm.timeout_seconds"),
    )

    tts_raw = _require_mapping(_require(raw, "tts", "root"), "tts", "tts")
    tts = TTSConfig(
        provider=str(_require(tts_raw, "provider", "tts")),
        voice=str(_require(tts_raw, "voice", "tts")),
        rate=str(_require(tts_raw, "rate", "tts")),
        volume=str(_require(tts_raw, "volume", "tts")),
        pitch=str(_require(tts_raw, "pitch", "tts")),
        sample_rate=_as_int(_require(tts_raw, "sample_rate", "tts"), "tts.sample_rate"),
    )

    video_raw = _require_mapping(_require(raw, "video", "root"), "video", "video")
    video = VideoConfig(
        default_palette=str(_require(video_raw, "default_palette", "video")),
        resolution=_validate_resolution(
            str(_require(video_raw, "resolution", "video")), "video.resolution"
        ),
        fps=_as_int(_require(video_raw, "fps", "video"), "video.fps"),
        video_bitrate=str(_require(video_raw, "video_bitrate", "video")),
        audio_bitrate=str(_require(video_raw, "audio_bitrate", "video")),
        subtitle_font=str(_require(video_raw, "subtitle_font", "video")),
        subtitle_font_size=_as_int(
            _require(video_raw, "subtitle_font_size", "video"), "video.subtitle_font_size"
        ),
    )

    resolutions_raw = _require_mapping(_require(raw, "resolutions", "root"), "resolutions", "resolutions")
    resolutions: Dict[str, str] = {}
    for key, value in resolutions_raw.items():
        resolutions[key] = _validate_resolution(str(value), f"resolutions.{key}")

    palettes = _load_palettes(palettes_path)

    if video.default_palette not in palettes:
        raise ConfigError(
            f"[video.default_palette] '{video.default_palette}' não existe em palettes.json. "
            f"Disponíveis: {sorted(palettes)}"
        )

    return AppConfig(
        paths=paths,
        llm=llm,
        tts=tts,
        video=video,
        resolutions=resolutions,
        palettes=palettes,
    )


def get_palette(name: str, config: AppConfig | None = None) -> Palette:
    """Retorna a paleta por nome. Se config não for passada, carrega sob demanda."""
    cfg = config or load_config()
    if name not in cfg.palettes:
        raise ConfigError(f"Paleta '{name}' não encontrada. Disponíveis: {sorted(cfg.palettes)}")
    return cfg.palettes[name]


# ---------------------------------------------------------------------------
# CLI (inspeção rápida)
# ---------------------------------------------------------------------------

def _print_summary(cfg: AppConfig) -> None:
    print("=" * 55)
    print("CONFIGURAÇÃO CARREGADA")
    print("=" * 55)
    print(f"LLM        : {cfg.llm.provider}/{cfg.llm.model} @ {cfg.llm.base_url}")
    print(f"TTS        : {cfg.tts.provider} | voice={cfg.tts.voice} rate={cfg.tts.rate}")
    print(f"Vídeo      : {cfg.video.resolution} @ {cfg.video.fps}fps")
    print(f"Paleta padr: {cfg.video.default_palette}")
    print(f"Paletas    : {len(cfg.palettes)} -> {sorted(cfg.palettes)}")
    print(f"Resoluções : {sorted(cfg.resolutions)}")
    print(f"Input dir  : {cfg.paths.input_dir}")
    print(f"Output dir : {cfg.paths.output_dir}")
    print("=" * 55)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carrega e valida a configuração central.")
    parser.add_argument("--palette", help="Nome da paleta para imprimir detalhes")
    args = parser.parse_args(argv)

    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"❌ Configuração inválida: {exc}")
        return 1

    _print_summary(cfg)

    if args.palette:
        try:
            p = get_palette(args.palette, cfg)
        except ConfigError as exc:
            print(f"❌ {exc}")
            return 1
        print(f"\nPaleta '{p.name}':")
        print(f"  primary    = {p.primary}")
        print(f"  accent     = {p.accent}")
        print(f"  text       = {p.text}")
        print(f"  background = {p.background}")

    return 0


if __name__ == "__main__":
    sys.exit(main())