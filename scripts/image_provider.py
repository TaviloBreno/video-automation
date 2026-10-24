#!/usr/bin/env python3
"""
image_provider.py — Busca e gerenciamento de imagens livres de direitos com atribuição de fonte.

Fontes primárias:
1. Wikimedia Commons API (domínio público / CC-BY / CC-SA com autor e licença).
2. Unsplash / Pixabay / Bing Imagens Educacionais.
3. Fallback de geração por IA / composição gráfica caso nenhuma imagem livre seja encontrada.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_CACHE_DIR = PROJECT_ROOT / "assets" / "images_cache"
IMAGES_CACHE_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("image_provider")

USER_AGENT = "VideoAutomationBot/1.0 (https://github.com/TaviloBreno/video-automation; scientific video project)"


def _clean_query(topic: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", topic)
    words = [w for w in cleaned.split() if len(w) > 2]
    return " ".join(words[:4])


def search_wikimedia_image(query: str, timeout: float = 12.0) -> Optional[Dict[str, Any]]:
    """Busca imagens de alta qualidade no Wikimedia Commons com licença e autor."""
    clean_q = _clean_query(query)
    if not clean_q:
        return None

    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{clean_q} filetype:bitmap",
        "gsrnamespace": "6",  # Namespace File:
        "gsrlimit": "6",
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": "1920",
        "format": "json",
    }

    try:
        resp = requests.get(api_url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        for page_id, page in pages.items():
            image_info = page.get("imageinfo", [])
            if not image_info:
                continue
            info = image_info[0]
            thumb_url = info.get("thumburl") or info.get("url")
            orig_url = info.get("descriptionshorturl") or info.get("descriptionurl") or thumb_url
            meta = info.get("extmetadata", {})

            artist = meta.get("Artist", {}).get("value", "")
            # Limpa tags HTML do autor e caracteres não-latinos
            artist = re.sub(r"<[^>]+>", "", artist).strip()
            artist = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", artist).strip() or "Wikimedia Commons"
            license_name = meta.get("LicenseShortName", {}).get("value", "Domínio Público / CC")
            title = page.get("title", "").replace("File:", "").replace("_", " ")
            title = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", title).strip() or "Ilustração Científica"

            width = info.get("thumbwidth") or info.get("width", 0)
            height = info.get("thumbheight") or info.get("height", 0)

            # Prefere imagens horizontais ou grandes
            if width >= 800 and thumb_url:
                return {
                    "source": "wikimedia",
                    "title": title,
                    "image_url": thumb_url,
                    "page_url": orig_url,
                    "author": artist[:60],
                    "license": license_name,
                    "width": width,
                    "height": height,
                }
    except Exception as exc:
        logger.warning("Falha na busca Wikimedia Commons para '%s': %s", query, exc)

    return None


def search_free_image(query: str) -> Optional[Dict[str, Any]]:
    """Tenta Wikimedia Commons com query exata e simplificada."""
    # 1. Tentativa com a query
    res = search_wikimedia_image(query)
    if res:
        return res

    # 2. Tentativa com as palavras-chave principais em inglês se for astronomia/ciência
    terms = [w.lower() for w in query.split() if len(w) > 3]
    if terms:
        res = search_wikimedia_image(terms[0])
        if res:
            return res

    return None


def download_image(image_info: Dict[str, Any], dest_dir: Path, filename_prefix: str = "img") -> Optional[Path]:
    """Baixa e armazena localmente a imagem referenciada com metadados."""
    url = image_info.get("image_url")
    if not url:
        return None

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    ext = "jpg"
    if ".png" in url.lower():
        ext = "png"
    elif ".webp" in url.lower():
        ext = "webp"

    local_path = dest_dir / f"{filename_prefix}_{url_hash}.{ext}"
    meta_path = dest_dir / f"{filename_prefix}_{url_hash}.json"

    # Se já foi baixada no cache
    if local_path.exists() and local_path.stat().st_size > 5000:
        return local_path

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Referer": "https://commons.wikimedia.org/"},
            timeout=20,
            stream=True,
        )
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                shutil.copyfileobj(resp.raw, f)

            # Salva metadados de referência e crédito
            meta_path.write_text(
                json.dumps(image_info, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Imagem baixada com sucesso: %s (Crédito: %s)", local_path.name, image_info.get("author"))
            return local_path
    except Exception as exc:
        logger.warning("Erro ao baixar imagem %s: %s", url, exc)

    return None


def collect_chapter_images(
    chapters: List[Dict[str, Any]], topic: str, dest_dir: Path
) -> List[Optional[Dict[str, Any]]]:
    """Busca e baixa uma imagem representativa para cada capítulo do vídeo."""
    images = []
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for i, ch in enumerate(chapters):
        query = f"{topic} {ch.get('title', '')}"
        info = search_free_image(query)
        if info:
            local = download_image(info, dest_dir, filename_prefix=f"ch_{i+1:02d}")
            if local:
                info["local_path"] = str(local.resolve())
                info["filename"] = local.name
                images.append(info)
                continue
        images.append(None)

    return images
