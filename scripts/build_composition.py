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
    """Remove caracteres orientais, limpa sufixos redundantes e trunca respeitando palavras inteiras."""
    if not title:
        return publisher or "Fonte Científica"

    # Remove caracteres de scripts orientais ou cirílicos
    cleaned = re.sub(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff]+", "", title)

    # Remove sufixos repetitivos comuns em títulos de sites (ex: " - Brasil Escola", " | Toda Matéria", " – Wikipédia")
    cleaned = re.sub(
        r"\s*[-–—|:]\s*(Brasil Escola|Toda Matéria|Wikipédia|Wikipedia|UOL|Mundo Educação|Canaltech|G1|BBC|TechTudo).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -–—·|:")

    if len(cleaned) < 3:
        cleaned = publisher or "Artigo Científico"

    # Trunca respeitando palavras completas (máximo ~45 caracteres)
    if len(cleaned) > 45:
        cutoff = cleaned[:45].rfind(" ")
        if cutoff > 20:
            cleaned = cleaned[:cutoff] + "…"
        else:
            cleaned = cleaned[:42] + "…"

    return cleaned


def detect_visual_theme(
    topic: str,
    content: str,
    chapter_title: str = "",
    explicit_archetype: str = "",
) -> tuple[str, str]:
    """Detecta o campo da ciência e subtema para gerar Motion Design contextualizado."""
    clean_sub = re.sub(r"[^\w\s]", "", chapter_title or topic).strip()[:24].upper()
    label_suffix = clean_sub if clean_sub else "CIÊNCIA & DADOS"

    if explicit_archetype:
        arch = explicit_archetype.lower().strip()
        arch_labels = {
            "orbital": ("orbital", f"DINÂMICA ORBITAL // {label_suffix}"),
            "infographic": ("infographic", f"TELEMETRIA & DADOS // {label_suffix}"),
            "blueprint": ("blueprint", f"DIAGRAMA TÉCNICO // {label_suffix}"),
            "spectrum": ("spectrum", f"ESPECTRO & ONDAS // {label_suffix}"),
            "network": ("network", f"REDE DE CONEXÕES // {label_suffix}"),
            "timeline": ("timeline", f"CRONOLOGIA CÓSMICA // {label_suffix}"),
            "quantum": ("quantum", f"ESTRUTURA QUÂNTICA // {label_suffix}"),
        }
        if arch in arch_labels:
            return arch_labels[arch]

    text = f"{topic} {chapter_title} {content}".lower()

    if re.search(r"(câncer|tumor|carcinoma|oncol|célula|biópsia|dna|genoma|mutação|gene|imunoterap|imune|anticorpo|linfócit|vírus|vacina|biolog|sangue|medicin)", text):
        return "network", f"BIOLOGIA & CÉLULAS // {label_suffix}"

    if re.search(r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos|espaço|astro|galáxia|universo|estrela|supernova)", text):
        return "orbital", f"ASTROFÍSICA & COSMO // {label_suffix}"

    if re.search(r"(telescópio|hubble|james webb|óptica|espelho|observatório|detector|resolução|coordenadas)", text):
        return "blueprint", f"OBSERVAÇÃO TÉCNICA // {label_suffix}"

    if re.search(r"(luz|onda|espectro|frequência|comprimento de onda|doppler|redshift|radiação|eletromagnét)", text):
        return "spectrum", f"ESPECTROGRAFIA // {label_suffix}"

    if re.search(r"(tempo|evolução|anos|milhões de anos|história|origem|cronologia|big bang)", text):
        return "timeline", f"EVOLUÇÃO TEMPORAL // {label_suffix}"

    if re.search(r"(átomo|quântic|elétron|próton|fóton|física|partícula)", text):
        return "quantum", f"MECÂNICA QUÂNTICA // {label_suffix}"

    if re.search(r"(inteligência artificial|ia|rede neural|algoritmo|computador|dados|deep learning)", text):
        return "network", f"SISTEMAS NEURAIS // {label_suffix}"

    return "infographic", f"DADOS & MEDIÇÃO // {label_suffix}"


