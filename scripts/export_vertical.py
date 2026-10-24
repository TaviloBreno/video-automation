#!/usr/bin/env python3
"""Export a 9:16 Shorts/Reels MP4 with H.264 video and AAC narration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_common import encode, ffmpeg_encode_command, prepare_export, video_filter


def export_vertical(
    input_path: str | Path = "output/final.mp4",
    audio_path: str | Path = "output/voice.mp3",
    output_path: str | Path = "output-vertical.mp4",
) -> Path:
    """Create a 1080x1920 vertical export, returning its absolute path."""
    ffmpeg, video, audio = prepare_export(input_path, audio_path, output_path)
    output = Path(output_path)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output = output.resolve()

    command = ffmpeg_encode_command(
        ffmpeg,
        video,
        audio,
        output,
        video_filter(1080, 1920),
    )
    return encode(command, output, "Shorts/Reels vertical")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="output/final.mp4", help="Vídeo de entrada")
    parser.add_argument("--audio", default="output/voice.mp3", help="Narração de entrada")
    parser.add_argument("--out", default="output-vertical.mp4", help="Arquivo MP4 de saída")
    args = parser.parse_args()
    export_vertical(args.input, args.audio, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
