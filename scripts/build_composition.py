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
    """Detecta o campo do conhecimento e subtema para gerar Motion Design estritamente contextualizado ao assunto falado."""
    raw_sub = re.sub(r"[^\w\s]", "", chapter_title or topic).strip()
    if len(raw_sub) > 36:
        cutoff = raw_sub[:36].rfind(" ")
        clean_sub = raw_sub[:cutoff].upper() if cutoff > 18 else raw_sub[:36].upper()
    else:
        clean_sub = raw_sub.upper()
    label_suffix = clean_sub if clean_sub else "DADOS & CONCEITO"

    c_text = (content or "").lower()
    combined_text = f"{topic} {chapter_title} {content}".lower()

    # 0.0 Gramática, Língua Portuguesa, Crase, Regras e Ortografia
    if re.search(r"(\bcrase\b|acento grave|regência|regencia|preposição|preposicao|artigo feminino|substantivo|verbo transitivo|concordância|concordancia|ortografia|acentuação|acentuacao|sintaxe|pontuação|pontuacao|oração|oracao|vocábulo|vocabulo|língua portuguesa|lingua portuguesa|gramática|gramatica)", c_text) or re.search(r"(\bcrase\b|gramática|gramatica|língua portuguesa|português|portugues)", combined_text):
        return "grammar", f"NORMA PADRÃO & GRAMÁTICA // {label_suffix}"

    # 0.01 Certo vs Errado / Comparação Prática
    if re.search(r"(certo ou errado|correto ou incorreto|permitido ou proibido|nunca use|evite usar|forma errada|forma certa|versus|diferença entre|antes de palavra)", c_text):
        return "comparison", f"CERTO vs ERRADO // {label_suffix}"

    # 0.02 Didática, Aulas, Exemplos, Macetes e Dicas de Fixação
    if re.search(r"(macete|dica de ouro|mnemônico|mnemonico|como usar|aprenda|passo a passo|não erre|exemplo prático|exemplo pratico|na prática|na pratica|em sala|memorizar|fixar|revisão|revisao|videoaula)", c_text) or re.search(r"(aula|aprender|dica)", combined_text):
        return "lesson", f"AULA & DICA DE FIXAÇÃO // {label_suffix}"

    # 0. Finanças, Moedas, Dólar, Investimentos, Risco, Probabilidade & Mercado
    if re.search(r"(\bdólar|dolar|câmbio|cambio|real|moeda|inflação|inflacao|juros|selic|mercado|bolsa|ações|acoes|ibov|investiment|lucro|preço|preco|volatilidade|risco|probabilidade|chance|ganhar|dinheiro|bilhões|bilhoes|previsão financeira|carteira)", c_text):
        return "finance", f"MERCADO & RISCO // {label_suffix}"

    # 0.1 Lançamento de Produto, Negócios, Startups, Vendas & Marketing
    if re.search(r"(lançamento de produto|lancamento de produto|produto|marca|negócio|negocio|startup|vendas|marketing|cliente|conversão|posicionamento|empresa|comercial|novo recurso)", c_text):
        return "business", f"LANÇAMENTO // {label_suffix}"

    # 0.2 Política, Eleições, Pesquisa de Opinião, Voto & Democracia
    if re.search(r"(eleição|eleicao|eleições|eleicoes|pesquisa de opinião|pesquisa eleitoral|voto|votar|candidato|urna|partido|governo|democracia|congresso|deputado|senador|presidente|rejeição|amostragem)", c_text):
        return "politics", f"CENÁRIO ELEITORAL // {label_suffix}"

    # 1. Prioridade Semântica da Sentença: Fórmulas Matemáticas e Equações
    if re.search(r"(\be\s*=\s*mc|\bf\s*=\s*g|\br_s\s*=|equação|fórmula|lei da grav|incerteza|constante|c\^2|matemát)", c_text):
        return "formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"

    # 2. Prioridade Semântica da Sentença: Dados Estatísticos, Porcentagens, Tendência & Grandezas
    if re.search(r"(\b\d+([.,]\d+)?\s*(%|vezes|x|km/s|km|anos-luz|graus|k|ºc)\b|porcento|por cento|aumento de|queda de|estatística|gráfico|taxa de|crescimento)", c_text):
        return "analytics", f"DADOS & TENDÊNCIA ESTATÍSTICA // {label_suffix}"

    # 3. Prioridade Semântica da Sentença: Espectro de Luz, Ondas, Radiação, Frequência & Raios-X
    if re.search(r"(espectro|raios-x|radiação|frequência|onda|luminos|comprimento de onda|doppler|redshift|eletromagnét)", c_text):
        return "spectrum", f"ESPECTROGRAFIA & ONDAS // {label_suffix}"

    # 4. Prioridade Semântica da Sentença: Telescópios, Observatórios, Instrumentos & Óptica
    if re.search(r"(telescópio|observatório|detector|hubble|james webb|instrumento|óptica|espelho|resolução|calibração)", c_text):
        return "blueprint", f"DIAGRAMA INSTRUMENTAL // {label_suffix}"

    # 5. Prioridade Semântica da Sentença: Radar, Varredura & Detecção de Sinais
    if re.search(r"(radar|sonar|varredura|rastreamento|sinal|detecção|varrer|sensor)", c_text):
        return "radar", f"VARREDURA & DETECÇÃO // {label_suffix}"

    # 6. Prioridade Semântica da Sentença: Cronologia, História, Séculos & Evolução no Tempo
    if re.search(r"(anos de história|século|séculos|ao longo de|cronologia|passado|evolução|linha do tempo|décadas|milhões de anos|bilhões de anos)", c_text):
        return "timeline", f"LINHA DO TEMPO & CRONOLOGIA // {label_suffix}"

    # 7. Prioridade Semântica da Sentença: Partículas Subatômicas, Átomos & Mecânica Quântica
    if re.search(r"(partícula|subatôm|átomo|quântic|fóton|elétron|próton|nêutron|bóson|quarks)", c_text):
        return "quantum", f"MECÂNICA QUÂNTICA // {label_suffix}"

    # 8. Prioridade Semântica da Sentença: Biologia Celular, Células, DNA, Medicina & Neurônios
    if re.search(r"(câncer|tumor|carcinoma|oncol|célula|biópsia|dna|genoma|mutação|gene|imunoterap|anticorpo|linfócit|vírus|vacina|biolog|sangue|telômero|senescência|neurônio|sinapse)", c_text):
        return "network", f"BIOLOGIA & CÉLULAS // {label_suffix}"

    # 9. Prioridade Semântica da Sentença: Psicologia, Cognição, Mente, Decisões & Comportamento
    if re.search(r"(psicolog|mente|comportamento|persuas|viés|cogni|emoç|influên|cérebro|percepç|decisão|inconsciente|hábito|atitude)", c_text):
        return "psychology", f"PSICOLOGIA COGNITIVA // {label_suffix}"

    # 10. Prioridade Semântica da Sentença: Política, Poder, Governo & Dinâmica Social
    if re.search(r"(polític|agitador|eleiç|urna|\b(poder executivo|poder judiciário|poder político|luta pelo poder|tomada de poder)\b|propaganda partidária|ideolog|governo|partido político|democrac|polariza|autorit|opinião pública|populis)", c_text):
        return "politics", f"DINÂMICA DE PODER // {label_suffix}"

    # 11. Prioridade Semântica da Sentença: Astrofísica Orbital, Buracos Negros, Quasars & Gravidade
    if re.search(r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos|órbita|gravidade|plasma|estrela de nêutrons|supernova|galáxia|universo)", c_text):
        return "orbital", f"ASTROFÍSICA ORBITAL // {label_suffix}"

    # Se a sentença não tiver termos específicos próprios, recorre ao arquétipo explícito válido
    if explicit_archetype:
        arch = explicit_archetype.lower().strip()
        arch_labels = {
            "grammar": ("grammar", f"NORMA PADRÃO & GRAMÁTICA // {label_suffix}"),
            "lesson": ("lesson", f"VIDEOAULA & FIXAÇÃO // {label_suffix}"),
            "comparison": ("comparison", f"CERTO vs ERRADO // {label_suffix}"),
            "politics": ("politics", f"DINÂMICA DE PODER // {label_suffix}"),
            "psychology": ("psychology", f"PSICOLOGIA COGNITIVA // {label_suffix}"),
            "orbital": ("orbital", f"ASTROFÍSICA ORBITAL // {label_suffix}"),
            "infographic": ("infographic", f"TELEMETRIA & DADOS // {label_suffix}"),
            "blueprint": ("blueprint", f"DIAGRAMA TÉCNICO // {label_suffix}"),
            "spectrum": ("spectrum", f"ESPECTROGRAFIA // {label_suffix}"),
            "network": ("network", f"REDE & SISTEMAS // {label_suffix}"),
            "timeline": ("timeline", f"REGISTRO HISTÓRICO // {label_suffix}"),
            "quantum": ("quantum", f"ESTRUTURA QUÂNTICA // {label_suffix}"),
            "formula": ("formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"),
            "radar": ("radar", f"VARREDURA & DETECÇÃO // {label_suffix}"),
            "analytics": ("analytics", f"DADOS & TENDÊNCIA // {label_suffix}"),
        }
        if arch in arch_labels:
            return arch_labels[arch]

    # Recorre ao tema global combinado (tópico e título do capítulo)
    if re.search(r"(câncer|célula|dna|gene|biolog|medicin|saúde|corpo|vida|envelhecimento|longevidade)", combined_text):
        return "network", f"BIOLOGIA & CÉLULAS // {label_suffix}"
    if re.search(r"(quasar|buraco negro|espaço|astro|galáxia|universo|estrela|cosmo)", combined_text):
        return "orbital", f"ASTROFÍSICA ORBITAL // {label_suffix}"
    if re.search(r"(polític|governo|sociedade|poder|eleiç|líder)", combined_text):
        return "politics", f"DINÂMICA SOCIAL // {label_suffix}"
    if re.search(r"(psicolog|mente|comportamento|cérebro|cogni)", combined_text):
        return "psychology", f"PSICOLOGIA // {label_suffix}"
    if re.search(r"(histór|século|guerra|passado|evolução)", combined_text):
        return "timeline", f"HISTÓRIA & TEMPO // {label_suffix}"

    return "infographic", f"TELEMETRIA & DADOS // {label_suffix}"


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


