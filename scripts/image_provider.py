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


def search_wikimedia_image(
    query: str,
    used_urls: Optional[set[str]] = None,
    timeout: float = 12.0,
) -> Optional[Dict[str, Any]]:
    """Busca imagens de alta qualidade no Wikimedia Commons com licença e autor, evitando duplicatas."""
    clean_q = _clean_query(query)
    if not clean_q:
        return None

    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{clean_q} filetype:bitmap",
        "gsrnamespace": "6",  # Namespace File:
        "gsrlimit": "10",
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

            # Evita reutilizar a mesma imagem já exibida em outro capítulo
            if not thumb_url:
                continue
            if used_urls is not None and (thumb_url in used_urls or orig_url in used_urls):
                continue

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

            # Prefere imagens com resolução razoável (>= 600px)
            if width >= 600:
                if used_urls is not None:
                    used_urls.add(thumb_url)
                    if orig_url:
                        used_urls.add(orig_url)
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


def search_wikimedia_gif(
    query: str,
    used_urls: Optional[set[str]] = None,
    timeout: float = 12.0,
) -> Optional[Dict[str, Any]]:
    """Busca GIFs e simulações animadas científicas no Wikimedia Commons."""
    clean_q = _clean_query(query)
    if not clean_q:
        return None

    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{clean_q} filetype:bitmap .gif",
        "gsrnamespace": "6",
        "gsrlimit": "12",
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime",
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
            gif_url = info.get("url") or info.get("thumburl")
            if not gif_url or ".gif" not in gif_url.lower():
                continue

            if used_urls is not None and gif_url in used_urls:
                continue

            meta = info.get("extmetadata", {})
            artist = meta.get("Artist", {}).get("value", "")
            artist = re.sub(r"<[^>]+>", "", artist).strip()
            artist = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", artist).strip() or "Wikimedia Commons"
            license_name = meta.get("LicenseShortName", {}).get("value", "Domínio Público / CC")
            title = page.get("title", "").replace("File:", "").replace("_", " ").replace(".gif", "")
            title = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", title).strip() or "Animação Científica"

            if used_urls is not None:
                used_urls.add(gif_url)

            return {
                "source": "wikimedia_gif",
                "title": title,
                "image_url": gif_url,
                "author": artist[:60],
                "license": license_name,
                "is_gif": True,
                "width": info.get("width", 800),
                "height": info.get("height", 600),
            }
    except Exception as exc:
        logger.debug("Wikimedia GIF search falhou para '%s': %s", query, exc)
    return None


