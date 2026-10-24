#!/usr/bin/env python3
"""
add_subtitles.py — Gera ASS karaokê e queima no vídeo via FFmpeg.

Substitui o `subreel render` (quebrado no Windows por bug de escape de
caminho no filtro ass). Em vez de gerar 3 formatos alpha, gera o ASS
karaokê a partir de voice.words.json e queima no vídeo final.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gen_karaoke_ass import generate_karaoke_ass
from scripts.burn_subtitles import burn_ass


def add_subtitles(
    words_path: str = "output/voice.words.json",
    video_path: str = "output/final.mp4",
    ass_path: str = "output/subs/karaoke.ass",
    out_video: str = "output/final_legendas.mp4",
) -> Path:
    """Gera ASS karaokê e queima no vídeo. Retorna caminho do vídeo final."""
    generate_karaoke_ass(words_path, ass_path)
    result = burn_ass(video_path, ass_path, out_video)
    print(f"✅ Legendas aplicadas: {result}")
    return result


if __name__ == "__main__":
    add_subtitles()