def generate_thematic_motion_html(theme: str, label: str, content: str = "") -> str:
    """Retorna Motion Design vetorial procedural específico do assunto falado."""
    if theme in ("grammar", "language", "portuguese"):
        is_crase = bool(re.search(r"(crase|acento grave|à|preposição|fusão)", f"{label} {content}".lower()))
        if is_crase:
            eq_html = '''
          <div class="grammar-formula-box">
            <div class="gf-part"><span class="gf-tag">PREPOSIÇÃO</span><span class="gf-word">A</span></div>
            <div class="gf-symbol">+</div>
            <div class="gf-part"><span class="gf-tag">ARTIGO FEMININO</span><span class="gf-word">A</span></div>
            <div class="gf-symbol">=</div>
            <div class="gf-result"><span class="gf-tag">FUSÃO</span><span class="gf-accent">&Agrave;</span></div>
          </div>
          <div class="grammar-cases-row">
            <div class="case-chip chip-correct"><span class="case-icon">✔</span> <span>Vou <b>&agrave;</b> praia (Volto <b>da</b> praia)</span></div>
            <div class="case-chip chip-prohibited"><span class="case-icon">✖</span> <span>Vou <b>a</b> p&eacute; (Palavra masculina)</span></div>
          </div>
          <div class="grammar-mnemonic">
            <span class="mnem-star">💡</span> <b>MACETE DE OURO:</b> "Se vou <i>A</i> e volto <i>DA</i>, crase h&aacute;! Se vou <i>A</i> e volto <i>DE</i>, crase pra qu&ecirc;?"
          </div>'''
        else:
            eq_html = '''
          <div class="grammar-formula-box general">
            <div class="gf-part"><span class="gf-tag">TERMO REGENTE</span><span class="gf-word">EXIGÊNCIA</span></div>
            <div class="gf-symbol">➔</div>
            <div class="gf-part"><span class="gf-tag">TERMO REGIDO</span><span class="gf-word">COMPLEMENTO</span></div>
          </div>
          <div class="grammar-cases-row">
            <div class="case-chip chip-correct"><span class="case-icon">✔</span> <span>Aplicação Correta na Norma Culta</span></div>
            <div class="case-chip chip-prohibited"><span class="case-icon">✖</span> <span>Erro Comum do Cotidiano</span></div>
          </div>
          <div class="grammar-mnemonic">
            <span class="mnem-star">📌</span> <b>REGRA FUNDAMENTAL:</b> Observe a regência do verbo e a classe da palavra seguinte.
          </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-grammar">
          <div class="grammar-hud-header">
            <span class="hud-sub-badge">NORMA PADRÃO & LÍNGUA PORTUGUESA</span>
          </div>
          <div class="grammar-interactive-board">
            {eq_html}
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("lesson", "classroom", "education", "study"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-lesson">
          <div class="lesson-hud-header">
            <span class="hud-sub-badge">VIDEOAULA // CONCEITO E FIXAÇÃO</span>
          </div>
          <div class="lesson-chalkboard">
            <div class="chalk-item item-1">
              <span class="chalk-badge">01</span>
              <div class="chalk-text"><b>ENTENDA A REGRA:</b> Mecanismo e estrutura fundamental</div>
            </div>
            <div class="chalk-item item-2">
              <span class="chalk-badge">02</span>
              <div class="chalk-text"><b>APLICAÇÃO PRÁTICA:</b> Exemplos reais do dia a dia</div>
            </div>
            <div class="chalk-item item-3">
              <span class="chalk-badge">03</span>
              <div class="chalk-text"><b>MACETE DE MEMÓRIA:</b> Atalho mental para não esquecer</div>
            </div>
          </div>
          <div class="lesson-footer-pill">
            <span class="pill-dot"></span> FOCO EM RETENÇÃO & CLAREZA
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("comparison", "contrast", "versus"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-comparison">
          <div class="comp-hud-header">
            <span class="hud-sub-badge">COMPARAÇÃO & APLICAÇÃO PRÁTICA</span>
          </div>
          <div class="comp-cards-container">
            <div class="comp-card card-correct">
              <div class="comp-status-row"><span class="comp-icon">✔</span> <span class="comp-label">CORRETO / PERMITIDO</span></div>
              <div class="comp-desc">Forma consagrada pela norma culta e clareza do contexto</div>
            </div>
            <div class="comp-card card-wrong">
              <div class="comp-status-row"><span class="comp-icon">✖</span> <span class="comp-label">INCORRETO / EVITAR</span></div>
              <div class="comp-desc">Pegadinha frequente em provas, redações e conversas</div>
            </div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("finance", "economy", "money", "market"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-finance">
          <div class="analytics-hud-header">
            <span class="hud-sub-badge">MERCADO, PROBABILIDADE & RISCO</span>
          </div>
          <svg class="analytics-chart-svg" viewBox="0 0 380 180" width="380" height="180">
            <line x1="30" y1="160" x2="360" y2="160" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>
            <line x1="30" y1="20" x2="30" y2="160" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>
            <path d="M 40 130 Q 90 150 140 90 T 240 60 T 350 25" fill="none" stroke="var(--palettePrimary)" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M 40 145 Q 90 160 140 110 T 240 85 T 350 55" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="5 5"/>
            <circle cx="350" cy="25" r="7" fill="var(--palettePrimary)"/>
          </svg>
          <div class="analytics-bars-row">
            <div class="stat-col"><div class="stat-fill f1" style="height: 55%; background: var(--palettePrimary);"></div><span>IBOV</span></div>
            <div class="stat-col"><div class="stat-fill f2" style="height: 82%; background: var(--paletteAccent);"></div><span>USD</span></div>
            <div class="stat-col"><div class="stat-fill f3" style="height: 40%; background: var(--palettePrimary);"></div><span>VOL</span></div>
            <div class="stat-col"><div class="stat-fill f4" style="height: 91%; background: #10b981;"></div><span>META</span></div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("business", "product", "launch"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-business">
          <div class="psych-hud-header">
            <span class="hud-sub-badge">LANÇAMENTO // PRODUTO & IMPACTO</span>
          </div>
          <div class="product-hud-core" style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:1rem; padding:1.5rem 0;">
            <div style="width:110px; height:110px; border-radius:24px; border:2px solid var(--palettePrimary); display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.04); box-shadow:0 0 30px var(--palettePrimary); font-size:2.5rem;">
              ✨
            </div>
            <div class="readout-pill" style="font-weight:700; letter-spacing:0.05em; font-size:0.85rem; padding:0.4rem 1rem; border-radius:9999px; background:rgba(255,255,255,0.08); border:1px solid var(--paletteAccent);">
              CONVERSÃO & VALOR DE MERCADO
            </div>
          </div>
          <div class="hud-label">{label}</div>
        </div>
      </div>'''

    elif theme in ("politics", "social", "power", "opinion"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-politics">
          <div class="polarization-hud">
            <span class="hud-sub-badge">DINÂMICA SOCIAL & OPINIÃO PÚBLICA</span>
            <div class="polarity-spectrum">
              <span class="pol-label left">GRUPO A // 48%</span>
              <div class="pol-bar"><div class="pol-needle"></div></div>
              <span class="pol-label right">GRUPO B // 52%</span>
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
            <div class="readout-pill">AMOSTRAGEM & PESQUISA: <b>REPRESENTATIVA</b></div>
            <div class="readout-pill">MARGEM DE ERRO: <b>±2.0%</b></div>
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
            <span class="readout-unit">MÉTRICA // ÍNDICE</span>
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
          <div class="blueprint-hud-coords">SISTEMA: ATIVO // ANÁLISE ESTRUTURAL</div>
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
            <div class="tl-node n-2"><div class="tl-pulse"></div><span>FASE I</span></div>
            <div class="tl-node n-3"><div class="tl-pulse"></div><span>FASE II</span></div>
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
            <div class="formula-sub-badge">LEI OU EQUAÇÃO FUNDAMENTAL</div>
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
        # Fallback Universal Moderno: Motion Design Geométrico Limpo e Neutro (para qualquer assunto)
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-universal">
          <div class="universal-waves" style="position:relative; width:340px; height:200px; display:flex; align-items:center; justify-content:center;">
            <svg viewBox="0 0 340 180" width="340" height="180">
              <rect x="20" y="20" width="300" height="140" rx="16" fill="rgba(255,255,255,0.03)" stroke="var(--palettePrimary)" stroke-width="1.5" stroke-dasharray="6 6"/>
              <circle cx="170" cy="90" r="45" fill="none" stroke="var(--paletteAccent)" stroke-width="2.5"/>
              <circle cx="170" cy="90" r="22" fill="var(--palettePrimary)" opacity="0.85"/>
              <line x1="60" y1="90" x2="110" y2="90" stroke="var(--paletteAccent)" stroke-width="2"/>
              <line x1="230" y1="90" x2="280" y2="90" stroke="var(--paletteAccent)" stroke-width="2"/>
            </svg>
          </div>
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
        "title": "DESTAQUE // INTRODUÇÃO",
        "subtitle": "PONTO CENTRAL",
        "body": "EXPLICAÇÃO",
        "image": "REGISTRO VISUAL",
        "shape": "CONCEITO",
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
            source_line = f'<div class="clip-sources">FONTES & REFERÊNCIAS  /  {citations}</div>'

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
            media_html = generate_thematic_motion_html(theme_key, theme_label, raw_content)

        role = html.escape(role_labels.get(el.get("type"), "EXPLICAÇÃO"))

        clips_html.append(f'''
    <div id="el-{index}" class="explainer-clip clip"
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