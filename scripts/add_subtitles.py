#!/usr/bin/env python3
"""
add_subtitles.py — Gera legendas em 3 formatos via subreel render.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def generate_subtitles(
    audio_path: str,
    words_path: str,
    out_dir: str = "output/subs",
    formats: str = "green,webm,mov",
) -> dict[str, Path]:
    """Gera legendas nos formatos green, webm e mov. Retorna dict formato→caminho."""
    out_path = PROJECT_ROOT / out_dir
    out_path.mkdir(parents=True, exist_ok=True)

    subreel = shutil.which("subreel")
    if not subreel:
        raise RuntimeError("subreel não encontrado no PATH.")

    cmd = [
        subreel, "render", str(PROJECT_ROOT / audio_path),
        "--timings", str(PROJECT_ROOT / words_path),
        "--formats", formats,
        "--out-dir", str(out_path),
    ]

    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)

    if result.returncode != 0:
        raise RuntimeError(f"subreel render falhou: {result.stderr}")

    # Mapeia os arquivos gerados
    generated = {}
    for fmt in formats.split(","):
        fmt = fmt.strip()
        if fmt == "green":
            generated["green"] = out_path / "subs-green.mp4"
        elif fmt == "webm":
            generated["webm"] = out_path / "subs-alpha.webm"
        elif fmt == "mov":
            generated["mov"] = out_path / "subs-alpha.mov"

    for fmt, path in generated.items():
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Arquivo {fmt} não gerado: {path}")
        print(f"✅ {fmt}: {path}")

    return generated


if __name__ == "__main__":
    generate_subtitles("output/voice.mp3", "output/voice.words.json")