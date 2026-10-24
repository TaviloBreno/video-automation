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


def detect_visual_theme(topic: str, content: str, chapter_title: str = "") -> tuple[str, str]:
    """Detecta o campo da ciência e subtema para gerar Motion Design contextualizado."""
    text = f"{topic} {chapter_title} {content}".lower()

    if re.search(r"(câncer|tumor|carcinoma|oncol|célula|biópsia|dna|genoma|mutação|gene|imunoterap|imune|anticorpo|linfócit|vírus|vacina|biolog|sangue|medicin)", text):
        if re.search(r"(imunoterap|imune|anticorpo|linfócit|t-cell)", text):
            label = "IMUNOTERAPIA & DEFESA"
        elif re.search(r"(dna|genoma|mutação|gene|crispr)", text):
            label = "GENÉTICA & DNA"
        elif re.search(r"(tumor|carcinoma|metástase)", text):
            label = "ONCOLOGIA CELULAR"
        else:
            label = "BIOLOGIA & CÉLULAS"
        return "biology", label

    if re.search(r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos|espaço|astro|galáxia|universo|estrela|supernova|hubble|james webb|telescópio|relativid)", text):
        if re.search(r"(buraco negro|singularidade|horizonte)", text):
            label = "BURACO NEGRO & SINGULARIDADE"
        elif re.search(r"(quasar|quásar|acrec)", text):
            label = "QUASAR & ENERGIA RELATIVÍSTICA"
        elif re.search(r"(supernova|estrela)", text):
            label = "EVOLUÇÃO ESTELAR"
        else:
            label = "ASTROFÍSICA & COSMO"
        return "astronomy", label

    if re.search(r"(inteligência artificial|ia|rede neural|algoritmo|computador|software|dados|deep learning|robô|chip|silício)", text):
        return "neural_tech", "REDES NEURAIS & IA"

    if re.search(r"(átomo|quântic|elétron|próton|fóton|física|partícula|radiação)", text):
        return "quantum_physics", "FÍSICA QUÂNTICA & ÁTOMOS"

    clean_sub = re.sub(r"[^\w\s]", "", chapter_title or topic).strip()
    return "science_general", (clean_sub[:24].upper() if clean_sub else "EXPLORAÇÃO CIENTÍFICA")


def generate_thematic_motion_html(theme: str, label: str) -> str:
    """Retorna Motion Design vetorial procedural específico do assunto falado."""
    if theme == "astronomy":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-astro">
          <div class="plasma-jet"></div>
          <div class="accretion-disk disk-outer"></div>
          <div class="accretion-disk disk-inner"></div>
          <div class="event-horizon"></div>
          <div class="hud-label">ASTROFÍSICA // {label}</div>
        </div>
      </div>'''
    elif theme == "biology":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-bio">
          <div class="cell-membrane"></div>
          <div class="dna-helix">
            <div class="dna-ring ring-a"></div>
            <div class="dna-ring ring-b"></div>
          </div>
          <div class="cell-nucleus"></div>
          <div class="hud-label">BIOLOGIA CELULAR // {label}</div>
        </div>
      </div>'''
    elif theme == "neural_tech":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-neural">
          <div class="neural-grid">
            <div class="synapse-orbit syn-1"></div>
            <div class="synapse-orbit syn-2"></div>
            <div class="neural-core"></div>
          </div>
          <div class="hud-label">SISTEMAS NEURAIS // {label}</div>
        </div>
      </div>'''
    elif theme == "quantum_physics":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-quantum">
          <div class="quantum-orbit q-1"></div>
          <div class="quantum-orbit q-2"></div>
          <div class="quantum-orbit q-3"></div>
          <div class="quantum-nucleus"></div>
          <div class="hud-label">ESTRUTURA ATÔMICA // {label}</div>
        </div>
      </div>'''
    else:
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic">
          <div class="orbit-ring ring-outer"></div>
          <div class="orbit-ring ring-mid"></div>
          <div class="orbit-ring ring-inner"></div>
          <div class="pulse-core"></div>
          <div class="hud-label">CIÊNCIA & DADOS // {label}</div>
        </div>
      </div>'''


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
    narration_text = scene.get("narration_text", "")
    topic_text = scene.get("topic", "")

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
            # Motion Design Procedural Neon Temático e Específico do Assunto Falado
            theme_key, theme_label = detect_visual_theme(topic_text, el.get("content", ""), narration_text)
            media_html = generate_thematic_motion_html(theme_key, theme_label)

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