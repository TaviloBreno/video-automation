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
        elif suffix == ".gif":
            mime = "image/gif"
        try:
            b64_content = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{b64_content}"
        except Exception as exc:
            logger.warning("Falha ao converter imagem para base64: %s", exc)

    return image_path_or_url


def _clean_source_title(title: str, publisher: str = "") -> str:
    """Remove caracteres orientais, limpa sufixos redundantes e trunca respeitando palavras inteiras."""
    if not title:
        return publisher or "Fonte de Pesquisa"

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
        cleaned = publisher or "Artigo de Pesquisa"

    # Trunca respeitando palavras completas (máximo ~90 caracteres para preservar títulos ricos)
    if len(cleaned) > 90:
        cutoff = cleaned[:90].rfind(" ")
        if cutoff > 45:
            cleaned = cleaned[:cutoff] + "…"
        else:
            cleaned = cleaned[:86] + "…"

    return cleaned


def _format_dynamic_copy(raw_content: str) -> str:
    """Evita textos monolíticos e monótonos na tela: fragmenta a fala em linhas cinéticas e destaca números e grandezas."""
    if not raw_content:
        return ""

    escaped = html.escape(str(raw_content).strip())

    # Destaca grandezas numéricas e unidades (ex: 13,8 bilhões, 300.000 km/s, 99.4%, 100x)
    styled = re.sub(
        r"(\b\d+([.,]\d+)?\s*(%|km/s|anos-luz|bilhões|milhões|vezes|km|graus|K|ºC|Hz|nm)\b)",
        r'<span class="stat-highlight">\1</span>',
        escaped,
        flags=re.IGNORECASE,
    )

    # Divide frases para animar dinamicamente na tela
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", styled) if s.strip()]
    if len(sentences) > 1:
        return "".join(f'<span class="kinetic-line">{s} </span>' for s in sentences)

    return f'<span class="kinetic-line">{styled}</span>'


