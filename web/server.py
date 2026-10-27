#!/usr/bin/env python3
"""
server.py — Servidor Web local com Flask para automação de vídeos do YouTube e Shorts virais.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
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
from scripts.bg_music import MUSIC_TRACKS
from scripts.config_loader import load_config
from scripts.image_provider import search_multiple_gifs
from scripts.long_video import JobCancelled, run_long_video, _clean_text
from scripts.viral_clips import detect_viral_candidates, render_viral_clip
from scripts.voice_cloner import (
    CUSTOM_VOICES_DIR,
    delete_custom_voice,
    get_custom_voice,
    list_custom_voices,
    save_voice_profile,
)

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "web" / "templates"),
    static_folder=str(PROJECT_ROOT / "web" / "static"),
)
app.json.ensure_ascii = False

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
    base_voices = [
        {"id": "pt-BR-AntonioSenior", "name": "👴 Antônio Sênior (Homem Mais Velho & Maduro — Tom Grave Solene)", "gender": "Masculina"},
        {"id": "pt-BR-AntonioDoc", "name": "🇧🇷 Antônio (Documentarista Brasileiro, Barítono com Pausas) - Padrão", "gender": "Masculina"},
        {"id": "pt-BR-AntonioNeural", "name": "🇧🇷 Antônio (Brasileiro, Tom Firme e Natural)", "gender": "Masculina"},
        {"id": "pt-BR-FranciscaNeural", "name": "🇧🇷 Francisca (Brasileira, Feminina Natural)", "gender": "Feminina"},
        {"id": "pt-BR-ThalitaMultilingualNeural", "name": "🇧🇷 Thalita (Brasileira, Feminina Jovem)", "gender": "Feminina"},
    ]

    # Carrega vozes personalizadas gravadas ou clonadas pelo usuário
    custom_voices_list = list_custom_voices()
    formatted_custom = [
        {
            "id": cv["id"],
            "name": f"🎙️ {cv['name']} (Sua Voz Clonada)",
            "gender": cv.get("gender", "Personalizada"),
            "is_custom": True,
            "sample_url": cv.get("sample_url"),
        }
        for cv in custom_voices_list
    ]

    voices = formatted_custom + base_voices

    palettes = []
    for name, p in cfg.palettes.items():
        palettes.append({
            "id": name,
            "primary": p.primary,
            "accent": p.accent,
            "text": p.text,
            "background": p.background,
        })

    bg_music_list = [
        {"id": "space_ambient", "name": "🌌 Espacial & Cósmico (Misterioso)"},
        {"id": "cinematic_epic", "name": "🎬 Documentário Épico & Ciência"},
        {"id": "inspirational", "name": "💡 Inspirador & Descobertas"},
        {"id": "lofi_chill", "name": "☕ Lo-Fi & Foco Relaxante"},
        {"id": "none", "name": "🔇 Nenhuma Música (Apenas Narração)"},
    ]

    visual_modes = [
        {
            "id": "motion_design",
            "name": "🎨 Motion Design (Gráficos Animados & Neon)",
            "description": "Tipografia cinética, efeitos visuais vetoriais, gradientes e formas neon.",
        },
        {
            "id": "images",
            "name": "📷 Imagens Científicas Reais",
            "description": "Fotografias e ilustrações científicas de alta qualidade com referências e licenças livres CC.",
        },
        {
            "id": "hybrid",
            "name": "⚡ Híbrido Inteligente",
            "description": "Motion Design impactante na introdução/conclusão e Imagens Reais nos capítulos centrais.",
        },
    ]

    voice_rates = [
        {"id": "-20%", "name": "🐢 Bem Lenta & Imersiva (-20%) — Estilo Documentário BBC / Carl Sagan"},
        {"id": "-15%", "name": "🎙️ Lenta & Reflexiva (-15%) — Pausada e Solene"},
        {"id": "-8%", "name": "📖 Moderada (-8%) — Narração Equilibrada"},
        {"id": "+0%", "name": "⚡ Padrão (+0%) — Mais Rápida"},
    ]

    aspect_ratios = [
        {
            "id": "16:9",
            "name": "16:9 Horizontal (YouTube padrão)",
            "description": "Formato widescreen (1920x1080) com layout lateral e palco científico expandido.",
            "icon": "desktop",
            "badge": "YouTube",
        },
        {
            "id": "9:16",
            "name": "9:16 Vertical (Reels, TikTok, Shorts)",
            "description": "Formato vertical (1080x1920) com visual no topo, texto centralizado e margem segura.",
            "icon": "smartphone",
            "badge": "Reels / TikTok / Shorts",
        },
    ]

    return jsonify({
        "palettes": palettes,
        "default_palette": cfg.video.default_palette,
        "voices": voices,
        "custom_voices": custom_voices_list,
        "default_voice": formatted_custom[0]["id"] if formatted_custom else cfg.tts.voice,
        "voice_rates": voice_rates,
        "default_voice_rate": cfg.tts.rate or "-20%",
        "legend_styles": list(SUBTITLE_STYLES.keys()),
        "default_legend_style": "karaoke",
        "bg_music_options": bg_music_list,
        "default_bg_music": "space_ambient",
        "visual_modes": visual_modes,
        "default_visual_mode": "motion_design",
        "aspect_ratios": aspect_ratios,
        "default_aspect_ratio": "16:9",
    })


@app.route("/api/voices/custom", methods=["GET"])
def api_list_custom_voices():
    """Retorna lista de vozes clonadas cadastradas."""
    return jsonify({"voices": list_custom_voices()})


@app.route("/api/voices/clone", methods=["POST"])
def api_clone_voice():
    """Recebe áudio gravado no microfone ou upload de arquivo para criar perfil de voz clonada."""
    name = request.form.get("name", "Minha Voz").strip()
    gender = request.form.get("gender", "auto").strip()

    file = request.files.get("audio")
    if not file or not file.filename:
        return jsonify({"error": "Nenhum arquivo de áudio foi enviado."}), 400

    raw_bytes = file.read()
    if len(raw_bytes) < 1000:
        return jsonify({"error": "Arquivo de áudio muito curto ou vazio."}), 400

    try:
        profile = save_voice_profile(
            name=name,
            raw_audio_bytes=raw_bytes,
            original_filename=file.filename,
            gender_hint=gender,
        )
        return jsonify({
            "success": True,
            "message": f"Voz '{profile['name']}' clonada e configurada com sucesso!",
            "profile": profile,
        })
    except Exception as exc:
        logger.exception("Erro ao processar clonagem de voz")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/voices/custom/<voice_id>", methods=["DELETE"])
def api_delete_custom_voice(voice_id: str):
    """Exclui um perfil de voz personalizada."""
    success = delete_custom_voice(voice_id)
    if success:
        return jsonify({"success": True, "message": "Voz removida com sucesso."})
    return jsonify({"error": "Voz não encontrada."}), 404


@app.route("/api/voices/custom/<voice_id>/sample.wav", methods=["GET"])
def api_get_custom_voice_sample(voice_id: str):
    """Retorna o áudio de amostra gravado para pré-escuta."""
    voice_dir = CUSTOM_VOICES_DIR / voice_id
    sample_path = voice_dir / "sample.wav"
    if sample_path.exists():
        return send_file(sample_path, mimetype="audio/wav")
    return jsonify({"error": "Amostra não encontrada."}), 404


@app.route("/api/media/search_gifs", methods=["GET"])
def api_search_gifs():
    """Busca animações e GIFs científicos para visualização ou inclusão no vídeo."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"gifs": []})
    try:
        limit = min(20, max(1, int(request.args.get("limit", 8))))
    except ValueError:
        limit = 8
    gifs = search_multiple_gifs(query, limit=limit)
    return jsonify({"query": query, "count": len(gifs), "gifs": gifs})


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    """Lista todos os jobs existentes no disco e em memória com metadados completos."""
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
                visual_mode = "motion_design"
                bg_music = "space_ambient"

                if not topic and manifest_path.exists():
                    try:
                        m = json.loads(manifest_path.read_text(encoding="utf-8"))
                        topic = m.get("topic")
                        title = m.get("title")
                        target_min = round(m.get("actual_seconds", m.get("target_seconds", 0)) / 60, 1)
                        visual_mode = m.get("visual_mode", "motion_design")
                        bg_music = m.get("bg_music", "space_ambient")
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

                shorts_dir = job_path / "shorts"
                shorts_count = len(list(shorts_dir.glob("*.mp4"))) if shorts_dir.exists() else 0

                has_video = (job_path / "video.mp4").exists()
                aspect_ratio = "16:9"
                if manifest_path.exists():
                    try:
                        m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                        aspect_ratio = m_data.get("aspect_ratio", "16:9")
                    except Exception:
                        pass

                jobs.append({
                    "id": job_id,
                    "topic": _clean_text(topic) or job_id,
                    "title": _clean_text(title) or _clean_text(topic) or "Vídeo",
                    "status": status,
                    "minutes": target_min or 0,
                    "has_video": has_video,
                    "video_url": f"/media/{job_id}/video.mp4" if has_video else None,
                    "shorts_count": shorts_count,
                    "visual_mode": visual_mode,
                    "aspect_ratio": aspect_ratio,
                    "bg_music": bg_music,
                    "created_at": job_path.stat().st_mtime,
                })
    return jsonify({"jobs": jobs})


