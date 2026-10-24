#!/usr/bin/env python3
"""Run the complete video pipeline from a description to delivery exports."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Callable, Sequence, TypeVar

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.add_subtitles import add_subtitles
from scripts.build_composition import build_composition
from scripts.compute_duration import compute_scene_duration
from scripts.config_loader import get_palette, load_config
from scripts.export_all import export_all
from scripts.generate_voice import generate_voice
from scripts.llm_client import parse_scene
from scripts.render_scene import render_scene
from scripts.settings import load_preferences

logger = logging.getLogger("pipeline")
T = TypeVar("T")


def _resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _read_description(description: str | Path) -> str:
    candidate = Path(description)
    path = _resolve_path(candidate)
    if path.is_file():
        text = path.read_text(encoding="utf-8-sig").strip()
        if not text:
            raise ValueError(f"Arquivo de descrição vazio: {path}")
        return text
    looks_like_path = (
        isinstance(description, Path)
        or "\n" in str(description)
        or candidate.suffix != ""
        or "/" in str(description)
        or "\\" in str(description)
    )
    if looks_like_path:
        raise FileNotFoundError(f"Arquivo de descrição não encontrado: {path}")
    text = str(description).strip()
    if not text:
        raise ValueError("A descrição não pode ser vazia.")
    return text


def _normalize_formats(formats: str | Sequence[str]) -> tuple[str, ...]:
    if isinstance(formats, str):
        requested = formats.split(",")
    else:
        requested = formats
    selected = tuple(dict.fromkeys(item.strip().lower() for item in requested if item.strip()))
    invalid = set(selected) - {"youtube", "vertical"}
    if not selected or invalid:
        raise ValueError(
            "formats deve conter youtube e/ou vertical; "
            f"recebido: {', '.join(selected) or '(vazio)'}"
        )
    return selected


def _stage(name: str, action: Callable[[], T]) -> T:
    logger.info("Iniciando etapa: %s", name)
    try:
        result = action()
    except Exception:
        logger.exception("Etapa falhou: %s", name)
        raise
    logger.info("Etapa concluída: %s", name)
    return result


def run(
    description: str | Path,
    palette: str | None = None,
    voice: str | None = None,
    legend_style: str | None = None,
    formats: str | Sequence[str] = ("youtube", "vertical"),
) -> dict[str, Path]:
    """Run parse, voice, duration, composition, render, subtitles, and exports."""
    selected_formats = _normalize_formats(formats)
    preferences = load_preferences()
    config = load_config()
    selected_palette = palette or preferences["palette"]
    selected_voice = voice or preferences["voice"] or config.tts.voice
    selected_legend_style = legend_style or preferences["legend_style"]
    get_palette(selected_palette, config)
    if not selected_voice.strip():
        raise ValueError("A voz não pode ser vazia.")

    output_dir = _resolve_path(config.paths.output_dir)
    scene_path = output_dir / "scene.json"
    words_path = output_dir / "voice.words.json"
    audio_path = output_dir / "voice.mp3"
    composition_path = _resolve_path("render/index.html")
    template_path = _resolve_path("render/src/template.html")
    rendered_path = output_dir / "final.mp4"
    subtitled_path = output_dir / "final_legendas.mp4"

    description_text = _stage("T1.4 — descrição → cena", lambda: _read_description(description))

    def create_scene() -> dict:
        scene = parse_scene(description_text, cfg=config)
        scene["palette"] = selected_palette
        scene_path.parent.mkdir(parents=True, exist_ok=True)
        scene_path.write_text(
            json.dumps(scene, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return scene

    scene = _stage("T1.4 — gerar e salvar cena", create_scene)

    _stage(
        "T2.1 — gerar narração e timings",
        lambda: generate_voice(
            scene["narration_text"],
            selected_voice,
            str(output_dir),
            rate=config.tts.rate,
            pitch=config.tts.pitch,
        ),
    )
    duration = _stage(
        "T2.4 — calcular duração",
        lambda: compute_scene_duration(words_path),
    )
    logger.info("Duração da narração/cena: %.2f s", duration)

    _stage(
        "T3.4 — construir composição",
        lambda: build_composition(
            str(scene_path),
            str(words_path),
            str(template_path),
            str(composition_path),
        ),
    )
    _stage(
        "T3.5 — renderizar vídeo",
        lambda: render_scene(str(composition_path), str(rendered_path)),
    )
    _stage(
        "T4.3 — gerar e aplicar legendas",
        lambda: add_subtitles(
            str(words_path),
            str(rendered_path),
            str(output_dir / "subs" / "karaoke.ass"),
            str(subtitled_path),
            selected_legend_style,
            str(audio_path),
        ),
    )
    _stage(
        "T5.3 — exportar formatos",
        lambda: export_all(
            input_path=str(subtitled_path),
            audio_path=str(audio_path),
            formats=selected_formats,
        ),
    )
    outputs = {
        "youtube": _resolve_path("output-youtube.mp4"),
        "vertical": _resolve_path("output-vertical.mp4"),
    }
    result = {name: outputs[name] for name in selected_formats}
    for name, path in result.items():
        logger.info("Arquivo final (%s): %s", name, path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="input/descricao.txt", help="Arquivo ou texto de descrição")
    parser.add_argument("--palette", help="Paleta (sobrescreve a preferência salva)")
    parser.add_argument("--voice", help="Voz TTS (sobrescreve a preferência salva)")
    parser.add_argument(
        "--legend-style",
        choices=("karaoke", "clean", "bold"),
        help="Estilo de legenda",
    )
    parser.add_argument(
        "--formats",
        default="youtube,vertical",
        help="Formatos separados por vírgula: youtube,vertical",
    )
    parser.add_argument("--verbose", action="store_true", help="Ativar logs detalhados")
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        run(args.input, args.palette, args.voice, args.legend_style, args.formats)
        return 0
    except Exception as exc:
        logger.error("Pipeline interrompido: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
