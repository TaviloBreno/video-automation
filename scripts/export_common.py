"""Shared helpers for the delivery-format exports."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def prepare_export(
    input_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path,
) -> tuple[str, Path, Path]:
    video = project_path(input_path)
    audio = project_path(audio_path)
    output = project_path(output_path)

    if not video.is_file():
        raise FileNotFoundError(f"Vídeo de entrada não encontrado: {video}")
    if not audio.is_file():
        raise FileNotFoundError(f"Áudio de entrada não encontrado: {audio}")
    if output in (video, audio):
        raise ValueError(f"O arquivo de saída não pode sobrescrever uma entrada: {output}")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg não encontrado no PATH.")

    output.parent.mkdir(parents=True, exist_ok=True)
    return ffmpeg, video, audio


def encode(
    command: list[str],
    output_path: Path,
    format_name: str,
) -> Path:
    print(f"Exportando {format_name}: {output_path}")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg falhou ao exportar {format_name} "
            f"(código {result.returncode}):\n{(result.stderr or '')[-1200:]}"
        )
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg terminou sem gerar o arquivo esperado: {output_path}")

    print(f"Export concluído: {output_path}")
    return output_path


def video_filter(width: int, height: int) -> str:
    """Fit the full source frame over a blurred, cropped copy."""
    return (
        f"[0:v:0]split=2[background][foreground];"
        f"[background]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=20:10[blurred];"
        f"[foreground]scale={width}:{height}:force_original_aspect_ratio=decrease[fit];"
        "[blurred][fit]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]"
    )


def ffmpeg_encode_command(
    ffmpeg: str,
    video: Path,
    audio: Path,
    output: Path,
    filter_graph: str,
) -> list[str]:
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(video),
        "-i", str(audio),
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(output),
    ]
