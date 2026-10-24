#!/usr/bin/env python3
"""
build_composition.py — Gera render/index.html a partir de scene.json e template_wide.html,
com suporte a conversão de imagens para Base64 Data URI e Motion Design procedural animado.
"""

from __future__ import annotations

import base64
import html
import json
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compute_duration import compute_scene_duration
from scripts.config_loader import get_palette, load_config

logger = logging.getLogger("build_composition")


def _image_to_data_uri(image_path_or_url: str) -> str:
    """Converte um arquivo de imagem local para Base64 Data URI para carregamento instantâneo offline."""
    if not image_path_or_url:
        return ""

    p = Path(image_path_or_url)
    if p.exists() and p.is_file() and p.stat().st_size > 0:
        suffix = p.suffix.lower()
        mime = "image/jpeg"
        if suffix == ".png":
            mime = "image/png"
        elif suffix == ".webp":
            mime = "image/webp"
        try:
            b64_content = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{b64_content}"
        except Exception as exc:
            logger.warning("Falha ao converter imagem para base64: %s", exc)

    return image_path_or_url


def _clean_source_title(title: str, publisher: str = "") -> str:
    """Remove caracteres asiáticos/orientais e higieniza títulos para exibição em português."""
    if not title:
        return publisher or "Fonte Confiável"
    cleaned = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -·|:")
    if len(cleaned) < 3:
        cleaned = publisher or "Artigo Científico"
    return cleaned[:42]


def build_composition(
    scene_path: str,
    words_path: str,
    template_path: str,
    output_path: str,
    padding: float = 0.3,
):
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    cfg = load_config()
    palette = get_palette(scene.get("palette", "dark-neon"), cfg)
    scene_duration = compute_scene_duration(words_path, padding=padding)

    template = Path(template_path).read_text(encoding="utf-8")
    sources = {source["id"]: source for source in scene.get("sources", [])}

    clips_html = []
    cursor = 0.0
    role_labels = {
        "title": "A PERGUNTA / TÍTULO",
        "subtitle": "IDEIA-CHAVE",
        "body": "MECANISMO & CIÊNCIA",
        "image": "OBSERVAÇÃO REAL",
        "shape": "MODELO TEÓRICO",
    }

    elements = scene.get("elements", [])
    total_elements = len(elements)

    for index, el in enumerate(elements, start=1):
        dur = float(el.get("duration_seconds", 4.0))
        content = html.escape(str(el.get("content", "")))
        source_ids = el.get("source_ids", [])
        cited_sources = [sources[sid] for sid in source_ids if sid in sources]

        source_line = ""
        if cited_sources:
            citations = "  ·  ".join(
                (
                    f'<span class="citation" title="{html.escape(s.get("url", ""), quote=True)}">'
                    f'<b>[{html.escape(s.get("id", ""))}</b> '
                    f'<i>{html.escape(_clean_source_title(s.get("title", ""), s.get("publisher", "")))}</i></span>'
                )
                for s in cited_sources
            )
            source_line = f'<div class="clip-sources">FONTES CIENTÍFICAS  /  {citations}</div>'

        # Verifica se há imagem associada
        image_src = el.get("image_path") or el.get("image_url") or ""
        data_uri = _image_to_data_uri(image_src)

        if data_uri:
            credit = html.escape(str(el.get("image_credit") or "Domínio Público / CC"))
            media_html = f'''
      <div class="clip-right-media">
        <div class="media-image-frame">
          <img src="{data_uri}" alt="Ilustração">
          <div class="image-credit-badge">Fonte: <b>{credit}</b></div>
        </div>
      </div>'''
        else:
            # Motion Design Procedural Neon Dinâmico
            media_html = '''
      <div class="clip-right-media">
        <div class="motion-design-graphic">
          <div class="orbit-ring ring-outer"></div>
          <div class="orbit-ring ring-mid"></div>
          <div class="orbit-ring ring-inner"></div>
          <div class="pulse-core"></div>
          <div class="hud-label">MOTION DESIGN // CIÊNCIA</div>
        </div>
      </div>'''

        role = html.escape(role_labels.get(el.get("type"), "EXPLICAÇÃO"))

        clips_html.append(f'''
    <div id="el-{index}" class="explainer-clip"
         data-start="{cursor:.3f}" data-duration="{dur:.3f}">
      <div class="clip-left-content">
        <div class="clip-heading">
          <span class="clip-index">{index:02d}</span>
          <span>{role}</span>
        </div>
        <div class="clip-copy">{content}</div>
        {source_line}
      </div>
      {media_html}
    </div>''')
        cursor += dur

    rendered_html = template.replace("{{CLIPS}}", "\n".join(clips_html))
    rendered_html = rendered_html.replace("{{SCENE_DURATION}}", str(scene_duration))
    rendered_html = rendered_html.replace("{{PALETTE_PRIMARY}}", palette.primary)
    rendered_html = rendered_html.replace("{{PALETTE_ACCENT}}", palette.accent)
    rendered_html = rendered_html.replace("{{PALETTE_TEXT}}", palette.text)
    rendered_html = rendered_html.replace("{{PALETTE_BACKGROUND}}", palette.background)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(rendered_html, encoding="utf-8")
    logger.info("Composição gerada com sucesso: %s (%.2fs)", output_path, scene_duration)
    return scene_duration


if __name__ == "__main__":
    build_composition(
        scene_path="output/scene.json",
        words_path="output/voice.words.json",
        template_path="render/src/template_wide.html",
        output_path="render/index.html",
    )