def detect_visual_theme(
    topic: str,
    content: str,
    chapter_title: str = "",
    explicit_archetype: str = "",
) -> tuple[str, str]:
    """Detecta o campo do conhecimento e subtema para gerar Motion Design estritamente contextualizado ao assunto."""
    raw_sub = re.sub(r"[^\w\s]", "", chapter_title or topic).strip()
    if len(raw_sub) > 36:
        cutoff = raw_sub[:36].rfind(" ")
        clean_sub = raw_sub[:cutoff].upper() if cutoff > 18 else raw_sub[:36].upper()
    else:
        clean_sub = raw_sub.upper()
    label_suffix = clean_sub if clean_sub else "DADOS & CONCEITO"

    if explicit_archetype:
        arch = explicit_archetype.lower().strip()
        arch_labels = {
            "politics": ("politics", f"DINÂMICA DE PODER & INFLUÊNCIA // {label_suffix}"),
            "social": ("politics", f"DINÂMICA SOCIAL & OPINIÃO // {label_suffix}"),
            "psychology": ("psychology", f"PSICOLOGIA COGNITIVA & MENTE // {label_suffix}"),
            "mind": ("psychology", f"COMPORTAMENTO HUMANO // {label_suffix}"),
            "orbital": ("orbital", f"DINÂMICA ORBITAL // {label_suffix}"),
            "infographic": ("infographic", f"TELEMETRIA & DADOS // {label_suffix}"),
            "blueprint": ("blueprint", f"DIAGRAMA TÉCNICO // {label_suffix}"),
            "spectrum": ("spectrum", f"ESPECTRO & ONDAS // {label_suffix}"),
            "network": ("network", f"REDE DE CONEXÕES // {label_suffix}"),
            "timeline": ("timeline", f"CRONOLOGIA HISTÓRICA // {label_suffix}"),
            "history": ("timeline", f"REGISTRO HISTÓRICO // {label_suffix}"),
            "quantum": ("quantum", f"ESTRUTURA QUÂNTICA // {label_suffix}"),
            "formula": ("formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"),
            "equation": ("formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"),
        }
        if arch in arch_labels:
            return arch_labels[arch]

    text = f"{topic} {chapter_title} {content}".lower()

    # 1. POLÍTICA, MANIPULAÇÃO, AGITADORES, ELEIÇÃO, PODER E MASSAS
    if re.search(r"(polític|manipula|agitador|eleiç|poder|propaganda|retórica|ideolog|governo|estado|voto|partido|líder|democrac|polariza|massa|autorit|opinião pública|populis|discurso)", text):
        return "politics", f"DINÂMICA DE PODER & POLÍTICA // {label_suffix}"

    # 2. PSICOLOGIA, COMPORTAMENTO, MENTE, VIESES, PERSUASÃO E COGNIÇÃO
    if re.search(r"(psicolog|mente|comportamento|persuas|viés|cogni|emoç|influên|cérebro|percepç|decisão|inconsciente|hábito|atitude)", text):
        return "psychology", f"PSICOLOGIA COGNITIVA & MENTE // {label_suffix}"

    # 3. SOCIOLOGIA, SOCIEDADE E COLETIVO
    if re.search(r"(sociedade|social|cultura|coletiv|populaç|comunidade|desigualdade|movimento social)", text):
        return "politics", f"DINÂMICA SOCIAL & COLETIVO // {label_suffix}"

    # 4. HISTÓRIA, GUERRAS E CIVILIZAÇÕES
    if re.search(r"(histór|guerra|revoluç|século|império|tratado|conflito|era moderna|antiguidade|geopolític)", text):
        return "timeline", f"REGISTRO HISTÓRICO & CRONOLOGIA // {label_suffix}"

    # 5. Fórmulas e Leis Físicas Matemáticas
    if re.search(r"(\be\s*=\s*mc|\bf\s*=\s*g|\br_s\s*=|\bkepler|\bnewton|\bhubble|\bequação|\bfórmula|\blei da grav|\bincerteza)", text):
        return "formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"

    # 6. Biologia, Células, Medicina e Saúde
    if re.search(r"(câncer|tumor|carcinoma|oncol|célula|biópsia|dna|genoma|mutação|gene|imunoterap|imune|anticorpo|linfócit|vírus|vacina|biolog|sangue|medicin)", text):
        return "network", f"BIOLOGIA & CÉLULAS // {label_suffix}"

    # 7. Astrofísica, Buracos Negros e Espaço
    if re.search(r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos|espaço|astro|galáxia|universo|estrela|supernova)", text):
        return "orbital", f"ASTROFÍSICA & COSMO // {label_suffix}"

    # 8. Telescópios e Observação
    if re.search(r"(telescópio|hubble|james webb|óptica|espelho|observatório|detector|resolução|coordenadas)", text):
        return "blueprint", f"OBSERVAÇÃO TÉCNICA // {label_suffix}"

    # 9. Luz e Ondas
    if re.search(r"(luz|onda|espectro|frequência|comprimento de onda|doppler|redshift|radiação|eletromagnét)", text):
        return "spectrum", f"ESPECTROGRAFIA // {label_suffix}"

    # 10. Evolução e Tempo
    if re.search(r"(tempo|evolução|anos|milhões de anos|origem|cronologia|big bang)", text):
        return "timeline", f"EVOLUÇÃO TEMPORAL // {label_suffix}"

    # 11. Física Quântica
    if re.search(r"(átomo|quântic|elétron|próton|fóton|física|partícula)", text):
        return "quantum", f"MECÂNICA QUÂNTICA // {label_suffix}"

    # 12. Tecnologia, IA e Redes
    if re.search(r"(inteligência artificial|ia|rede neural|algoritmo|computador|dados|deep learning)", text):
        return "network", f"SISTEMAS NEURAIS // {label_suffix}"

    return "infographic", f"DADOS & MEDIÇÃO // {label_suffix}"