def generate_thematic_motion_html(theme: str, label: str) -> str:
    """Retorna Motion Design vetorial procedural específico do assunto falado."""
    if theme in ("orbital", "astronomy"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-orbital">
          <div class="plasma-jet"></div>
          <div class="accretion-disk disk-outer"></div>
          <div class="accretion-disk disk-inner"></div>
          <div class="event-horizon"></div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme == "infographic":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-infographic">
          <svg class="radial-gauge-svg" viewBox="0 0 360 360" width="360" height="360">
            <circle class="gauge-bg" cx="180" cy="180" r="140" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
            <circle class="gauge-bar" cx="180" cy="180" r="140" fill="none" stroke="var(--palettePrimary)" stroke-width="10" stroke-dasharray="880" stroke-dashoffset="260" stroke-linecap="round"/>
            <circle class="gauge-inner-ring" cx="180" cy="180" r="105" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="6 8"/>
          </svg>
          <div class="infographic-bars">
            <div class="meter-bar bar-1"></div>
            <div class="meter-bar bar-2"></div>
            <div class="meter-bar bar-3"></div>
            <div class="meter-bar bar-4"></div>
          </div>
          <div class="gauge-center-readout">
            <span class="readout-val">98.4%</span>
            <span class="readout-unit">FLUXO RELATIVÍSTICO</span>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme == "blueprint":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-blueprint">
          <div class="crosshair-axis axis-x"></div>
          <div class="crosshair-axis axis-y"></div>
          <div class="blueprint-reticle ret-outer"></div>
          <div class="blueprint-reticle ret-mid"></div>
          <div class="blueprint-reticle ret-inner"></div>
          <div class="blueprint-corner tl"></div>
          <div class="blueprint-corner tr"></div>
          <div class="blueprint-corner bl"></div>
          <div class="blueprint-corner br"></div>
          <div class="blueprint-hud-coords">AZ: 184.22° // EL: +47.19° // RA: 12h 55m</div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme == "spectrum":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-spectrum">
          <svg class="spectrum-svg" viewBox="0 0 420 280" width="420" height="280">
            <path class="sine-wave wave-1" d="M 0 140 Q 52.5 60 105 140 T 210 140 T 315 140 T 420 140" fill="none" stroke="var(--palettePrimary)" stroke-width="3"/>
            <path class="sine-wave wave-2" d="M 0 140 Q 52.5 210 105 140 T 210 140 T 315 140 T 420 140" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="4 4"/>
          </svg>
          <div class="spectrum-dispersion-bar"></div>
          <div class="spectral-absorption-lines">
            <div class="abs-line line-1"></div>
            <div class="abs-line line-2"></div>
            <div class="abs-line line-3"></div>
            <div class="abs-line line-4"></div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("network", "biology", "neural_tech"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-network">
          <svg class="network-svg" viewBox="0 0 380 380" width="380" height="380">
            <line x1="190" y1="190" x2="80" y2="90" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="4 4"/>
            <line x1="190" y1="190" x2="300" y2="90" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="4 4"/>
            <line x1="190" y1="190" x2="310" y2="280" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="4 4"/>
            <line x1="190" y1="190" x2="70" y2="270" stroke="rgba(255,255,255,0.2)" stroke-width="2" stroke-dasharray="4 4"/>
            <circle class="net-node node-a" cx="80" cy="90" r="14" fill="var(--paletteAccent)"/>
            <circle class="net-node node-b" cx="300" cy="90" r="12" fill="var(--palettePrimary)"/>
            <circle class="net-node node-c" cx="310" cy="280" r="15" fill="var(--paletteAccent)"/>
            <circle class="net-node node-d" cx="70" cy="270" r="11" fill="var(--palettePrimary)"/>
          </svg>
          <div class="network-core"></div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme == "timeline":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-timeline">
          <div class="timeline-axis"></div>
          <div class="timeline-nodes">
            <div class="tl-node n-1"><div class="tl-pulse"></div><span>T-0</span></div>
            <div class="tl-node n-2"><div class="tl-pulse"></div><span>ERA I</span></div>
            <div class="tl-node n-3"><div class="tl-pulse"></div><span>ERA II</span></div>
            <div class="tl-node n-4 active"><div class="tl-pulse"></div><span>PRESENTE</span></div>
          </div>
          <div class="timeline-scanner-beam"></div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("quantum", "quantum_physics"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-quantum">
          <div class="quantum-orbit q-1"></div>
          <div class="quantum-orbit q-2"></div>
          <div class="quantum-orbit q-3"></div>
          <div class="quantum-nucleus"></div>
          <div class="hud-label">{label}</div>
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
          <div class="hud-label">{label}</div>
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
            arch = el.get("visual_archetype") or scene.get("visual_archetype") or ""
            ch_title = scene.get("chapter_title") or ""
            theme_key, theme_label = detect_visual_theme(topic_text, el.get("content", ""), ch_title, explicit_archetype=arch)
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