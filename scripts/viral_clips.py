#!/usr/bin/env python3
"""
viral_clips.py — Identifica trechos virais em vídeos longos e gera cortes verticais (Shorts/Reels/TikTok).

Fluxo:
1. Detecta momentos com ganchos fortes e alta retenção (15 a 60 segundos).
2. Recorta o vídeo original e áudio sincronizado.
3. Transforma em formato vertical 9:16 (1080x1920) com background blur dinâmico.
4. Gera e queima legendas verticais karaokê ajustadas ao corte.
"""

from __future__ import annotations

import json
import logging
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.add_subtitles import SUBTITLE_STYLES
from scripts.burn_subtitles import burn_ass
from scripts.config_loader import AppConfig, load_config
from scripts.gen_karaoke_ass import generate_karaoke_ass
from scripts.llm_client import (
    OLLAMA_ENABLED,
    _call_groq,
    _call_ollama,
    _parse_json_response,
)

logger = logging.getLogger("viral_clips")


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


def _get_media_duration(path: Path) -> float:
    result = subprocess.run(
        [
            _ffprobe(),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _snap_to_words(
    words: List[Dict[str, Any]], target_start: float, target_end: float
) -> tuple[float, float, List[Dict[str, Any]]]:
    """Ajusta o início e fim para as fronteiras exatas de palavras mais próximas."""
    if not words:
        return target_start, target_end, []

    # Encontra a primeira palavra que começa próxima de target_start
    best_start_idx = 0
    min_start_diff = float("inf")
    for i, w in enumerate(words):
        diff = abs(w["start"] - target_start)
        if diff < min_start_diff:
            min_start_diff = diff
            best_start_idx = i

    # Encontra a última palavra que termina próxima de target_end
    best_end_idx = len(words) - 1
    min_end_diff = float("inf")
    for i in range(best_start_idx, len(words)):
        diff = abs(w["end"] - target_end)
        if diff < min_end_diff:
            min_end_diff = diff
            best_end_idx = i

    if best_end_idx <= best_start_idx:
        best_end_idx = min(len(words) - 1, best_start_idx + 1)

    actual_start = max(0.0, float(words[best_start_idx]["start"]))
    actual_end = float(words[best_end_idx]["end"])

    selected_words = []
    for w in words[best_start_idx : best_end_idx + 1]:
        selected_words.append(
            {
                "text": w["text"],
                "start": max(0.0, round(float(w["start"]) - actual_start, 3)),
                "end": max(0.0, round(float(w["end"]) - actual_start, 3)),
            }
        )

    return actual_start, actual_end, selected_words


def detect_viral_candidates(
    manifest_data: Dict[str, Any],
    words_data: List[Dict[str, Any]],
    cfg: Optional[AppConfig] = None,
    min_sec: float = 15.0,
    max_sec: float = 60.0,
) -> List[Dict[str, Any]]:
    """Usa IA (com fallback heurístico) para detectar os momentos mais virais do vídeo."""
    cfg = cfg or load_config()
    chapters = manifest_data.get("chapters", [])
    total_sec = manifest_data.get("actual_seconds") or manifest_data.get("target_seconds", 60.0)

    # Prepara resumo dos capítulos com tempos
    chapters_summary = []
    for c in chapters:
        start = c.get("start", 0.0)
        dur = c.get("duration", 0.0)
        chapters_summary.append(
            {
                "index": c.get("index", 0) + 1,
                "title": c.get("title", ""),
                "summary": c.get("summary", ""),
                "start": start,
                "end": round(start + dur, 2),
                "duration": dur,
                "narration_sample": c.get("narration", "")[:180] + "...",
            }
        )

    prompt = (
        "Você é um especialista em crescimento de canais virais no YouTube Shorts, TikTok e Instagram Reels.\n"
        f"Analise o roteiro e os capítulos do vídeo abaixo (duração total: {total_sec:.1f} segundos):\n\n"
        + json.dumps(chapters_summary, ensure_ascii=False, indent=2)
        + "\n\nIdentifique os 3 a 5 MELHORES trechos virais para transformar em vídeos verticais (Shorts).\n"
        "Critérios de seleção para viralizar:\n"
        "- Começar com um gancho ('hook') irresistível nos primeiros 3 segundos.\n"
        "- Conteúdo com curiosidade extrema, fato chocante ou explicação clara de mistério.\n"
        f"- Cada corte deve ter duração entre {int(min_sec)} e {int(max_sec)} segundos.\n"
        "- O corte deve ter começo, meio e fim compreensíveis.\n\n"
        "Responda SOMENTE em formato JSON com o seguinte formato exato:\n"
        '{"clips": [\n'
        '  {\n'
        '    "title": "Título chamativo com emoji (ex: O Buraco Negro Devorador! 🌌)",\n'
        '    "hook": "Frase de abertura forte que prende a atenção",\n'
        '    "start_time": 0.0,\n'
        '    "end_time": 45.0,\n'
        '    "viral_score": 95,\n'
        '    "reason": "Por que este trecho tem alto potencial de viralização"\n'
        "  }\n"
        "]}"
    )

    clips: List[Dict[str, Any]] = []

    try:
        messages = [{"role": "user", "content": prompt}]
        raw = _call_ollama(messages, cfg) if OLLAMA_ENABLED else _call_groq(messages, cfg)
        parsed = _parse_json_response(raw)
        raw_clips = parsed.get("clips", [])
        for c in raw_clips:
            s = float(c.get("start_time", 0.0))
            e = float(c.get("end_time", 0.0))
            if e > s and (e - s) >= min_sec:
                if (e - s) > max_sec:
                    e = s + max_sec
                e = min(e, total_sec)
                clips.append(
                    {
                        "title": _clean_text(str(c.get("title", "Corte Viral"))),
                        "hook": _clean_text(str(c.get("hook", ""))),
                        "start_time": round(s, 2),
                        "end_time": round(e, 2),
                        "duration": round(e - s, 2),
                        "viral_score": int(c.get("viral_score", 90)),
                        "reason": _clean_text(str(c.get("reason", "Gancho forte e ritmo acelerado"))),
                    }
                )
    except Exception as exc:
        logger.warning("Detecção por IA falhou (%s), aplicando detecção heurística baseada nos capítulos.", exc)

    # Se a IA não retornou clipes suficientes, gera automaticamente a partir dos capítulos
    if not clips and chapters:
        for idx, ch in enumerate(chapters):
            ch_start = float(ch.get("start", 0.0))
            ch_dur = float(ch.get("duration", 30.0))
            dur = min(max_sec, max(min_sec, ch_dur))
            ch_end = min(total_sec, ch_start + dur)
            score = 95 if idx == 0 else (90 if idx == len(chapters) - 1 else 85)
            clips.append(
                {
                    "title": f"🔥 {ch.get('title', f'Destaque {idx + 1}')}",
                    "hook": ch.get("summary", "Descubra o segredo neste corte rápido!"),
                    "start_time": round(ch_start, 2),
                    "end_time": round(ch_end, 2),
                    "duration": round(ch_end - ch_start, 2),
                    "viral_score": score,
                    "reason": "Capítulo estruturado com gancho e conclusão dinâmica.",
                }
            )

    return sorted(clips, key=lambda x: x["viral_score"], reverse=True)


def render_viral_clip(
    video_source_path: Path,
    words_data: List[Dict[str, Any]],
    start_time: float,
    end_time: float,
    output_path: Path,
    legend_style: str = "karaoke",
    clip_title: str = "",
) -> Dict[str, Any]:
    """Corta o vídeo original, converte para 1080x1920 (Shorts) com fundo blur e queima legenda."""
    video_source = Path(video_source_path).resolve()
    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not video_source.exists():
        raise FileNotFoundError(f"Vídeo de origem não encontrado: {video_source}")

    # Alinha os tempos com as palavras faladas
    actual_start, actual_end, clip_words = _snap_to_words(words_data, start_time, end_time)
    duration = actual_end - actual_start

    tmp_dir = output_file.parent / f"tmp_{output_file.stem}"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cut_raw = tmp_dir / "cut_raw.mp4"
    ass_path = tmp_dir / "subs_vertical.ass"
    words_sub_path = tmp_dir / "words_cut.json"

    # Salva palavras ajustadas para o trecho
    words_sub_path.write_text(
        json.dumps({"language": "pt", "source": "cut", "words": clip_words}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Gera legenda ASS vertical 1080x1920
    # Margem vertical calculada para não tampar botões de Shorts/TikTok (centro-inferior)
    style_params = SUBTITLE_STYLES.get(legend_style, SUBTITLE_STYLES["karaoke"])
    generate_karaoke_ass(
        str(words_sub_path),
        str(ass_path),
        font_size=style_params.get("font_size", 68),
        primary_color=style_params.get("primary_color", "&H00FFFFFF"),
        highlight_color=style_params.get("highlight_color", "&H0000FFFF"),
        play_res_x=1080,
        play_res_y=1920,
        margin_v=420,  # Posiciona a legenda no meio inferior seguro de redes sociais
    )

    # 1. Filtro FFmpeg para criar 1080x1920 vertical dinâmico:
    # - Fundo: scale para cobrir 1080x1920 + crop + blur forte
    # - Vídeo principal: scale para caber em 1080 de largura mantendo proporção (16:9 -> 1080x608)
    # - Overlay centralizado verticalmente
    filter_complex = (
        "[0:v]split=2[bg_in][fg_in];"
        "[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:12[bg];"
        "[fg_in]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
        f"[base]ass='{str(ass_path).replace('\\', '/').replace(':', r'\:')}'[outv]"
    )

    cmd = [
        _ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{actual_start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(video_source),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_file),
    ]

    logger.info("Renderizando corte vertical: %s (%0.2fs -> %0.2fs)", output_file.name, actual_start, actual_end)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0 or not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError(f"FFmpeg falhou ao gerar corte vertical ({output_file.name}): {result.stderr[-800:]}")

    # Limpeza de temporários
    shutil.rmtree(tmp_dir, ignore_errors=True)

    actual_duration = _get_media_duration(output_file)

    return {
        "file": output_file.name,
        "path": str(output_file),
        "title": clip_title or f"Short {actual_start:.0f}s-{actual_end:.0f}s",
        "start": actual_start,
        "end": actual_end,
        "duration": round(actual_duration, 2),
        "size_bytes": output_file.stat().st_size,
    }
