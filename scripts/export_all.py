#!/usr/bin/env python3
"""Run YouTube and vertical exports concurrently."""

from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_common import project_path

YOUTUBE_SCRIPT = PROJECT_ROOT / "scripts" / "export_youtube.py"
VERTICAL_SCRIPT = PROJECT_ROOT / "scripts" / "export_vertical.py"


def export_all(
    input_path: str = "output/final.mp4",
    audio_path: str = "output/voice.mp3",
    youtube_output: str = "output-youtube.mp4",
    vertical_output: str = "output-vertical.mp4",
) -> None:
    """Launch both format-specific exporters and report any failures."""
    if project_path(youtube_output) == project_path(vertical_output):
        raise ValueError("Os caminhos de saída horizontal e vertical devem ser diferentes.")

    commands = {
        "YouTube horizontal": [
            sys.executable, str(YOUTUBE_SCRIPT),
            "--input", input_path, "--audio", audio_path, "--out", youtube_output,
        ],
        "Shorts/Reels vertical": [
            sys.executable, str(VERTICAL_SCRIPT),
            "--input", input_path, "--audio", audio_path, "--out", vertical_output,
        ],
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            name: executor.submit(
                subprocess.run,
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            for name, command in commands.items()
        }
        failures = []
        for name, future in futures.items():
            result = future.result()
            if result.returncode != 0:
                failures.append(
                    f"{name} (código {result.returncode}):\n"
                    f"{(result.stderr or result.stdout or '')[-1200:]}"
                )
            else:
                print(f"{name}: concluído")

    if failures:
        raise RuntimeError("Falha(s) na exportação:\n" + "\n".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="output/final.mp4", help="Vídeo de entrada")
    parser.add_argument("--audio", default="output/voice.mp3", help="Narração de entrada")
    parser.add_argument(
        "--out-youtube", default="output-youtube.mp4", help="Saída horizontal"
    )
    parser.add_argument(
        "--out-vertical", default="output-vertical.mp4", help="Saída vertical"
    )
    args = parser.parse_args()
    export_all(args.input, args.audio, args.out_youtube, args.out_vertical)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
