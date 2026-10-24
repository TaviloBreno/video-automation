#!/usr/bin/env python3
"""
burn_subtitles.py — Queima legendas ASS no vídeo via FFmpeg (libass).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ffmpeg_path() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado no PATH.")
    return ffmpeg


def burn_ass(
    video_path: str,
    ass_path: str,
    out_path: str,
    audio_path: str | None = None,
) -> Path:
    """Queima ASS via filtro subtitles (libass). Usa caminhos relativos para evitar
    o problema de escape de ':' do Windows no filtro."""
    video_abs = (PROJECT_ROOT / video_path).resolve()
    ass_abs = (PROJECT_ROOT / ass_path).resolve()
    out_abs = (PROJECT_ROOT / out_path).resolve()
    audio_abs = (PROJECT_ROOT / audio_path).resolve() if audio_path else None
    out_abs.parent.mkdir(parents=True, exist_ok=True)

    if not video_abs.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_abs}")
    if not ass_abs.exists():
        raise FileNotFoundError(f"ASS não encontrado: {ass_abs}")
    if audio_abs is not None and not audio_abs.is_file():
        raise FileNotFoundError(f"Áudio não encontrado: {audio_abs}")

    # Escapa ':' do Windows no caminho do ASS para o filtro
    ass_filter = str(ass_abs).replace("\\", "/").replace(":", "\\:")

    cmd = [
        _ffmpeg_path(), "-y",
        "-i", str(video_abs),
    ]
    if audio_abs is not None:
        cmd.extend(["-i", str(audio_abs)])
    cmd.extend([
        "-vf", f"ass='{ass_filter}'",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
    ])
    if audio_abs is not None:
        cmd.extend(["-map", "0:v:0", "-map", "1:a:0", "-c:a", "copy", "-shortest"])
    else:
        cmd.extend(["-c:a", "copy"])
    cmd.append(str(out_abs))
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg falhou: {result.stderr[-800:]}")
    print(f"ASS queimado: {out_abs}")
    return out_abs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="output/final.mp4")
    parser.add_argument("--ass", default="output/subs/karaoke.ass")
    parser.add_argument("--out", default="output/final_karaoke.mp4")
    args = parser.parse_args()

    burn_ass(args.video, args.ass, args.out)