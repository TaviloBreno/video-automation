#!/usr/bin/env python3
"""Load, save, and interactively edit user pipeline preferences."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.add_subtitles import SUBTITLE_STYLES
from scripts.config_loader import ConfigError, load_config

PREFERENCES_PATH = PROJECT_ROOT / "config" / "user_prefs.yaml"


def default_preferences() -> dict[str, str]:
    config = load_config()
    return {
        "palette": config.video.default_palette,
        "voice": config.tts.voice,
        "legend_style": "karaoke",
    }


def load_preferences(path: str | Path = PREFERENCES_PATH) -> dict[str, str]:
    preferences = default_preferences()
    prefs_path = Path(path)
    if not prefs_path.is_absolute():
        prefs_path = PROJECT_ROOT / prefs_path
    if not prefs_path.exists():
        return preferences

    raw: Any = yaml.safe_load(prefs_path.read_text(encoding="utf-8"))
    if raw is None:
        return preferences
    if not isinstance(raw, dict):
        raise ValueError(f"Preferências devem ser um mapeamento YAML: {prefs_path}")

    unknown = set(raw) - set(preferences)
    if unknown:
        raise ValueError(f"Preferências desconhecidas em {prefs_path}: {sorted(unknown)}")
    preferences.update({key: str(value) for key, value in raw.items()})
    validate_preferences(preferences)
    return preferences


def validate_preferences(preferences: dict[str, str]) -> dict[str, str]:
    config = load_config()
    if preferences["palette"] not in config.palettes:
        raise ConfigError(
            f"Paleta inválida: {preferences['palette']!r}. "
            f"Disponíveis: {', '.join(sorted(config.palettes))}"
        )
    if preferences["legend_style"] not in SUBTITLE_STYLES:
        raise ValueError(
            f"Estilo de legenda inválido: {preferences['legend_style']!r}. "
            f"Disponíveis: {', '.join(SUBTITLE_STYLES)}"
        )
    if not preferences["voice"].strip():
        raise ValueError("A voz não pode ser vazia.")
    return preferences


def save_preferences(
    updates: dict[str, str],
    path: str | Path = PREFERENCES_PATH,
) -> dict[str, str]:
    preferences = load_preferences(path)
    unknown = set(updates) - set(preferences)
    if unknown:
        raise ValueError(f"Campos de preferência desconhecidos: {sorted(unknown)}")
    preferences.update(updates)
    validate_preferences(preferences)

    prefs_path = Path(path)
    if not prefs_path.is_absolute():
        prefs_path = PROJECT_ROOT / prefs_path
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    prefs_path.write_text(
        yaml.safe_dump(preferences, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return preferences


def _interactive_preferences(current: dict[str, str]) -> dict[str, str]:
    config = load_config()
    palettes = sorted(config.palettes)
    styles = list(SUBTITLE_STYLES)

    print("Paletas disponíveis:")
    for index, name in enumerate(palettes, start=1):
        print(f"  {index}. {name}")
    choice = input(f"Paleta [{current['palette']}]: ").strip()
    if choice:
        if choice.isdigit():
            index = int(choice) - 1
            if index < 0 or index >= len(palettes):
                raise ValueError(f"Opção de paleta inválida: {choice}")
            current["palette"] = palettes[index]
        else:
            current["palette"] = choice

    choice = input(f"Voz TTS [{current['voice']}]: ").strip()
    if choice:
        current["voice"] = choice

    print("Estilos de legenda: " + ", ".join(styles))
    choice = input(f"Estilo [{current['legend_style']}]: ").strip()
    if choice:
        current["legend_style"] = choice
    return current


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--palette", help="Salvar paleta preferida")
    parser.add_argument("--voice", help="Salvar voz TTS preferida")
    parser.add_argument(
        "--legend-style",
        choices=sorted(SUBTITLE_STYLES),
        help="Salvar estilo de legenda preferido",
    )
    parser.add_argument("--interactive", action="store_true", help="Abrir menu interativo")
    parser.add_argument("--show", action="store_true", help="Exibir preferências atuais")
    args = parser.parse_args(argv)

    try:
        updates = {
            key: value
            for key, value in {
                "palette": args.palette,
                "voice": args.voice,
                "legend_style": args.legend_style,
            }.items()
            if value is not None
        }
        if args.interactive:
            preferences = _interactive_preferences(load_preferences())
            preferences = save_preferences(preferences)
        elif updates:
            preferences = save_preferences(updates)
        else:
            preferences = load_preferences()
        for key, value in preferences.items():
            print(f"{key}: {value}")
        return 0
    except (ConfigError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Erro ao carregar/salvar preferências: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
