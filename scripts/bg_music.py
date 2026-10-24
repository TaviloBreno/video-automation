#!/usr/bin/env python3
"""
bg_music.py — Gerenciamento e mixagem de música de fundo sem direitos autorais com Audio Ducking.

O ducking diminui automaticamente o volume da música de fundo enquanto a voz da
narração está ativa, garantindo que o locutor seja sempre ouvido com clareza.
"""

from __future__ import annotations

import logging
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MUSIC_DIR = PROJECT_ROOT / "assets" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("bg_music")

# Lista de estilos de música livres de direitos autorais
MUSIC_TRACKS: Dict[str, Dict[str, Any]] = {
    "space_ambient": {
        "name": "Espacial & Cósmico (Sintetizador Profundo)",
        "mood": "space",
        "description": "Texturas etéreas e sintetizadores imersivos para astronomia e física.",
        "author": "Royalty-Free Public Domain",
        "freqs": [110, 164.8, 220, 329.6],  # Frequências A2/E3/A3/E4
    },
    "cinematic_epic": {
        "name": "Documentário Épico & Ciência",
        "mood": "epic",
        "description": "Clima grandioso e solene para explicar grandes descobertas.",
        "author": "Royalty-Free Public Domain",
        "freqs": [130.8, 196.0, 261.6, 392.0],  # C3/G3/C4/G4
    },
    "inspirational": {
        "name": "Inspirador & Descoberta",
        "mood": "inspiring",
        "description": "Leve, curioso e positivo, ótimo para fatos interessantes e estudos.",
        "author": "Royalty-Free Public Domain",
        "freqs": [146.8, 220.0, 293.7, 440.0],  # D3/A3/D4/A4
    },
    "lofi_chill": {
        "name": "Lo-Fi & Calmo",
        "mood": "chill",
        "description": "Ritmo sereno e focado para aprendizado contínuo.",
        "author": "Royalty-Free Public Domain",
        "freqs": [123.5, 185.0, 246.9, 370.0],  # B2/F#3/B3/F#4
    },
}


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg não encontrado no PATH.")
    return path


def generate_ambient_track(mood_id: str, duration_seconds: float, output_path: Path) -> Path:
    """Gera uma trilha sonora ambiente harmônica procedural com FFmpeg (100% royalty-free)."""
    track = MUSIC_TRACKS.get(mood_id, MUSIC_TRACKS["space_ambient"])
    f = track.get("freqs", [110, 165, 220, 330])

    # Gera acordes ambientes suaves com modulação de amplitude e reverb simulado
    filter_expr = (
        f"aevalsrc='0.15*sin(2*PI*{f[0]}*t)*sin(0.12*t)"
        f"+0.10*sin(2*PI*{f[1]}*t)*sin(0.18*t)"
        f"+0.08*sin(2*PI*{f[2]}*t)*cos(0.15*t)"
        f"+0.05*sin(2*PI*{f[3]}*t)*cos(0.22*t)':s=48000:d={duration_seconds:.2f},"
        "lowpass=f=800,volume=0.9,"
        f"afade=t=in:ss=0:d=2.5,afade=t=out:st={max(0, duration_seconds - 3):.2f}:d=3"
    )

    cmd = [
        _ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        filter_expr,
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)
    return output_path


def get_or_create_music(mood_id: str, duration_seconds: float, dest_dir: Path) -> Optional[Path]:
    """Obtém ou gera a trilha sonora sem direitos autorais para a duração requerida."""
    if mood_id == "none" or not mood_id:
        return None

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_music = dest_dir / f"bg_music_{mood_id}.m4a"

    # Se já existir arquivo de áudio local customizado em assets/music/<mood_id>.mp3, usa ele
    custom_track = MUSIC_DIR / f"{mood_id}.mp3"
    if custom_track.exists() and custom_track.stat().st_size > 10000:
        # Loop ou corte para a duração requerida
        loop_cmd = [
            _ffmpeg(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(custom_track),
            "-t",
            f"{duration_seconds:.2f}",
            "-af",
            f"afade=t=out:st={max(0, duration_seconds - 3):.2f}:d=3",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_music),
        ]
        subprocess.run(loop_cmd, check=True)
        return out_music

    # Gera a faixa procedural harmônica
    try:
        generate_ambient_track(mood_id, duration_seconds + 2.0, out_music)
        return out_music
    except Exception as exc:
        logger.warning("Falha ao gerar trilha de fundo: %s", exc)
        return None


def mix_voice_and_music(
    voice_path: Path,
    music_path: Optional[Path],
    output_path: Path,
    music_volume: float = 0.16,
) -> Path:
    """Mixagem profissional de narração + música com compressão sidechain (Audio Ducking)."""
    voice_p = Path(voice_path).resolve()
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if not music_path or not Path(music_path).exists():
        # Apenas copia o áudio da voz se não houver música
        shutil.copyfile(voice_p, out_p)
        return out_p

    music_p = Path(music_path).resolve()

    # Filtro FFmpeg Ducking:
    # A voz (input 0) aciona a compressão da música (input 1), reduzindo seu volume quando a voz fala
    filter_complex = (
        f"[1:a]volume={music_volume:.3f}[bg];"
        "[0:a][bg]sidechaincompress=threshold=0.08:ratio=4:attack=200:release=600[compressed_bg];"
        "[0:a][compressed_bg]amix=inputs=2:duration=first:dropout_transition=2[outa]"
    )

    cmd = [
        _ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(voice_p),
        "-i",
        str(music_p),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outa]",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        str(out_p),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0 or not out_p.exists():
        logger.warning("Filtro sidechain falhou, aplicando amix simples: %s", result.stderr[-400:])
        fallback_filter = f"[1:a]volume={music_volume*0.8:.3f}[bg];[0:a][bg]amix=inputs=2:duration=first[outa]"
        fallback_cmd = [
            _ffmpeg(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(voice_p),
            "-i",
            str(music_p),
            "-filter_complex",
            fallback_filter,
            "-map",
            "[outa]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_p),
        ]
        subprocess.run(fallback_cmd, check=True)

    logger.info("Mixagem de narração + música royalty-free concluída: %s", out_p.name)
    return out_p