def _get_formula_preset(text: str) -> dict[str, Any]:
    """Retorna fórmula matemática consagrada correspondente ao contexto."""
    lower = text.lower()
    if "buraco negro" in lower or "singularidade" in lower or "horizonte" in lower or "raio" in lower:
        return {
            "eq": "R<sub>s</sub> = <sup>2GM</sup>&frasl;<sub>c<sup>2</sup></sub>",
            "name": "Raio de Schwarzschild (Horizonte de Eventos)",
            "vars": [
                ("R<sub>s</sub>", "Raio Limite"),
                ("G", "Cte Gravitacional"),
                ("M", "Massa do Objeto"),
                ("c", "Velocidade da Luz"),
            ],
        }
    elif "hubble" in lower or "expansão" in lower or "universo" in lower or "distância" in lower:
        return {
            "eq": "v = H<sub>0</sub> &times; d",
            "name": "Lei de Hubble-Lemaître (Expansão Cósmica)",
            "vars": [
                ("v", "Velocidade de Recessão"),
                ("H<sub>0</sub>", "Constante de Hubble"),
                ("d", "Distância Cósmica"),
            ],
        }
    elif "quântic" in lower or "incerteza" in lower or "heisenberg" in lower or "partícula" in lower:
        return {
            "eq": "&Delta;x &middot; &Delta;p &ge; <sup>&hbar;</sup>&frasl;<sub>2</sub>",
            "name": "Princípio da Incerteza de Heisenberg",
            "vars": [
                ("&Delta;x", "Incerteza da Posição"),
                ("&Delta;p", "Incerteza do Momento"),
                ("&hbar;", "Constante de Planck Reduzida"),
            ],
        }
    elif "gravid" in lower or "atração" in lower or "órbita" in lower or "newton" in lower:
        return {
            "eq": "F = G &middot; <sup>(m<sub>1</sub> &middot; m<sub>2</sub>)</sup>&frasl;<sub>r<sup>2</sup></sub>",
            "name": "Lei da Gravitação Universal de Newton",
            "vars": [
                ("F", "Força Gravitacional"),
                ("G", "Constante Gravitacional"),
                ("m", "Massas Interagentes"),
                ("r", "Distância Radial"),
            ],
        }
    else:
        return {
            "eq": "E = m &middot; c<sup>2</sup>",
            "name": "Equivalência Massa-Energia de Einstein",
            "vars": [
                ("E", "Energia Repouso"),
                ("m", "Massa Relativística"),
                ("c", "Velocidade da Luz"),
            ],
        }


