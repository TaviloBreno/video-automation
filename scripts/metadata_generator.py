#!/usr/bin/env python3
"""
metadata_generator.py — Geração de metadados de SEO profissionais para YouTube e redes sociais.

Produz:
- YouTube Longo: Títulos de alto CTR, descrição com timestamps e referências, tags, conceito de capa.
- Shorts / Reels / TikTok: Descrições adaptadas ao formato e algoritmo de cada plataforma.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config_loader import AppConfig, load_config
from scripts.llm_client import (
    OLLAMA_ENABLED,
    _call_groq,
    _call_ollama,
    _parse_json_response,
)

logger = logging.getLogger("metadata_generator")


def _format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def generate_youtube_metadata(
    topic: str,
    manifest: Dict[str, Any],
    images_info: Optional[List[Dict[str, Any]]] = None,
    cfg: Optional[AppConfig] = None,
) -> Dict[str, Any]:
    """Gera pacote completo de SEO e metadados para publicação no YouTube."""
    cfg = cfg or load_config()
    chapters = manifest.get("chapters", [])
    sources = manifest.get("sources", [])
    title_base = manifest.get("title", topic)

    # Monta lista de timestamps dos capítulos
    timestamps_text = []
    for c in chapters:
        start_t = _format_time(c.get("start", 0.0))
        timestamps_text.append(f"{start_t} - {c.get('title', 'Capítulo')}")
    chapters_str = "\n".join(timestamps_text)

    # Monta referências de imagens
    images_credits = []
    if images_info:
        for img in images_info:
            if img:
                images_credits.append(
                    f"• {img.get('title', 'Imagem')} — Autor: {img.get('author', 'Desconhecido')} ({img.get('license', 'CC')})"
                )
    images_str = "\n".join(images_credits) if images_credits else "Imagens de domínio público e Wikimedia Commons."

    prompt = (
        "Você é um estrategista sênior de canais de sucesso do YouTube Brasil especializado em ciência e documentários.\n"
        f"Gere o pacote completo de SEO para o vídeo sobre: '{topic}' (Título provisório: '{title_base}').\n\n"
        f"Capítulos do vídeo:\n{chapters_str}\n\n"
        "Crie:\n"
        "1. 3 variações de Títulos altamente atraentes (alto CTR, sem clickbait falso, envolventes).\n"
        "2. Resumo instigante em 2 parágrafos para a introdução da descrição.\n"
        "3. Lista de 15 a 25 Tags/palavras-chave em português separadas por vírgula para a aba de tags do YouTube Studio.\n"
        "4. 8 a 12 Hashtags relevantes (#).\n"
        "5. Ideia visual para a Thumbnail (capa do vídeo) com elementos visuais e texto curto de impacto.\n\n"
        "Responda SOMENTE em JSON com este formato exato:\n"
        '{\n'
        '  "title_options": ["Opção 1", "Opção 2", "Opção 3"],\n'
        '  "best_title": "O melhor título selecionado",\n'
        '  "summary": "Dois parágrafos cativantes explicando o mistério abordado no vídeo.",\n'
        '  "tags": "palavra1, palavra2, palavra3, ...",\n'
        '  "hashtags": ["#Astronomia", "#Quasars", "#Ciência", ...],\n'
        '  "thumbnail_concept": {\n'
        '    "visual": "Descrição da imagem que deve estar na capa",\n'
        '    "text_overlay": "Texto curto de 2 a 4 palavras na capa"\n'
        '  }\n'
        '}'
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        raw = _call_ollama(messages, cfg) if OLLAMA_ENABLED else _call_groq(messages, cfg)
        data = _parse_json_response(raw)
    except Exception as exc:
        logger.warning("Falha ao gerar SEO via IA: %s, aplicando gerador padrão.", exc)
        data = {
            "title_options": [
                f"{topic}: Os Maiores Mistérios Revelados",
                f"O Que Ninguém Te Contou Sobre {topic}",
                f"{topic}: Como Realmente Funciona?",
            ],
            "best_title": f"{topic}: Tudo o Que a Ciência Sabe",
            "summary": f"Descubra todos os detalhes sobre {topic} nesta explicação aprofundada.",
            "tags": f"{topic}, ciência, astronomia, documentário, física, universo",
            "hashtags": ["#Ciência", "#Universo", "#Astronomia", "#Documentário"],
            "thumbnail_concept": {
                "visual": f"Imagem dramática em alta resolução representando {topic}",
                "text_overlay": "O SEGREDO!",
            },
        }

    # Monta a descrição final completa formatada pronta para o YouTube
    sources_text = []
    if sources:
        for s in sources:
            sources_text.append(f"• [{s.get('id')}] {s.get('title')} ({s.get('publisher', '')}) - {s.get('url', '')}")
    sources_str = "\n".join(sources_text) if sources_text else "Pesquisa acadêmica e artigos científicos públicos."

    full_description = (
        f"{data.get('summary', '')}\n\n"
        f"🔔 Inscreva-se no canal e ative o sino para não perder nenhuma explicação científica semanal!\n\n"
        f"⏱️ CAPÍTULOS:\n{chapters_str}\n\n"
        f"📚 FONTES E REFERÊNCIAS:\n{sources_str}\n\n"
        f"🖼️ CRÉDITOS VISUAIS:\n{images_str}\n\n"
        f"{' '.join(data.get('hashtags', []))}"
    )

    return {
        "title_options": data.get("title_options", []),
        "best_title": data.get("best_title", title_base),
        "full_description": full_description,
        "summary": data.get("summary", ""),
        "tags": data.get("tags", ""),
        "hashtags": data.get("hashtags", []),
        "thumbnail_concept": data.get("thumbnail_concept", {}),
        "timestamps": chapters_str,
    }


def generate_social_clip_metadata(
    clip_title: str,
    clip_hook: str,
    topic: str,
    cfg: Optional[AppConfig] = None,
) -> Dict[str, Any]:
    """Gera textos e hashtags adaptadas especificamente para TikTok, Instagram Reels e YouTube Shorts."""
    cfg = cfg or load_config()

    prompt = (
        "Você é um especialista em redes sociais de vídeos curtos verticais (TikTok, Instagram Reels e Shorts).\n"
        f"Gere legendas e hashtags personalizadas para o seguinte corte viral:\n"
        f"Tema: {topic}\n"
        f"Título do trecho: {clip_title}\n"
        f"Gancho: {clip_hook}\n\n"
        "Crie para cada rede:\n"
        "- tiktok: Título magnético com emoji, legenda curta de 2 linhas, chamada para seguir/comentar, e 6 hashtags em alta (#fy, etc).\n"
        "- instagram_reels: Legenda envolvente, pergunta instigante para gerar debates nos comentários, e hashtags de alcance.\n"
        "- youtube_shorts: Título com gancho chamativo, descrição convidando a ver o vídeo completo no canal, e hashtags (#Shorts).\n\n"
        "Responda SOMENTE em formato JSON:\n"
        '{\n'
        '  "tiktok": {\n'
        '    "title": "...",\n'
        '    "caption": "...",\n'
        '    "hashtags": "#fy #ciencia ..."\n'
        '  },\n'
        '  "instagram_reels": {\n'
        '    "title": "...",\n'
        '    "caption": "...",\n'
        '    "hashtags": "#astronomia #curiosidades ..."\n'
        '  },\n'
        '  "youtube_shorts": {\n'
        '    "title": "...",\n'
        '    "caption": "...",\n'
        '    "hashtags": "#Shorts #Ciencia ..."\n'
        '  }\n'
        '}'
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        raw = _call_ollama(messages, cfg) if OLLAMA_ENABLED else _call_groq(messages, cfg)
        return _parse_json_response(raw)
    except Exception as exc:
        logger.warning("Falha ao gerar metadados de redes sociais: %s", exc)
        return {
            "tiktok": {
                "title": f"😱 {clip_title}",
                "caption": f"{clip_hook} Você sabia disso? Siga para mais curiosidades científicas!",
                "hashtags": "#fy #foryou #ciencia #curiosidades #universo #astronomia",
            },
            "instagram_reels": {
                "title": f"🌌 {clip_title}",
                "caption": f"{clip_hook}\n\nO que você faria se estivesse lá? Comente abaixo! 👇",
                "hashtags": "#astronomia #universo #curiosidades #fatos #exploracao #ciencia",
            },
            "youtube_shorts": {
                "title": f"{clip_title} 🔥 #Shorts",
                "caption": f"{clip_hook}\nAssista ao documentário completo no nosso canal!",
                "hashtags": "#Shorts #Ciencia #Universo",
            },
        }
