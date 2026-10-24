#!/usr/bin/env python3
"""Friendly command-line interface for the video automation pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.add_subtitles import SUBTITLE_STYLES, add_subtitles
from scripts.build_composition import build_composition
from scripts.config_loader import load_config
from scripts.export_all import export_all
from scripts.generate_voice import generate_voice
from scripts.pipeline import run as run_pipeline
from scripts.render_scene import render_scene
from scripts.settings import load_preferences


def _path(value: str) -> Path:
    candidate = Path(value)
    return candidate.resolve() if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()


def _run_script(script_name: str, arguments: list[str]) -> int:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script_name), *arguments],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result.returncode


def _add_style_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--legend-style",
        choices=sorted(SUBTITLE_STYLES),
        help="Estilo de legenda (padrão: preferência salva)",
    )


def _add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--formats",
        default="youtube,vertical",
        help="Formatos separados por vírgula: youtube,vertical",
    )


def _format_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _render_existing() -> None:
    scene = _path("output/scene.json")
    words = _path("output/voice.words.json")
    composition = _path("render/index.html")
    build_composition(
        str(scene),
        str(words),
        str(_path("render/src/template.html")),
        str(composition),
    )
    render_scene(str(composition), str(_path("output/final.mp4")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gere vídeos narrados, legendados e exportados para redes sociais."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="Verificar dependências do ambiente")

    parse_parser = subparsers.add_parser("parse", help="Gerar a cena a partir de uma descrição")
    parse_parser.add_argument("--input", default="input/descricao.txt")
    parse_parser.add_argument("--palette")
    parse_parser.add_argument("--no-research", action="store_true")

    voice_parser = subparsers.add_parser("voice", help="Gerar a narração e timings")
    voice_parser.add_argument("--input", default="output/scene.json", help="Cena JSON ou texto")
    voice_parser.add_argument("--voice")

    subparsers.add_parser("render", help="Renderizar a cena e a narração atuais")

    subs_parser = subparsers.add_parser("subs", help="Aplicar legendas ao vídeo renderizado")
    _add_style_argument(subs_parser)

    export_parser = subparsers.add_parser("export", help="Exportar formatos de publicação")
    _add_format_argument(export_parser)

    all_parser = subparsers.add_parser("all", help="Executar o pipeline completo")
    all_parser.add_argument("--input", default="input/descricao.txt")
    all_parser.add_argument("--palette")
    all_parser.add_argument("--voice")
    _add_style_argument(all_parser)
    _add_format_argument(all_parser)
    all_parser.add_argument("--verbose", action="store_true")
    all_parser.add_argument(
        "--no-research",
        action="store_false",
        dest="research",
        help="Desativar a busca na web para usar somente a descrição",
    )
    all_parser.set_defaults(research=True)

    args = parser.parse_args(argv)

    if args.command == "check":
        return _run_script("check_env.py", [])
    if args.command == "parse":
        command = ["--input", args.input]
        if args.palette:
            command.extend(["--palette", args.palette])
        if args.no_research:
            command.append("--no-research")
        return _run_script("parse_scene.py", command)
    if args.command == "voice":
        preferences = load_preferences()
        source = _path(args.input)
        if source.is_file() and source.suffix.lower() == ".json":
            narration = json.loads(source.read_text(encoding="utf-8"))["narration_text"]
        elif source.is_file():
            narration = source.read_text(encoding="utf-8-sig")
        elif Path(args.input).suffix:
            raise FileNotFoundError(f"Arquivo de entrada não encontrado: {source}")
        else:
            narration = args.input
        config = load_config()
        generate_voice(
            narration,
            args.voice or preferences["voice"] or config.tts.voice,
            str(_path(config.paths.output_dir)),
            rate=config.tts.rate,
            pitch=config.tts.pitch,
        )
        return 0
    if args.command == "render":
        _render_existing()
        return 0
    preferences = load_preferences()
    if args.command == "subs":
        add_subtitles(
            legend_style=args.legend_style or preferences["legend_style"],
            audio_path="output/voice.mp3",
        )
        return 0
    if args.command == "export":
        formats = _format_list(args.formats)
        export_all(
            input_path="output/final_legendas.mp4",
            audio_path="output/voice.mp3",
            formats=formats,
        )
        return 0
    if args.command == "all":
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        try:
            run_pipeline(
                args.input,
                args.palette,
                args.voice,
                args.legend_style,
                _format_list(args.formats),
                args.research,
            )
            return 0
        except Exception as exc:
            logging.getLogger("cli").error("Pipeline interrompido: %s", exc)
            return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
