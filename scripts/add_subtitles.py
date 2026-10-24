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

SUBTITLE_STYLES = {
    "karaoke": {"font_size": 64, "primary_color": "&H00FFFFFF", "highlight_color": "&H0000FFFF"},
    "clean": {"font_size": 56, "primary_color": "&H00FFFFFF", "highlight_color": "&H00FFFF00"},
    "bold": {"font_size": 72, "primary_color": "&H00FFFFFF", "highlight_color": "&H00FF00FF"},
}


def add_subtitles(
    words_path: str = "output/voice.words.json",
    video_path: str = "output/final.mp4",
    ass_path: str = "output/subs/karaoke.ass",
    out_video: str = "output/final_legendas.mp4",
    legend_style: str = "karaoke",
    audio_path: str | None = None,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    margin_v: int = 150,
) -> Path:
    """Gera ASS karaokê e queima no vídeo. Retorna caminho do vídeo final."""
    if legend_style not in SUBTITLE_STYLES:
        raise ValueError(
            f"Estilo de legenda inválido: {legend_style!r}. "
            f"Disponíveis: {', '.join(SUBTITLE_STYLES)}"
        )
    generate_karaoke_ass(
        words_path,
        ass_path,
        **SUBTITLE_STYLES[legend_style],
        play_res_x=play_res_x,
        play_res_y=play_res_y,
        margin_v=margin_v,
    )
    result = burn_ass(video_path, ass_path, out_video, audio_path=audio_path)
    print(f"Legendas aplicadas: {result}")
    return result


if __name__ == "__main__":
    add_subtitles()