def search_multiple_gifs(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Retorna uma lista de GIFs disponíveis para escolha ou pré-visualização."""
    clean_q = _clean_query(query)
    if not clean_q:
        return []

    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{clean_q} filetype:bitmap .gif",
        "gsrnamespace": "6",
        "gsrlimit": str(limit * 2),
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime",
        "format": "json",
    }

    results = []
    try:
        resp = requests.get(api_url, params=params, headers={"User-Agent": USER_AGENT}, timeout=10.0)
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                image_info = page.get("imageinfo", [])
                if not image_info:
                    continue
                info = image_info[0]
                gif_url = info.get("url") or ""
                if not gif_url or ".gif" not in gif_url.lower():
                    continue

                meta = info.get("extmetadata", {})
                artist = meta.get("Artist", {}).get("value", "")
                artist = re.sub(r"<[^>]+>", "", artist).strip() or "Wikimedia Commons"
                license_name = meta.get("LicenseShortName", {}).get("value", "Domínio Público / CC")
                title = page.get("title", "").replace("File:", "").replace("_", " ").replace(".gif", "")

                results.append({
                    "title": title,
                    "url": gif_url,
                    "thumb": info.get("thumburl") or gif_url,
                    "author": artist[:60],
                    "license": license_name,
                    "width": info.get("width", 800),
                    "height": info.get("height", 600),
                })
                if len(results) >= limit:
                    break
    except Exception as exc:
        logger.warning("Falha ao buscar múltiplos GIFs: %s", exc)
    return results

    return None


# Mapeamento semântico de termos científicos para conceitos visuais de alta fidelidade
SCIENTIFIC_CONCEPTS_MAP = [
    (r"(câncer|tumor|carcinoma|oncol|célula|biópsia|mutação celular)", ["Cancer_cell", "Mitosis", "Tumor", "Cell_biology"]),
    (r"(imunoterap|sistema imune|anticorpo|linfócit|t-cell|car-t)", ["Immunotherapy", "T_cell", "Antibody", "Immune_system"]),
    (r"(dna|genoma|mutação|gene|genétic|crispr|código genético)", ["DNA", "Gene_editing", "Chromosome", "Mutation"]),
    (r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos)", ["Quasar", "Black_hole", "Accretion_disk", "Supermassive_black_hole"]),
    (r"(galáxia|universo|hubble|james webb|telescópio|estrela|supernova|nebulosa)", ["Galaxy", "James_Webb_Space_Telescope", "Supernova", "Nebula", "Milky_Way"]),
    (r"(inteligência artificial|rede neural|algoritmo|deep learning|robô|computação)", ["Artificial_intelligence", "Artificial_neural_network", "Robotics"]),
    (r"(átomo|quântic|elétron|próton|física de partículas|fóton)", ["Atom", "Quantum_mechanics", "Particle_physics"]),
    (r"(cérebro|neurônio|sinapse|neurociência|cogni)", ["Neuron", "Brain", "Synapse"]),
]


def extract_scientific_terms(topic: str, title: str, narration: str = "") -> list[str]:
    """Extrai entidades científicas específicas para encontrar imagens fidedignas ao tema falado."""
    combined = f"{topic} {title} {narration}".lower()
    candidates: list[str] = []
    for pattern, terms in SCIENTIFIC_CONCEPTS_MAP:
        if re.search(pattern, combined):
            for t in terms:
                if t not in candidates:
                    candidates.append(t)

    # Se não houver correspondência nas categorias principais, extrai substantivos-chave
    if not candidates:
        words = [w for w in re.sub(r"[^\w\s]", " ", title).split() if len(w) > 3]
        if words:
            candidates.append(words[0].capitalize())
    return candidates


def search_wikipedia_image(
    term: str,
    lang: str = "en",
    used_urls: Optional[set[str]] = None,
    timeout: float = 8.0,
) -> Optional[Dict[str, Any]]:
    """Busca imagem oficial e representativa de um conceito científico na Wikipedia REST API, evitando duplicatas."""
    clean_term = term.strip().replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_term)}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            img_data = data.get("originalimage") or data.get("thumbnail")
            if img_data and img_data.get("source"):
                img_url = img_data["source"]
                if used_urls is not None and img_url in used_urls:
                    return None

                title = data.get("title", clean_term).replace("_", " ")
                desc = data.get("description", "Ilustração Científica Oficial")
                author = "Wikipedia / Wikimedia Commons"
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

                if used_urls is not None:
                    used_urls.add(img_url)
                    if page_url:
                        used_urls.add(page_url)

                return {
                    "source": f"wikipedia_{lang}",
                    "title": f"{title} ({desc})",
                    "image_url": img_url,
                    "page_url": page_url,
                    "author": author,
                    "license": "Domínio Público / CC-BY-SA",
                    "width": img_data.get("width", 1920),
                    "height": img_data.get("height", 1080),
                }
    except Exception as exc:
        logger.debug("Wikipedia image falhou para '%s': %s", term, exc)
    return None


def search_free_image(
    query: str,
    topic: str = "",
    chapter_title: str = "",
    narration: str = "",
    visual_keywords: Optional[List[str]] = None,
    used_urls: Optional[set[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Busca imagem de alta fidelidade ligada exatamente ao assunto falado neste capítulo específico."""
    # 1. Prioridade máxima: visual_keywords sugeridas pelo LLM para o conteúdo específico do capítulo
    if visual_keywords:
        for kw in visual_keywords:
            if not kw or len(kw.strip()) < 3:
                continue
            clean_kw = kw.strip()
            # Se for pedido de simulação ou animação, tenta GIF primeiro
            if re.search(r"(simulat|animat|orbit|collis|wave|pulsar|rotation|gif)", clean_kw, re.IGNORECASE):
                gif_res = search_wikimedia_gif(clean_kw, used_urls=used_urls)
                if gif_res:
                    return gif_res

            # Tenta Wikipedia
            res = search_wikipedia_image(clean_kw, lang="en", used_urls=used_urls)
            if res:
                return res
            # Tenta Wikimedia Commons
            res = search_wikimedia_image(clean_kw, used_urls=used_urls)
            if res:
                return res

    # 2. Termos científicos específicos extraídos apenas do título e narração do capítulo (evitando poluição do topic global)
    ch_terms = extract_scientific_terms(chapter_title, chapter_title, narration)
    for t in ch_terms[:3]:
        # Tenta GIF se o capítulo falar de dinâmica/movimento
        if re.search(r"(movimento|órbita|rotação|fusão|colisão|expansão|onda|pulso|reação)", f"{chapter_title} {narration}", re.IGNORECASE):
            gif_res = search_wikimedia_gif(t, used_urls=used_urls)
            if gif_res:
                return gif_res

        res = search_wikipedia_image(t, lang="en", used_urls=used_urls)
        if res:
            return res
        res = search_wikimedia_image(t, used_urls=used_urls)
        if res:
            return res

    # 3. Tentativa no Wikimedia Commons com o título do capítulo limpo
    if chapter_title:
        res = search_wikimedia_image(chapter_title, used_urls=used_urls)
        if res:
            return res

    # 4. Termos do tópico geral somente como fallback se nada for encontrado para o capítulo
    if topic:
        topic_terms = extract_scientific_terms(topic, "", "")
        for t in topic_terms[:3]:
            res = search_wikipedia_image(t, lang="en", used_urls=used_urls)
            if res:
                return res
            res = search_wikimedia_image(t, used_urls=used_urls)
            if res:
                return res

    # 5. Fallback final com a query pura
    if query:
        res = search_wikimedia_image(query, used_urls=used_urls)
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
    if ".gif" in url.lower():
        ext = "gif"
    elif ".png" in url.lower():
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
    """Busca e baixa uma imagem representativa e ÚNICA para cada capítulo do vídeo."""
    images = []
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    used_urls: set[str] = set()

    for i, ch in enumerate(chapters):
        ch_title = ch.get("title", "")
        ch_narration = ch.get("narration", "")
        visual_kws = ch.get("visual_keywords", [])
        if isinstance(visual_kws, str):
            visual_kws = [k.strip() for k in visual_kws.split(",") if k.strip()]

        info = search_free_image(
            query=ch_title,
            topic=topic,
            chapter_title=ch_title,
            narration=ch_narration,
            visual_keywords=visual_kws,
            used_urls=used_urls,
        )
        if info:
            local = download_image(info, dest_dir, filename_prefix=f"ch_{i+1:02d}")
            if local:
                info["local_path"] = str(local.resolve())
                info["filename"] = local.name
                images.append(info)
                continue
        images.append(None)

    return images
