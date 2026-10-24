#!/usr/bin/env python3
"""
server.py — Servidor Web local com Flask para automação de vídeos do YouTube e Shorts virais.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, Response, jsonify, render_template, request, send_file, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.add_subtitles import SUBTITLE_STYLES
from scripts.config_loader import load_config
from scripts.long_video import JobCancelled, run_long_video
from scripts.viral_clips import detect_viral_candidates, render_viral_clip

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "web" / "templates"),
    static_folder=str(PROJECT_ROOT / "web" / "static"),
)

JOBS_DIR = PROJECT_ROOT / "output" / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

# Armazenamento em memória do estado dos jobs ativos
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
CANCEL_FLAGS: Dict[str, threading.Event] = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("web_server")


def _get_job_path(job_id: str) -> Path:
    safe_id = re.sub(r"[^\w\-]", "", job_id)
    return JOBS_DIR / safe_id


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config_info():
    """Retorna opções disponíveis de paletas, vozes e estilos."""
    cfg = load_config()
    voices = [
        {"id": "pt-BR-FranciscaNeural", "name": "Francisca (Feminina, Natural) - Padrão", "gender": "Feminina"},
        {"id": "pt-BR-AntonioNeural", "name": "Antônio (Masculino, Firme)", "gender": "Masculina"},
        {"id": "pt-BR-ThalitaNeural", "name": "Thalita (Feminina, Jovem)", "gender": "Feminina"},
        {"id": "pt-BR-NicolauNeural", "name": "Nicolau (Masculino, Calmo)", "gender": "Masculina"},
        {"id": "pt-BR-FabioNeural", "name": "Fábio (Masculino, Dinâmico)", "gender": "Masculina"},
    ]
    palettes = []
    for name, p in cfg.palettes.items():
        palettes.append({
            "id": name,
            "primary": p.primary,
            "accent": p.accent,
            "text": p.text,
            "background": p.background,
        })

    return jsonify({
        "palettes": palettes,
        "default_palette": cfg.video.default_palette,
        "voices": voices,
        "default_voice": cfg.tts.voice,
        "legend_styles": list(SUBTITLE_STYLES.keys()),
        "default_legend_style": "karaoke",
    })


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """Lista todos os jobs existentes no disco e em memória."""
    jobs = []
    if JOBS_DIR.exists():
        for job_path in sorted(JOBS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if job_path.is_dir():
                job_id = job_path.name
                manifest_path = job_path / "manifest.json"
                script_path = job_path / "script.json"
                info = ACTIVE_JOBS.get(job_id, {})
                status = info.get("status", "completed" if manifest_path.exists() else "unknown")
                topic = info.get("topic")
                title = info.get("title")
                target_min = info.get("minutes")

                if not topic and manifest_path.exists():
                    try:
                        m = json.loads(manifest_path.read_text(encoding="utf-8"))
                        topic = m.get("topic")
                        title = m.get("title")
                        target_min = round(m.get("target_seconds", 0) / 60, 1)
                    except Exception:
                        pass
                elif not topic and script_path.exists():
                    try:
                        s = json.loads(script_path.read_text(encoding="utf-8"))
                        topic = s.get("topic")
                        title = s.get("title")
                        target_min = round(s.get("target_seconds", 0) / 60, 1)
                    except Exception:
                        pass

                jobs.append({
                    "id": job_id,
                    "topic": topic or job_id,
                    "title": title or topic or "Vídeo",
                    "status": status,
                    "minutes": target_min or 0,
                    "has_video": (job_path / "video.mp4").exists(),
                    "created_at": job_path.stat().st_mtime,
                })
    return jsonify({"jobs": jobs})


@app.route("/api/generate", methods=["POST"])
def generate_video():
    """Cria e inicia o processo assíncrono de geração de vídeo longo."""
    data = request.json or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "O tema do vídeo é obrigatório."}), 400

    try:
        minutes = float(data.get("minutes", 2.0))
    except (ValueError, TypeError):
        return jsonify({"error": "A duração em minutos deve ser um número válido."}), 400

    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    job_dir = _get_job_path(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    cancel_event = threading.Event()
    CANCEL_FLAGS[job_id] = cancel_event

    job_state: Dict[str, Any] = {
        "id": job_id,
        "topic": topic,
        "title": "Gerando roteiro...",
        "minutes": minutes,
        "status": "running",
        "progress": 0.0,
        "stage": "Inicializando pipeline...",
        "logs": ["Iniciando projeto..."],
        "error": None,
        "manifest": None,
        "started_at": time.time(),
    }
    ACTIVE_JOBS[job_id] = job_state

    params = {
        "topic": topic,
        "minutes": minutes,
        "palette": data.get("palette"),
        "voice": data.get("voice"),
        "legend_style": data.get("legend_style", "karaoke"),
        "research": bool(data.get("research", True)),
    }

    def _worker():
        def _prog(pct: float, msg: str):
            job_state["progress"] = round(pct * 100, 1)
            job_state["stage"] = msg
            job_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(job_state["logs"]) > 100:
                job_state["logs"].pop(0)

        def _cancelled() -> bool:
            return cancel_event.is_set()

        try:
            logger.info("Job %s iniciado: %s (%.1f min)", job_id, topic, minutes)
            manifest = run_long_video(job_dir, params, progress=_prog, cancelled=_cancelled)
            job_state["status"] = "completed"
            job_state["progress"] = 100.0
            job_state["stage"] = "Vídeo finalizado com sucesso!"
            job_state["title"] = manifest.get("title", topic)
            job_state["manifest"] = manifest
            job_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] Concluído com sucesso!")
        except JobCancelled:
            job_state["status"] = "cancelled"
            job_state["stage"] = "Cancelado pelo usuário."
            job_state["logs"].append("Job cancelado.")
        except Exception as exc:
            logger.exception("Job %s falhou", job_id)
            job_state["status"] = "failed"
            job_state["error"] = str(exc)
            job_state["stage"] = f"Erro: {exc}"
            job_state["logs"].append(f"ERRO: {exc}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    return jsonify({"job_id": job_id, "status": "running"})


@app.route("/api/status/<job_id>", methods=["GET"])
def job_status(job_id: str):
    """Consulta o progresso e o estado em tempo real do job."""
    info = ACTIVE_JOBS.get(job_id)
    job_dir = _get_job_path(job_id)

    if not info:
        # Tenta carregar do disco se for um job anterior
        manifest_path = job_dir / "manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return jsonify({
                    "id": job_id,
                    "status": "completed",
                    "progress": 100.0,
                    "stage": "Vídeo pronto.",
                    "topic": manifest.get("topic"),
                    "title": manifest.get("title"),
                    "minutes": round(manifest.get("actual_seconds", 0) / 60, 1),
                    "manifest": manifest,
                    "logs": ["Carregado do histórico."],
                })
            except Exception:
                pass
        return jsonify({"error": "Job não encontrado"}), 404

    return jsonify(info)


@app.route("/api/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    """Sinaliza cancelamento para um job em execução."""
    if job_id in CANCEL_FLAGS:
        CANCEL_FLAGS[job_id].set()
        if job_id in ACTIVE_JOBS:
            ACTIVE_JOBS[job_id]["status"] = "cancelling"
            ACTIVE_JOBS[job_id]["stage"] = "Interrompendo..."
        return jsonify({"success": True})
    return jsonify({"error": "Job não está em execução"}), 400


@app.route("/api/jobs/<job_id>/manifest", methods=["GET"])
def get_job_manifest(job_id: str):
    """Retorna o manifesto detalhado com roteiro, capítulos e fontes."""
    job_dir = _get_job_path(job_id)
    manifest_path = job_dir / "manifest.json"
    if not manifest_path.exists():
        return jsonify({"error": "Manifesto ainda não disponível"}), 404
    return jsonify(json.loads(manifest_path.read_text(encoding="utf-8")))


@app.route("/api/jobs/<job_id>/detect_shorts", methods=["POST"])
def detect_shorts(job_id: str):
    """Usa a IA para encontrar os trechos virais com maior retenção."""
    job_dir = _get_job_path(job_id)
    manifest_path = job_dir / "manifest.json"
    words_path = job_dir / "long_words.json"

    if not manifest_path.exists() or not words_path.exists():
        return jsonify({"error": "O vídeo longo precisa estar concluído primeiro."}), 400

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    words_data = json.loads(words_path.read_text(encoding="utf-8")).get("words", [])

    candidates = detect_viral_candidates(manifest, words_data)

    # Salva lista de candidatos
    shorts_meta_path = job_dir / "viral_candidates.json"
    shorts_meta_path.write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")

    return jsonify({"candidates": candidates})


@app.route("/api/jobs/<job_id>/render_short", methods=["POST"])
def render_short(job_id: str):
    """Renderiza um corte vertical 9:16 selecionado com legendas dinâmicas."""
    job_dir = _get_job_path(job_id)
    video_source = job_dir / "video.mp4"
    words_path = job_dir / "long_words.json"

    if not video_source.exists() or not words_path.exists():
        return jsonify({"error": "Vídeo base não encontrado."}), 400

    data = request.json or {}
    start_time = float(data.get("start_time", 0.0))
    end_time = float(data.get("end_time", 30.0))
    title = data.get("title", "Corte Viral")
    legend_style = data.get("legend_style", "karaoke")

    shorts_dir = job_dir / "shorts"
    shorts_dir.mkdir(parents=True, exist_ok=True)

    clip_id = f"short_{int(start_time)}_{int(end_time)}_{uuid.uuid4().hex[:4]}"
    out_file = shorts_dir / f"{clip_id}.mp4"

    words_data = json.loads(words_path.read_text(encoding="utf-8")).get("words", [])

    try:
        result = render_viral_clip(
            video_source_path=video_source,
            words_data=words_data,
            start_time=start_time,
            end_time=end_time,
            output_path=out_file,
            legend_style=legend_style,
            clip_title=title,
        )
        return jsonify({"success": True, "clip": result})
    except Exception as exc:
        logger.exception("Falha ao renderizar corte viral")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/jobs/<job_id>/shorts", methods=["GET"])
def list_shorts(job_id: str):
    """Lista todos os Shorts já gerados para este job."""
    job_dir = _get_job_path(job_id)
    shorts_dir = job_dir / "shorts"
    clips = []
    if shorts_dir.exists():
        for f in sorted(shorts_dir.glob("*.mp4")):
            clips.append({
                "file": f.name,
                "url": f"/media/{job_id}/shorts/{f.name}",
                "size_bytes": f.stat().st_size,
            })
    return jsonify({"shorts": clips})


@app.route("/media/<job_id>/<path:filename>")
def serve_media(job_id: str, filename: str):
    """Serve arquivos de vídeo e mídia com suporte a range requests para o player HTML5."""
    job_dir = _get_job_path(job_id)
    file_path = (job_dir / filename).resolve()
    if not file_path.exists() or not str(file_path).startswith(str(job_dir.resolve())):
        return "Arquivo não encontrado", 404
    return send_file(file_path, conditional=True)


def start_server(host="127.0.0.1", port=5000, debug=False):
    print("=======================================================")
    print("Video Automation Web UI rodando em:")
    print(f"http://localhost:{port}")
    print("=======================================================")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    start_server()