def generate_thematic_motion_html(theme: str, label: str) -> str:
    """Retorna Motion Design vetorial procedural específico do assunto falado."""
    if theme in ("politics", "social", "power", "opinion"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-politics">
          <div class="polarization-hud">
            <span class="hud-sub-badge">DINÂMICA DE PODER & INFLUÊNCIA</span>
            <div class="polarity-spectrum">
              <span class="pol-label left">POLO ALFA // 48%</span>
              <div class="pol-bar"><div class="pol-needle"></div></div>
              <span class="pol-label right">POLO BETA // 52%</span>
            </div>
          </div>
          <svg class="influence-net-svg" viewBox="0 0 380 230" width="380" height="230">
            <line class="inf-line" x1="60" y1="115" x2="190" y2="55" stroke="var(--palettePrimary)" stroke-width="2" stroke-dasharray="4 4"/>
            <line class="inf-line" x1="60" y1="115" x2="190" y2="175" stroke="var(--palettePrimary)" stroke-width="2" stroke-dasharray="4 4"/>
            <line class="inf-line" x1="320" y1="115" x2="190" y2="55" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="4 4"/>
            <line class="inf-line" x1="320" y1="115" x2="190" y2="175" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="4 4"/>
            <circle class="influencer-core core-a" cx="60" cy="115" r="22" fill="var(--palettePrimary)"/>
            <circle class="influencer-core core-b" cx="320" cy="115" r="22" fill="var(--paletteAccent)"/>
            <circle class="mass-node m-1" cx="190" cy="55" r="14" fill="rgba(255,255,255,0.7)"/>
            <circle class="mass-node m-2" cx="190" cy="175" r="14" fill="rgba(255,255,255,0.7)"/>
          </svg>
          <div class="politics-readouts">
            <div class="readout-pill">ÍNDICE DE PERSUASÃO: <b>89.4%</b></div>
            <div class="readout-pill">DISPERSÃO DE NARRATIVA: <b>ALTA</b></div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("psychology", "cognition", "mind", "behavior"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-psychology">
          <div class="psych-hud-header">
            <span class="hud-sub-badge">PROCESSAMENTO COGNITIVO & VIESES</span>
          </div>
          <div class="psych-brain-core">
            <div class="synapse-ring s-outer"></div>
            <div class="synapse-ring s-mid"></div>
            <div class="decision-nucleus"></div>
          </div>
          <div class="bias-scales-box">
            <div class="scale-row">
              <span class="scale-lbl">GATILHO EMOCIONAL</span>
              <div class="scale-track"><div class="scale-fill fill-accent" style="width: 86%;"></div></div>
            </div>
            <div class="scale-row">
              <span class="scale-lbl">FILTRO RACIONAL</span>
              <div class="scale-track"><div class="scale-fill fill-primary" style="width: 29%;"></div></div>
            </div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("orbital", "astronomy"):
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

    elif theme == "formula":
        preset = _get_formula_preset(label)
        vars_badges = "".join(
            f'<div class="formula-var-chip"><span class="var-sym">{v[0]}</span><span class="var-lbl">{v[1]}</span></div>'
            for v in preset["vars"]
        )
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-formula">
          <div class="formula-card">
            <div class="formula-sub-badge">LEI CIENTÍFICA FUNDAMENTAL</div>
            <div class="formula-math-display">{preset["eq"]}</div>
            <div class="formula-caption">{preset["name"]}</div>
            <div class="formula-vars-grid">{vars_badges}</div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("analytics", "chart", "data"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-analytics">
          <div class="analytics-hud-header">
            <span class="hud-sub-badge">DADOS ESTATÍSTICOS & TENDÊNCIA</span>
          </div>
          <svg class="analytics-chart-svg" viewBox="0 0 380 180" width="380" height="180">
            <line x1="40" y1="160" x2="350" y2="160" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
            <line x1="40" y1="20" x2="40" y2="160" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
            <polyline points="50,135 110,105 170,125 230,65 290,80 345,30" fill="none" stroke="var(--paletteAccent)" stroke-width="3" stroke-linecap="round"/>
            <circle cx="230" cy="65" r="5" fill="var(--palettePrimary)"/>
            <circle cx="345" cy="30" r="7" fill="var(--paletteAccent)"/>
          </svg>
          <div class="analytics-bars-row">
            <div class="stat-col"><div class="stat-fill f1" style="height: 45%;"></div><span>P1</span></div>
            <div class="stat-col"><div class="stat-fill f2" style="height: 78%;"></div><span>P2</span></div>
            <div class="stat-col"><div class="stat-fill f3" style="height: 60%;"></div><span>P3</span></div>
            <div class="stat-col"><div class="stat-fill f4" style="height: 94%;"></div><span>MAX</span></div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("radar", "sonar", "scan"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-radar">
          <div class="radar-hud-circle">
            <div class="radar-sweep-line"></div>
            <div class="radar-blip b1"></div>
            <div class="radar-blip b2"></div>
            <div class="radar-axis-x"></div>
            <div class="radar-axis-y"></div>
          </div>
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
        raw_content = str(el.get("content", ""))
        content = _format_dynamic_copy(raw_content)
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
            theme_key, theme_label = detect_visual_theme(topic_text, raw_content, ch_title, explicit_archetype=arch)
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