@app.route("/api/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """Exclui completamente o vídeo e todos os arquivos do projeto."""
    if job_id in CANCEL_FLAGS:
        CANCEL_FLAGS[job_id].set()
    ACTIVE_JOBS.pop(job_id, None)

    job_dir = _get_job_path(job_id)
    if job_dir.exists():
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.info("Job %s excluído com sucesso do disco", job_id)
            return jsonify({"success": True, "message": "Vídeo e projeto excluídos com sucesso."})
        except Exception as exc:
            logger.error("Erro ao excluir job %s: %s", job_id, exc)
            return jsonify({"error": f"Erro ao apagar arquivos: {exc}"}), 500

    return jsonify({"error": "Projeto não encontrado"}), 404


@app.route("/api/jobs/<job_id>", methods=["PUT"])
def update_job(job_id: str):
    """Atualiza título, tema e capítulos do roteiro de um projeto existente."""
    job_dir = _get_job_path(job_id)
    manifest_path = job_dir / "manifest.json"
    script_path = job_dir / "script.json"

    if not job_dir.exists():
        return jsonify({"error": "Projeto não encontrado"}), 404

    data = request.json or {}
    new_title = data.get("title")
    new_topic = data.get("topic")
    new_chapters = data.get("chapters")

    if manifest_path.exists():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            if new_title:
                m["title"] = new_title
            if new_topic:
                m["topic"] = new_topic
            if new_chapters and isinstance(new_chapters, list):
                for i, ch_data in enumerate(new_chapters):
                    if i < len(m.get("chapters", [])):
                        if "title" in ch_data:
                            m["chapters"][i]["title"] = ch_data["title"]
                        if "narration" in ch_data:
                            m["chapters"][i]["narration"] = ch_data["narration"]
            manifest_path.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            return jsonify({"error": f"Erro ao atualizar manifest: {exc}"}), 500

    if script_path.exists():
        try:
            s = json.loads(script_path.read_text(encoding="utf-8"))
            if new_title:
                s["title"] = new_title
            if new_topic:
                s["topic"] = new_topic
            if new_chapters and isinstance(new_chapters, list):
                for i, ch_data in enumerate(new_chapters):
                    if i < len(s.get("chapters", [])):
                        if "title" in ch_data:
                            s["chapters"][i]["title"] = ch_data["title"]
                        if "narration" in ch_data:
                            s["chapters"][i]["narration"] = ch_data["narration"]
            script_path.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return jsonify({"success": True, "message": "Projeto atualizado com sucesso."})


@app.route("/api/jobs/<job_id>/rebuild", methods=["POST"])
def rebuild_job(job_id: str):
    """Re-renderiza o vídeo a partir do roteiro salvo ou com novas opções visuais."""
    job_dir = _get_job_path(job_id)
    if not job_dir.exists():
        return jsonify({"error": "Projeto não encontrado"}), 404

    data = request.json or {}
    manifest_path = job_dir / "manifest.json"
    script_path = job_dir / "script.json"
    base_data = {}
    if manifest_path.exists():
        try:
            base_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    elif script_path.exists():
        try:
            base_data = json.loads(script_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    topic = data.get("topic") or base_data.get("topic", "Vídeo")
    minutes = float(data.get("minutes") or (base_data.get("actual_seconds", base_data.get("target_seconds", 120)) / 60))
    visual_mode = data.get("visual_mode") or base_data.get("visual_mode", "motion_design")

    params = {
        "topic": topic,
        "minutes": minutes,
        "palette": data.get("palette") or base_data.get("palette"),
        "voice": data.get("voice") or base_data.get("voice"),
        "voice_rate": data.get("voice_rate") or base_data.get("voice_rate") or cfg.tts.rate or "-20%",
        "legend_style": data.get("legend_style") or base_data.get("legend_style", "karaoke"),
        "research": False,
        "bg_music": data.get("bg_music") or base_data.get("bg_music", "space_ambient"),
        "visual_mode": visual_mode,
        "enable_images": (visual_mode != "motion_design"),
    }

    cancel_event = threading.Event()
    CANCEL_FLAGS[job_id] = cancel_event

    job_state = {
        "id": job_id,
        "topic": topic,
        "title": "Reconstruindo vídeo...",
        "minutes": minutes,
        "status": "running",
        "progress": 0.0,
        "stage": "Re-renderizando capítulos...",
        "logs": ["Iniciando re-renderização..."],
        "error": None,
        "manifest": None,
        "started_at": time.time(),
    }
    ACTIVE_JOBS[job_id] = job_state

    def _worker():
        def _prog(pct: float, msg: str):
            job_state["progress"] = round(pct * 100, 1)
            job_state["stage"] = msg
            job_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(job_state["logs"]) > 100:
                job_state["logs"].pop(0)

        try:
            manifest = run_long_video(job_dir, params, progress=_prog, cancelled=lambda: cancel_event.is_set())
            job_state["status"] = "completed"
            job_state["progress"] = 100.0
            job_state["stage"] = "Vídeo atualizado com sucesso!"
            job_state["title"] = manifest.get("title", topic)
            job_state["manifest"] = manifest
        except JobCancelled:
            job_state["status"] = "cancelled"
            job_state["stage"] = "Cancelado."
        except Exception as exc:
            logger.exception("Rebuild falhou: %s", exc)
            job_state["status"] = "failed"
            job_state["error"] = str(exc)

    threading.Thread(target=_worker, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "running"})


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

    visual_mode = data.get("visual_mode", "motion_design")
    aspect_ratio = str(data.get("aspect_ratio") or "16:9").strip()
    if aspect_ratio not in ("16:9", "9:16"):
        aspect_ratio = "16:9"

    params = {
        "topic": topic,
        "minutes": minutes,
        "aspect_ratio": aspect_ratio,
        "palette": data.get("palette"),
        "voice": data.get("voice"),
        "voice_rate": data.get("voice_rate") or cfg.tts.rate or "-20%",
        "legend_style": data.get("legend_style", "karaoke"),
        "research": bool(data.get("research", True)),
        "bg_music": data.get("bg_music", "space_ambient"),
        "visual_mode": visual_mode,
        "enable_images": (visual_mode != "motion_design") and bool(data.get("enable_images", True)),
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
    hook = data.get("hook", "")
    legend_style = data.get("legend_style", "karaoke")

    manifest = {}
    manifest_path = job_dir / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            pass

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
            clip_hook=hook,
            topic=manifest.get("topic", title),
        )
        return jsonify({"success": True, "clip": result})
    except Exception as exc:
        logger.exception("Falha ao renderizar corte viral")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/jobs/<job_id>/shorts", methods=["GET"])
def list_shorts(job_id: str):
    """Lista todos os Shorts já gerados para este job, com metadados para redes sociais."""
    job_dir = _get_job_path(job_id)
    shorts_dir = job_dir / "shorts"
    clips = []
    if shorts_dir.exists():
        for f in sorted(shorts_dir.glob("*.mp4")):
            meta_file = f.with_suffix(".json")
            social_meta = None
            if meta_file.exists():
                try:
                    social_meta = json.loads(meta_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            clips.append({
                "file": f.name,
                "url": f"/media/{job_id}/shorts/{f.name}",
                "size_bytes": f.stat().st_size,
                "social_metadata": social_meta,
            })
    return jsonify({"shorts": clips})


@app.route("/api/jobs/<job_id>/shorts/<filename>", methods=["DELETE"])
def delete_short(job_id: str, filename: str):
    """Exclui um vídeo vertical Short e seus metadados de redes sociais associados."""
    safe_filename = Path(filename).name
    if not safe_filename.endswith(".mp4"):
        return jsonify({"error": "Arquivo inválido"}), 400

    job_dir = _get_job_path(job_id)
    shorts_dir = job_dir / "shorts"
    video_file = shorts_dir / safe_filename
    meta_file = video_file.with_suffix(".json")

    deleted = False
    if video_file.exists():
        try:
            video_file.unlink()
            deleted = True
        except Exception as exc:
            logger.error("Erro ao apagar arquivo de short %s: %s", video_file, exc)
            return jsonify({"error": f"Erro ao apagar vídeo: {exc}"}), 500

    if meta_file.exists():
        try:
            meta_file.unlink()
        except Exception:
            pass

    if deleted:
        logger.info("Short %s do job %s excluído com sucesso", safe_filename, job_id)
        return jsonify({"success": True, "message": "Short excluído com sucesso."})

    return jsonify({"error": "Short não encontrado"}), 404



@app.route("/api/music/<path:filename>")
def serve_music_sample(filename: str):
    """Serve amostras de trilhas sonoras royalty-free."""
    music_dir = (PROJECT_ROOT / "assets" / "music").resolve()
    file_path = (music_dir / filename).resolve()
    if not file_path.name.endswith(".mp3"):
        file_path = file_path.with_suffix(".mp3")
    if not file_path.exists() or not str(file_path).startswith(str(music_dir)):
        return "Música não encontrada", 404
    return send_file(file_path, conditional=True)


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
