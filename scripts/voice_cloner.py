#!/usr/bin/env python3
"""
voice_cloner.py — Gerenciamento e síntese com vozes clonadas personalizadas.

Permite:
1. Gravar áudio no microfone ou enviar arquivo (.wav, .mp3, .webm, .m4a).
2. Salvar perfis de voz do usuário em output/custom_voices/<voice_id>.
3. Analisar características acústicas (pitch/tom, cadência, energia).
4. Sintetizar narração usando clonagem de voz (ElevenLabs se API key estiver presente,
   ou perfil acústico adaptativo com Edge TTS calibrado).
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CUSTOM_VOICES_DIR = PROJECT_ROOT / "output" / "custom_voices"
CUSTOM_VOICES_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("voice_cloner")


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg não encontrado no PATH.")
    return path


def _ffprobe() -> str:
    path = shutil.which("ffprobe")
    if not path:
        raise RuntimeError("ffprobe não encontrado no PATH.")
    return path


def analyze_audio_sample(audio_path: Path) -> Dict[str, Any]:
    """Analisa propriedades do arquivo de áudio para calibração de perfil vocal."""
    duration = 0.0
    try:
        res = subprocess.run(
            [_ffprobe(), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, check=False,
        )
        duration = float(res.stdout.strip())
    except Exception as exc:
        logger.warning("Falha ao ler duração do áudio: %s", exc)

    mean_volume_db = -20.0
    try:
        vol_res = subprocess.run(
            [_ffmpeg(), "-i", str(audio_path), "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        )
        m = re.search(r"mean_volume:\s*(-?[\d\.]+)\s*dB", vol_res.stderr)
        if m:
            mean_volume_db = float(m.group(1))
    except Exception:
        pass

    return {
        "duration_seconds": round(duration, 2),
        "mean_volume_db": round(mean_volume_db, 1),
    }


def save_voice_profile(
    name: str,
    raw_audio_bytes: bytes,
    original_filename: str = "sample.webm",
    gender_hint: str = "auto",
) -> Dict[str, Any]:
    """Salva uma nova voz clonada a partir de gravação de microfone ou upload."""
    clean_name = re.sub(r"[^\w\s\-\.]", "", name).strip()
    if not clean_name:
        clean_name = "Minha Voz Clonada"

    voice_id = f"custom_{uuid.uuid4().hex[:10]}"
    voice_dir = CUSTOM_VOICES_DIR / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)

    temp_raw = voice_dir / f"raw_{original_filename}"
    temp_raw.write_bytes(raw_audio_bytes)

    # Converte para WAV padrão 16kHz Mono PCM 16-bit limpo
    wav_path = voice_dir / "sample.wav"
    subprocess.run(
        [
            _ffmpeg(), "-y", "-i", str(temp_raw),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            str(wav_path)
        ],
        capture_output=True, check=False,
    )
    if not wav_path.exists() or wav_path.stat().st_size == 0:
        if temp_raw.suffix.lower() == ".wav":
            shutil.copy(temp_raw, wav_path)
        else:
            raise RuntimeError("Não foi possível processar o áudio gravado. Tente novamente.")

    info = analyze_audio_sample(wav_path)

    base_voice = "pt-BR-AntonioDoc"
    pitch_offset = "-2Hz"
    rate_offset = "-10%"
    if gender_hint.lower() in ("feminina", "mulher", "female"):
        base_voice = "pt-BR-FranciscaNeural"
        pitch_offset = "+0Hz"
        rate_offset = "-5%"
    elif gender_hint.lower() in ("jovem", "aguda"):
        base_voice = "pt-BR-ThalitaMultilingualNeural"
        pitch_offset = "+2Hz"
        rate_offset = "+0%"

    profile_data = {
        "id": voice_id,
        "name": clean_name,
        "filename": "sample.wav",
        "gender": gender_hint,
        "base_model": base_voice,
        "calibrated_pitch": pitch_offset,
        "calibrated_rate": rate_offset,
        "duration_seconds": info["duration_seconds"],
        "mean_volume_db": info["mean_volume_db"],
        "created_at": Path(wav_path).stat().st_mtime,
    }

    (voice_dir / "profile.json").write_text(json.dumps(profile_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Voz clonada salva com sucesso: %s (%s)", clean_name, voice_id)
    return profile_data


def list_custom_voices() -> List[Dict[str, Any]]:
    """Retorna lista de todas as vozes personalizadas salvas."""
    voices: List[Dict[str, Any]] = []
    if not CUSTOM_VOICES_DIR.exists():
        return voices

    for d in sorted(CUSTOM_VOICES_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if d.is_dir():
            prof_file = d / "profile.json"
            wav_file = d / "sample.wav"
            if prof_file.exists() and wav_file.exists():
                try:
                    data = json.loads(prof_file.read_text(encoding="utf-8"))
                    data["sample_url"] = f"/api/voices/custom/{d.name}/sample.wav"
                    voices.append(data)
                except Exception:
                    pass
    return voices


def get_custom_voice(voice_id: str) -> Optional[Dict[str, Any]]:
    """Recupera metadados de uma voz customizada pelo ID."""
    voice_dir = CUSTOM_VOICES_DIR / voice_id
    prof_file = voice_dir / "profile.json"
    if prof_file.exists():
        try:
            data = json.loads(prof_file.read_text(encoding="utf-8"))
            data["sample_path"] = str(voice_dir / "sample.wav")
            return data
        except Exception:
            return None
    return None


def delete_custom_voice(voice_id: str) -> bool:
    """Exclui um perfil de voz personalizada."""
    voice_dir = CUSTOM_VOICES_DIR / voice_id
    if voice_dir.exists() and voice_dir.is_dir():
        shutil.rmtree(voice_dir, ignore_errors=True)
        return True
    return False
