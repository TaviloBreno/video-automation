#!/usr/bin/env python3
"""
parse_scene.py — CLI que lê input/descricao.txt e escreve output/scene.json.

Uso:
    python scripts/parse_scene.py --input input/descricao.txt --output output/scene.json
    python scripts/parse_scene.py --input input/descricao.txt --palette tiktok-bold
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Garante raiz no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config_loader import load_config, ConfigError, get_palette
from scripts.llm_client import parse_scene
from scripts.scene_validator import validate_scene, SceneValidationError

logger = logging.getLogger("parse_scene")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera output/scene.json a partir de uma descrição em linguagem natural."
    )
    parser.add_argument(
        "--input", "-i",
        default="input/descricao.txt",
        help="Arquivo de descrição (padrão: input/descricao.txt)",
    )
    parser.add_argument(
        "--output", "-o",
        default="output/scene.json",
        help="Arquivo JSON de saída (padrão: output/scene.json)",
    )
    parser.add_argument(
        "--palette", "-p",
        default=None,
        help="Força uma paleta (sobrescreve a escolhida pelo LLM)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Log detalhado",
    )
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    # 1. Lê descrição
    input_path = PROJECT_ROOT / args.input
    if not input_path.exists():
        logger.error("Arquivo de entrada não encontrado: %s", input_path)
        return 1

    description = input_path.read_text(encoding="utf-8").strip()
    if not description:
        logger.error("Arquivo de entrada vazio: %s", input_path)
        return 1

    logger.info("Descrição lida (%d caracteres)", len(description))

    # 2. Carrega config e valida palette forçada (se houver)
    try:
        cfg = load_config()
    except ConfigError as exc:
        logger.error("Configuração inválida: %s", exc)
        return 1

    if args.palette:
        try:
            get_palette(args.palette, cfg)  # valida que existe
        except ConfigError as exc:
            logger.error("Paleta inválida: %s", exc)
            return 1
        logger.info("Paleta forçada via CLI: %s", args.palette)

    # 3. Chama o pipeline (parse_scene já faz retry/fallback)
    try:
        scene = parse_scene(description, cfg=cfg)
    except Exception as exc:
        logger.error("Falha ao gerar cena: %s", exc)
        return 1

    # 4. Sobrescreve palette se --palette foi passado
    if args.palette:
        scene["palette"] = args.palette

    # 5. Revalida o schema final (garantia extra)
    try:
        validate_scene(scene)
    except SceneValidationError as exc:
        logger.error("Cena gerada não passou na validação final:")
        for msg in exc.errors:
            logger.error("  - %s", msg)
        return 1

    # 6. Escreve saída
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(scene, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Cena escrita em: %s", output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())