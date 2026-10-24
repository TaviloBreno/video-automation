#!/usr/bin/env python3
"""
generate_voice.py — Gera MP3 + words.json a partir de texto via subreel tts.

Uso:
    from scripts.generate_voice import generate_voice
    mp3, words = generate_voice("texto...", "pt-BR-FranciscaNeural", "output")

CLI:
    python scripts/generate_voice.py --text "texto..." --voice pt-BR-FranciscaNeural
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config_loader import load_config, ConfigError

logger = logging.getLogger("generate_voice")


def generate_voice(
    text: str,
    voice: str,
    out_dir: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> Tuple[Path, Path]:
    """
    Gera voice.mp3 e voice.words.json usando `subreel tts`.

    Retorna (mp3_path, words_json_path).
    Lança RuntimeError se o subreel falhar ou não gerar os arquivos.
    """
    if not text or not text.strip():
        raise ValueError("'text' não pode ser vazio")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    mp3_path = out_path / "voice.mp3"
    words_path = out_path / "voice.words.json"

    cmd = [
        "subreel", "tts",
        "--text-inline", text.strip(),
        "--voice", voice,
        "--rate", rate,
        "--pitch", pitch,
        "--out", str(mp3_path),
        "--timings", str(words_path),
    ]

    logger.info("Executando subreel tts...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"subreel tts falhou (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        raise RuntimeError(f"MP3 não gerado ou vazio: {mp3_path}")

    if not words_path.exists() or words_path.stat().st_size == 0:
        raise RuntimeError(f"words.json não gerado ou vazio: {words_path}")

    logger.info("MP3 gerado: %s (%d bytes)", mp3_path, mp3_path.stat().st_size)
    logger.info("Words gerado: %s (%d bytes)", words_path, words_path.stat().st_size)

    return mp3_path, words_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera voice.mp3 + voice.words.json via subreel.")
    parser.add_argument("--text", "-t", default=None, help="Texto a narrar")
    parser.add_argument("--input", "-i", default=None, help="Arquivo de texto (utf-8-sig)")
    parser.add_argument("--voice", "-v", default=None, help="Voz (padrão: cfg.tts.voice)")
    parser.add_argument("--out-dir", "-o", default="output", help="Diretório de saída")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8-sig").strip()
    elif args.text:
        text = args.text
    else:
        logger.error("Forneça --text ou --input")
        return 1

    if args.voice:
        voice = args.voice
    else:
        try:
            cfg = load_config()
            voice = cfg.tts.voice
        except ConfigError as exc:
            logger.error("Config inválida: %s", exc)
            return 1

    try:
        mp3, words = generate_voice(text, voice, args.out_dir)
    except Exception as exc:
        logger.error("Falha: %s", exc)
        return 1

    print(f"✅ MP3: {mp3}")
    print(f"✅ Words: {words}")
    return 0


if __name__ == "__main__":
    sys.exit(main())