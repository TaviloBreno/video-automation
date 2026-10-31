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


def clean_speech_text(text: str) -> str:
    """Remove vícios de oralidade e introduções conversacionais."""
    t = re.sub(r"^(mas\s+)?antes de mergulhar nessa aventura[,\s]*", "", text, flags=re.IGNORECASE)
    t = re.sub(r"^(olá\s+(pessoal|a todos)|bem-vindos|fala pessoal)[,\s!]*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^(então|portanto|veja bem|como vimos)[,\s!]*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"[,\s]*(então,?\s*vamos lá!?|vamos lá!?|vem comigo!?)$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_pedagogical_callouts(
    content: str,
    topic: str = "",
    chapter_title: str = "",
    theme: str = "lesson",
) -> dict:
    """Extrai 2 a 3 pontos didáticos e conceituais dinâmicos diretamente da sentença falada pelo professor."""
    cleaned = clean_speech_text(content or "")
    combined = f"{topic} {chapter_title} {content}".lower()
    c_lower = cleaned.lower()

    items = []

    # 1. BIOGÊNESE, ABIOGÊNESE & ORIGEM DA VIDA
    if theme in ("biogenesis", "biology") or re.search(r"(biogênese|biogenese|abiogênese|abiogenese|geração espontânea|geracao espontanea|origem da vida|pasteur|redi)", combined):
        if re.search(r"(o que significa|entender|conceito|fundamental|compreensão|compreensao)", c_lower):
            items.append({
                "num": "01",
                "tag": "CONCEITO-CHAVE",
                "title": "DEFINIÇÃO DE BIOGÊNESE",
                "desc": "Postulado de que todo organismo vivo provém exclusivamente de outro ser vivo preexistente."
            })
            items.append({
                "num": "02",
                "tag": "POSTULADO CENTRAL",
                "title": "PRINCIPIO DA VIDA",
                "desc": "Nenhum organismo celular complexo surge por criação espontânea da matéria inanimada."
            })
            items.append({
                "num": "03",
                "tag": "IMPACTO CIENTÍFICO",
                "title": "BASE DA BIOLOGIA",
                "desc": "Marco que derrubou a teoria da geração espontânea e estruturou a ciência moderna."
            })
        elif re.search(r"(pasteur|pescoço de cisne|caldo|fervura)", c_lower):
            items.append({
                "num": "01",
                "tag": "EXPERIMENTO",
                "title": "FRASCO PESCOÇO DE CISNE",
                "desc": "Gargalo curvado manteve contato com o oxigênio do ar enquanto reteve bactérias na curva."
            })
            items.append({
                "num": "02",
                "tag": "EVIDÊNCIA",
                "title": "ESTERILIDADE PROVADA",
                "desc": "O caldo nutritivo permaneceu estéril até a quebra deliberada do bico de vidro."
            })
            items.append({
                "num": "03",
                "tag": "CONCLUSÃO",
                "title": "REFUTAÇÃO DA ABIOGÊNESE",
                "desc": "Confirmou que micróbios colonizadores vêm do ambiente externo carregados pelo ar."
            })
        elif re.search(r"(redi|carne|frasco|moscas|larvas)", c_lower):
            items.append({
                "num": "01",
                "tag": "MÉTODO DE REDI",
                "title": "TESTE DOS FRASCOS",
                "desc": "Frascos de carne abertos vs frascos protegidos por tela fina de gaze."
            })
            items.append({
                "num": "02",
                "tag": "OBSERVAÇÃO",
                "title": "SURGIMENTO DE LARVAS",
                "desc": "Larvas só eclodiram nos potes onde moscas tiveram acesso para depositar ovos."
            })
            items.append({
                "num": "03",
                "tag": "DEDUÇÃO",
                "title": "REPRODUÇÃO BIOLÓGICA",
                "desc": "A carne em decomposição não cria vida; apenas serve de alimento para larvas."
            })
        else:
            items.append({
                "num": "01",
                "tag": "MECANISMO CELULAR",
                "title": "REPLICAÇÃO DA VIDA",
                "desc": f"{cleaned[:75]}..." if len(cleaned) > 75 else cleaned
            })
            items.append({
                "num": "02",
                "tag": "DIVISÃO CELULAR",
                "title": "CONTINUIDADE GENÉTICA",
                "desc": "Transmissão fiel do material genético e organização molecular das células."
            })
            items.append({
                "num": "03",
                "tag": "SÍNTESE",
                "title": "EVOLUÇÃO & ORIGEM",
                "desc": "Linhagem contínua de seres vivos moldando a biodiversidade biológica."
            })

    # 2. GRAMÁTICA, CRASE & NORMA PADRÃO
    elif theme == "grammar" or re.search(r"(crase|acento grave|regência|regencia|preposição|preposicao|artigo)", combined):
        if re.search(r"(nunca|proib|masculin|verbo)", c_lower):
            items.append({
                "num": "01",
                "tag": "PROIBIÇÃO FORMAL",
                "title": "ANTES DE MASCULINOS & VERBOS",
                "desc": "Palavras masculinas exigem artigo 'o', e verbos não admitem artigo determinativo."
            })
            items.append({
                "num": "02",
                "tag": "PROVA REAL",
                "title": "TESTE DE SUBSTITUIÇÃO",
                "desc": "Substitua por termo masculino: 'Vou a pé' (não admite fusão com 'ao')."
            })
            items.append({
                "num": "03",
                "tag": "REGRA DE OURO",
                "title": "SEM ARTIGO = SEM CRASE",
                "desc": "Se não houver presença simultânea da preposição e do artigo feminino, não use acento grave."
            })
        else:
            items.append({
                "num": "01",
                "tag": "REGRA GERAL",
                "title": "FUSÃO SINTÁTICA",
                "desc": "Preposição 'A' requerida pelo termo regente + Artigo 'A' que acompanha o substantivo feminino."
            })
            items.append({
                "num": "02",
                "tag": "MACETE DE OURO",
                "title": "TESTE DO 'AO'",
                "desc": "Troque a palavra por um substantivo masculino: se virar 'AO', use crase obrigatória!"
            })
            items.append({
                "num": "03",
                "tag": "EXEMPLO PRÁTICO",
                "title": "APLICAÇÃO CORRETA",
                "desc": "Vou à praia (Volto da praia) vs Vou a Roma (Volto de Roma, sem crase)."
            })

    # 3. DIDÁTICA GERAL & FIXAÇÃO UNIVERSAL
    else:
        sentences = [s.strip() for s in re.split(r"[.!?]+", cleaned) if len(s.strip()) > 10]
        if len(sentences) >= 2:
            s1 = sentences[0]
            s2 = sentences[1]
            items.append({
                "num": "01",
                "tag": "CONCEITO-BASE",
                "title": (topic or "FUNDAMENTO").upper(),
                "desc": s1 if len(s1) <= 88 else s1[:85] + "..."
            })
            items.append({
                "num": "02",
                "tag": "DESENVOLVIMENTO",
                "title": "MECANISMO EM AÇÃO",
                "desc": s2 if len(s2) <= 88 else s2[:85] + "..."
            })
            items.append({
                "num": "03",
                "tag": "FIXAÇÃO COGNITIVA",
                "title": "APLICAÇÃO PRÁTICA",
                "desc": "Princípio orientador para interpretação precisa e domínio do assunto."
            })
        else:
            items.append({
                "num": "01",
                "tag": "TESE CENTRAL",
                "title": (topic or "CONCEITO").upper(),
                "desc": cleaned if len(cleaned) <= 85 else cleaned[:82] + "..."
            })
            items.append({
                "num": "02",
                "tag": "ESTRUTURAÇÃO",
                "title": "FUNDAMENTAÇÃO",
                "desc": "Relação lógica e pedagógica entre causas, evidências e resultados."
            })
            items.append({
                "num": "03",
                "tag": "MEMORIZAÇÃO",
                "title": "PONTO-CHAVE",
                "desc": "Atalho conceitual projetado para fixação imediata do conteúdo."
            })

    badge = f"{topic.upper()} // DIDÁTICA & CONCEITO" if topic else "SÍNTESE PEDAGÓGICA // CONCEITO"
    return {"badge": badge, "items": items}


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

    # 1. Biogênese, Abiogênese, Origem da Vida, Pasteur e Redi
    if re.search(r"(\bbiogênese\b|\bbiogenese\b|\babiogênese\b|\babiogenese\b|geração espontânea|geracao espontanea|origem da vida|louis pasteur|\bpasteur\b|francesco redi|\bredi\b|caldo nutritivo|pescoço de cisne|surgimento da vida)", c_text) or re.search(r"(\bbiogênese\b|\bbiogenese\b|\babiogênese\b|\babiogenese\b|geração espontânea|origem da vida|\bpasteur\b|\bredi\b)", combined_text):
        return "biogenesis", f"BIOGÊNESE & ORIGEM DA VIDA // {label_suffix}"

    # 2. Biologia Celular, Mitose, Genética e DNA
    if re.search(r"(célula|celular|mitose|meiose|divisão celular|citoplasma|membrana plasmática|núcleo celular|organela|mitocôndria|dna|genoma|mutação|gene|imunoterap|anticorpo|linfócit|vírus|bactéria|vacina|biolog|sangue|telômero|organismo vivo|evolução)", c_text) or re.search(r"(célula|celular|dna|genoma|biolog|mitose)", combined_text):
        return "biology", f"BIOLOGIA CELULAR // {label_suffix}"

    # 3. Gramática, Língua Portuguesa, Crase, Regras e Ortografia
    if re.search(r"(\bcrase\b|acento grave|regência|regencia|preposição|preposicao|artigo feminino|substantivo|verbo transitivo|concordância|concordancia|ortografia|acentuação|acentuacao|sintaxe|pontuação|pontuacao|oração|oracao|vocábulo|vocabulo|língua portuguesa|lingua portuguesa|gramática|gramatica)", c_text) or re.search(r"(\bcrase\b|gramática|gramatica|língua portuguesa|português|portugues)", combined_text):
        return "grammar", f"NORMA PADRÃO & GRAMÁTICA // {label_suffix}"

    # 4. Certo vs Errado / Comparação Prática
    if re.search(r"(certo ou errado|correto ou incorreto|permitido ou proibido|nunca use|evite usar|forma errada|forma certa|versus|diferença entre|antes de palavra)", c_text):
        return "comparison", f"CERTO vs ERRADO // {label_suffix}"

    # 5. Finanças, Moedas, Dólar, Investimentos, Risco & Mercado
    if re.search(r"(\bdólar|dolar|câmbio|cambio|real|moeda|inflação|inflacao|juros|selic|mercado|bolsa|ações|acoes|ibov|investiment|lucro|preço|preco|volatilidade|risco|probabilidade|chance|ganhar|dinheiro|bilhões|bilhoes|previsão financeira|carteira)", c_text):
        return "finance", f"MERCADO & RISCO // {label_suffix}"

    # 6. Fórmulas Matemáticas e Equações
    if re.search(r"(\be\s*=\s*mc|\bf\s*=\s*g|\br_s\s*=|equação|fórmula|lei da grav|incerteza|constante|c\^2|matemát)", c_text):
        return "formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"

    # 7. Dados Estatísticos e Grandezas
    if re.search(r"(\b\d+([.,]\d+)?\s*(%|vezes|x|km/s|km|anos-luz|graus|k|ºc)\b|porcento|por cento|aumento de|queda de|estatística|gráfico|taxa de|crescimento)", c_text):
        return "analytics", f"DADOS & TENDÊNCIA ESTATÍSTICA // {label_suffix}"

    # 8. Partículas Subatômicas, Átomos & Mecânica Quântica
    if re.search(r"(partícula|subatôm|átomo|quântic|fóton|elétron|próton|nêutron|bóson|quarks)", c_text):
        return "quantum", f"MECÂNICA QUÂNTICA // {label_suffix}"

    # 9. Cronologia, História, Séculos & Evolução no Tempo
    if re.search(r"(anos de história|século|séculos|ao longo de|cronologia|passado|evolução histórica|linha do tempo|décadas|milhões de anos|bilhões de anos)", c_text):
        return "timeline", f"LINHA DO TEMPO & CRONOLOGIA // {label_suffix}"

    # 10. Política, Eleições, Pesquisa de Opinião, Voto & Democracia
    if re.search(r"(eleição|eleicao|eleições|eleicoes|pesquisa de opinião|pesquisa eleitoral|voto|votar|candidato|urna|partido|governo|democracia|congresso|deputado|senador|presidente|rejeição|amostragem|polític|poder executivo|poder judiciário|poder político)", c_text):
        return "politics", f"CENÁRIO ELEITORAL // {label_suffix}"

    # 11. Astrofísica Orbital, Buracos Negros, Quasars & Gravidade
    if re.search(r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos|órbita|gravidade|plasma|estrela de nêutrons|supernova|galáxia|universo)", c_text):
        return "orbital", f"ASTROFÍSICA ORBITAL // {label_suffix}"

    # 12. Psicologia, Cognição, Mente, Decisões & Comportamento
    if re.search(r"(psicolog|mente|comportamento|persuas|viés|cogni|emoç|influên|cérebro|percepç|decisão|inconsciente|hábito|atitude)", c_text):
        return "psychology", f"PSICOLOGIA COGNITIVA // {label_suffix}"

    # 13. Didática Específica, Macetes e Dicas de Fixação (Apenas se a frase for estritamente uma dica)
    if re.search(r"(macete|dica de ouro|mnemônico|mnemonico|como usar|aprenda|passo a passo|não erre|exemplo prático|exemplo pratico|na prática|na pratica|em sala|memorizar|fixar|revisão|revisao)", c_text):
        return "lesson", f"AULA & DICA DE FIXAÇÃO // {label_suffix}"

    # 14. Se a sentença não tiver termos específicos próprios, recorre ao arquétipo explícito válido
    if explicit_archetype:
        arch = explicit_archetype.lower().strip()
        arch_labels = {
            "biogenesis": ("biogenesis", f"BIOGÊNESE // {label_suffix}"),
            "biology": ("biology", f"BIOLOGIA & CÉLULAS // {label_suffix}"),
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
    if re.search(r"(biogênese|biogenese|abiogênese|abiogenese|origem da vida|pasteur|redi)", combined_text):
        return "biogenesis", f"BIOGÊNESE & ORIGEM DA VIDA // {label_suffix}"
    if re.search(r"(câncer|célula|dna|gene|biolog|medicin|saúde|corpo|vida|envelhecimento|longevidade)", combined_text):
        return "biology", f"BIOLOGIA & CÉLULAS // {label_suffix}"
    if re.search(r"(quasar|buraco negro|espaço|astro|galáxia|universo|estrela|cosmo)", combined_text):
        return "orbital", f"ASTROFÍSICA ORBITAL // {label_suffix}"
    if re.search(r"(polític|governo|sociedade|poder|eleiç|líder)", combined_text):
        return "politics", f"DINÂMICA SOCIAL // {label_suffix}"
    if re.search(r"(psicolog|mente|comportamento|cérebro|cogni)", combined_text):
        return "psychology", f"PSICOLOGIA // {label_suffix}"
    if re.search(r"(histór|século|guerra|passado|evolução)", combined_text):
        return "timeline", f"HISTÓRIA & TEMPO // {label_suffix}"

    return "lesson", f"AULA & SÍNTESE // {label_suffix}"


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


def _render_callout_cards(callouts: list[dict], extra_class: str = "") -> str:
    cards = []
    for c in callouts:
        num = html.escape(str(c.get("num", "01")))
        tag = html.escape(str(c.get("tag", "PONTO")))
        title = html.escape(str(c.get("title", "")))
        desc = html.escape(str(c.get("desc", "")))
        cards.append(f'''
            <div class="pedag-item {extra_class}">
              <span class="pedag-badge" data-layout-ignore>{num} {tag}</span>
              <div class="pedag-body">
                <span class="pedag-title">{title}</span>
                <span class="pedag-desc">{desc}</span>
              </div>
            </div>''')
    return "\n".join(cards)


def generate_thematic_motion_html(
    theme: str,
    label: str,
    content: str = "",
    topic: str = "",
    chapter_title: str = "",
) -> str:
    """Retorna Motion Design vetorial procedural específico do assunto falado com ilustrações animadas e textos explicativos reais."""
    pedag_data = extract_pedagogical_callouts(content, topic=topic, chapter_title=chapter_title, theme=theme)
    callout_cards_html = _render_callout_cards(pedag_data["items"])

    # 1. BIOGÊNESE & ORIGEM DA VIDA
    if theme in ("biogenesis", "biology", "origin_of_life", "cell_division"):
        is_biogenesis = "biogênese" in f"{label} {topic} {chapter_title} {content}".lower() or "biogenese" in f"{label} {topic} {chapter_title} {content}".lower()
        badge_text = "BIOGÊNESE & ORIGEM DA VIDA // CIÊNCIA EXPERIMENTAL" if is_biogenesis else "BIOLOGIA CELULAR // ESTRUTURA E VIDA"
        pill_text = "DIVISÃO CELULAR // A VIDA PROVÉM DA VIDA" if is_biogenesis else "DIVISÃO CELULAR // MITOSE & DUPLICAÇÃO"

        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>{badge_text}</span>
          </div>
          <div class="bio-stage-layout">
            <div class="bio-vector-stage">
              <svg class="cell-division-svg" viewBox="0 0 460 170" width="100%" height="170">
                <defs>
                  <radialGradient id="nucGlowLeft" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.9" />
                    <stop offset="60%" stop-color="#0284c7" stop-opacity="0.5" />
                    <stop offset="100%" stop-color="#0369a1" stop-opacity="0" />
                  </radialGradient>
                  <radialGradient id="nucGlowRight" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#a855f7" stop-opacity="0.9" />
                    <stop offset="60%" stop-color="#7c3aed" stop-opacity="0.5" />
                    <stop offset="100%" stop-color="#6d28d9" stop-opacity="0" />
                  </radialGradient>
                  <filter id="bioFilterGlow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>
                <!-- Membrana celular elástica em citocinese -->
                <path class="cell-membrane" d="M 130 20 C 190 20, 195 65, 230 65 C 265 65, 270 20, 330 20 C 390 20, 420 50, 420 85 C 420 120, 390 150, 330 150 C 270 150, 265 105, 230 105 C 195 105, 190 150, 130 150 C 70 150, 40 120, 40 85 C 40 50, 70 20, 130 20 Z"
                      fill="rgba(56, 189, 248, 0.05)" stroke="var(--palettePrimary)" stroke-width="2.5" filter="url(#bioFilterGlow)"/>
                <line class="contractile-ring" x1="230" y1="60" x2="230" y2="110" stroke="var(--paletteAccent)" stroke-width="2.5" stroke-dasharray="3 3"/>
                <!-- Núcleo esquerdo com cromatina -->
                <circle class="cell-nucleus nuc-left" cx="135" cy="85" r="26" fill="url(#nucGlowLeft)"/>
                <circle cx="135" cy="85" r="11" fill="#bae6fd" opacity="0.85"/>
                <path class="chromatin-coil" d="M 128 80 Q 135 76 142 82 T 136 92" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
                <!-- Núcleo direito com cromatina -->
                <circle class="cell-nucleus nuc-right" cx="325" cy="85" r="26" fill="url(#nucGlowRight)"/>
                <circle cx="325" cy="85" r="11" fill="#e9d5ff" opacity="0.85"/>
                <path class="chromatin-coil" d="M 318 80 Q 325 76 332 82 T 326 92" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
                <!-- Organelas e partículas vitais -->
                <ellipse class="bio-organelle o-1" cx="95" cy="55" rx="12" ry="6" transform="rotate(-25 95 55)" fill="rgba(16, 185, 129, 0.6)" stroke="#10b981" stroke-width="1.5"/>
                <ellipse class="bio-organelle o-2" cx="365" cy="115" rx="12" ry="6" transform="rotate(30 365 115)" fill="rgba(16, 185, 129, 0.6)" stroke="#10b981" stroke-width="1.5"/>
                <circle class="bio-particle bp-1" cx="180" cy="45" r="3" fill="var(--paletteAccent)"/>
                <circle class="bio-particle bp-2" cx="105" cy="120" r="2.5" fill="var(--palettePrimary)"/>
                <circle class="bio-particle bp-3" cx="280" cy="45" r="3" fill="var(--paletteAccent)"/>
                <circle class="bio-particle bp-4" cx="355" cy="50" r="2.5" fill="var(--palettePrimary)"/>
              </svg>
              <div class="bio-telemetry-badge" data-layout-ignore>
                <span class="bio-pulse-dot"></span> {pill_text}
              </div>
            </div>
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 2. GRAMÁTICA, LÍNGUA PORTUGUESA & CRASE
    elif theme in ("grammar", "language", "portuguese"):
        is_crase = bool(re.search(r"(crase|acento grave|à|preposição|fusão)", f"{label} {content}".lower()))
        if is_crase:
            eq_html = '''
          <div class="grammar-formula-box">
            <div class="gf-part"><span class="gf-tag" data-layout-ignore>PREPOSIÇÃO</span><span class="gf-word">A</span></div>
            <div class="gf-symbol">+</div>
            <div class="gf-part"><span class="gf-tag" data-layout-ignore>ARTIGO FEMININO</span><span class="gf-word">A</span></div>
            <div class="gf-symbol">=</div>
            <div class="gf-result"><span class="gf-tag" data-layout-ignore>FUSÃO</span><span class="gf-accent">&Agrave;</span></div>
          </div>'''
        else:
            eq_html = '''
          <div class="grammar-formula-box general">
            <div class="gf-part"><span class="gf-tag" data-layout-ignore>TERMO REGENTE</span><span class="gf-word">EXIGÊNCIA</span></div>
            <div class="gf-symbol">➔</div>
            <div class="gf-part"><span class="gf-tag" data-layout-ignore>TERMO REGIDO</span><span class="gf-word">COMPLEMENTO</span></div>
          </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-grammar">
          <div class="grammar-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>NORMA PADRÃO & LÍNGUA PORTUGUESA</span>
          </div>
          <div class="grammar-interactive-board">
            {eq_html}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 3. DIDÁTICA, AULAS & CONCEITOS ESTRUTURADOS
    elif theme in ("lesson", "classroom", "education", "study"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-lesson">
          <div class="lesson-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>VIDEOAULA // CONCEITO E FIXAÇÃO</span>
          </div>
          <div class="didactic-vector-map">
            <svg class="concept-map-svg" viewBox="0 0 460 70" width="100%" height="70">
              <line x1="80" y1="35" x2="230" y2="35" stroke="var(--palettePrimary)" stroke-width="2" stroke-dasharray="4 4" class="concept-wire wire-1"/>
              <line x1="230" y1="35" x2="380" y2="35" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="4 4" class="concept-wire wire-2"/>
              <circle cx="80" cy="35" r="20" fill="rgba(56, 189, 248, 0.2)" stroke="var(--palettePrimary)" stroke-width="2"/>
              <text x="80" y="39" font-size="10" font-weight="800" fill="#ffffff" text-anchor="middle">CONCEITO</text>
              <circle cx="230" cy="35" r="24" fill="rgba(168, 85, 247, 0.25)" stroke="var(--paletteAccent)" stroke-width="2"/>
              <text x="230" y="39" font-size="10" font-weight="800" fill="#ffffff" text-anchor="middle">MECANISMO</text>
              <circle cx="380" cy="35" r="20" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" stroke-width="2"/>
              <text x="380" y="39" font-size="10" font-weight="800" fill="#ffffff" text-anchor="middle">SÍNTESE</text>
            </svg>
          </div>
          <div class="pedagogical-callouts-box">
            {callout_cards_html}
          </div>
          <div class="lesson-footer-pill" data-layout-ignore>
            <span class="pill-dot"></span> FOCO EM RETENÇÃO & CLAREZA PEDAGÓGICA
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 4. COMPARAÇÃO / CERTO vs ERRADO
    elif theme in ("comparison", "contrast", "versus"):
        c_items = pedag_data.get("items", [])
        c_correct = c_items[0]["desc"] if len(c_items) > 0 else "Aplicação consagrada pela norma padrão e clareza do contexto"
        c_wrong = c_items[1]["desc"] if len(c_items) > 1 else "Pegadinha frequente em provas, redações e conversas"
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-comparison">
          <div class="comp-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>COMPARAÇÃO & APLICAÇÃO PRÁTICA</span>
          </div>
          <div class="comp-cards-container">
            <div class="comp-card card-correct">
              <div class="comp-status-row"><span class="comp-icon">✔</span> <span class="comp-label" data-layout-ignore>CORRETO / RECOMENDADO</span></div>
              <div class="comp-desc">{html.escape(c_correct)}</div>
            </div>
            <div class="comp-card card-wrong">
              <div class="comp-status-row"><span class="comp-icon">✖</span> <span class="comp-label" data-layout-ignore>INCORRETO / EVITAR</span></div>
              <div class="comp-desc">{html.escape(c_wrong)}</div>
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 5. FINANÇAS & MERCADO
    elif theme in ("finance", "economy", "money", "market"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-finance">
          <div class="analytics-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>MERCADO, PROBABILIDADE & RISCO</span>
          </div>
          <svg class="analytics-chart-svg" viewBox="0 0 380 160" width="380" height="160">
            <line x1="30" y1="140" x2="360" y2="140" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>
            <line x1="30" y1="20" x2="30" y2="140" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>
            <path d="M 40 120 Q 90 140 140 80 T 240 50 T 350 20" fill="none" stroke="var(--palettePrimary)" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M 40 135 Q 90 150 140 100 T 240 75 T 350 45" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="5 5"/>
            <circle cx="350" cy="20" r="6" fill="var(--palettePrimary)"/>
          </svg>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 6. NEGÓCIOS & PRODUTO
    elif theme in ("business", "product", "launch"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-business">
          <div class="psych-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>LANÇAMENTO // PRODUTO & IMPACTO</span>
          </div>
          <div class="product-hud-core" style="display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0.8rem; padding:1rem 0;">
            <div style="width:90px; height:90px; border-radius:20px; border:2px solid var(--palettePrimary); display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.04); box-shadow:0 0 30px var(--palettePrimary); font-size:2.2rem;">
              ✨
            </div>
            <div class="readout-pill" style="font-weight:700; letter-spacing:0.05em; font-size:0.85rem; padding:0.4rem 1rem; border-radius:9999px; background:rgba(255,255,255,0.08); border:1px solid var(--paletteAccent);">
              CONVERSÃO & VALOR DE MERCADO
            </div>
          </div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 7. POLÍTICA & PODER
    elif theme in ("politics", "social", "power", "opinion"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-politics">
          <div class="polarization-hud">
            <span class="hud-sub-badge" data-layout-ignore>DINÂMICA SOCIAL & OPINIÃO PÚBLICA</span>
            <div class="polarity-spectrum">
              <span class="pol-label left">GRUPO A // 48%</span>
              <div class="pol-bar"><div class="pol-needle"></div></div>
              <span class="pol-label right">GRUPO B // 52%</span>
            </div>
          </div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 8. PSICOLOGIA & COGNIÇÃO
    elif theme in ("psychology", "cognition", "mind", "behavior"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-psychology">
          <div class="psych-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>PROCESSAMENTO COGNITIVO & VIESES</span>
          </div>
          <div class="psych-brain-core">
            <div class="synapse-ring s-outer"></div>
            <div class="synapse-ring s-mid"></div>
            <div class="decision-nucleus"></div>
          </div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 9. ASTROFÍSICA ORBITAL
    elif theme in ("orbital", "astronomy"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-orbital">
          <div class="plasma-jet"></div>
          <div class="accretion-disk disk-outer"></div>
          <div class="accretion-disk disk-inner"></div>
          <div class="event-horizon"></div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 10. INFOGRÁFICO & TELEMETRIA
    elif theme == "infographic":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-infographic">
          <svg class="radial-gauge-svg" viewBox="0 0 360 360" width="280" height="280">
            <circle class="gauge-bg" cx="180" cy="180" r="140" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
            <circle class="gauge-bar" cx="180" cy="180" r="140" fill="none" stroke="var(--palettePrimary)" stroke-width="10" stroke-dasharray="880" stroke-dashoffset="260" stroke-linecap="round"/>
            <circle class="gauge-inner-ring" cx="180" cy="180" r="105" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="6 8"/>
            <text x="180" y="175" text-anchor="middle" fill="#ffffff" font-size="34" font-weight="900" font-family="'JetBrains Mono', monospace">78.4%</text>
            <text x="180" y="205" text-anchor="middle" fill="var(--paletteAccent)" font-size="12" font-weight="700" letter-spacing="3">TELEMETRIA</text>
          </svg>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 11. DIAGRAMA INSTRUMENTAL
    elif theme in ("blueprint", "telescope", "instrument"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-blueprint">
          <div class="reticle-ring ret-outer"></div>
          <div class="reticle-ring ret-mid"></div>
          <div class="reticle-axis-h"></div>
          <div class="reticle-axis-v"></div>
          <div class="reticle-target-box"></div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 12. RADAR & DETECÇÃO
    elif theme in ("radar", "sensor", "scanner"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-radar">
          <div class="radar-circle rc-1"></div>
          <div class="radar-circle rc-2"></div>
          <div class="radar-circle rc-3"></div>
          <div class="radar-sweep"></div>
          <div class="radar-blip blip-1"></div>
          <div class="radar-blip blip-2"></div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 13. ESPECTRO & ONDAS
    elif theme in ("spectrum", "wave"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-spectrum">
          <svg class="sine-waves-svg" viewBox="0 0 420 280" width="420" height="280">
            <path class="sine-wave wave-1" d="M 0 140 Q 35 60 70 140 T 140 140 T 210 140 T 280 140 T 350 140 T 420 140" fill="none" stroke="var(--palettePrimary)" stroke-width="3"/>
            <path class="sine-wave wave-2" d="M 0 140 Q 52.5 210 105 140 T 210 140 T 315 140 T 420 140" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="4 4"/>
          </svg>
          <div class="spectrum-dispersion-bar"></div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 14. REDE & SISTEMAS
    elif theme in ("network", "neural_tech"):
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
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 15. LINHA DO TEMPO & CRONOLOGIA
    elif theme == "timeline":
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-timeline">
          <div class="timeline-axis"></div>
          <div class="timeline-nodes">
            <div class="tl-node n-1"><div class="tl-pulse"></div><span>ORIGEM</span></div>
            <div class="tl-node n-2"><div class="tl-pulse"></div><span>MÉTODO</span></div>
            <div class="tl-node n-3"><div class="tl-pulse"></div><span>PROVA</span></div>
            <div class="tl-node n-4 active"><div class="tl-pulse"></div><span>HOJE</span></div>
          </div>
          <div class="timeline-scanner-beam"></div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 16. MECÂNICA QUÂNTICA & ÁTOMOS
    elif theme in ("quantum", "quantum_physics"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-quantum">
          <div class="quantum-orbit q-1"></div>
          <div class="quantum-orbit q-2"></div>
          <div class="quantum-orbit q-3"></div>
          <div class="quantum-nucleus"></div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 17. FÓRMULA MATEMÁTICA
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
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 18. DADOS & ESTATÍSTICAS
    elif theme in ("analytics", "chart", "data"):
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-analytics">
          <div class="analytics-hud-header">
            <span class="hud-sub-badge" data-layout-ignore>TELEMETRIA DE CRESCIMENTO // ESTATÍSTICA</span>
          </div>
          <div class="analytics-bars-row">
            <div class="stat-col"><div class="stat-fill f1" style="height: 48%; background: var(--palettePrimary);"></div><span>BASE</span></div>
            <div class="stat-col"><div class="stat-fill f2" style="height: 74%; background: var(--paletteAccent);"></div><span>EXP</span></div>
            <div class="stat-col"><div class="stat-fill f3" style="height: 62%; background: var(--palettePrimary);"></div><span>TAXA</span></div>
            <div class="stat-col"><div class="stat-fill f4" style="height: 95%; background: #10b981;"></div><span>PICO</span></div>
          </div>
          <div class="pedagogical-callouts-box compact">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 19. PADRÃO UNIVERSAL
    return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-universal">
          <div class="universal-waves" style="position:relative; width:340px; height:140px; display:flex; align-items:center; justify-content:center;">
            <svg viewBox="0 0 340 140" width="340" height="140">
              <rect x="20" y="15" width="300" height="110" rx="16" fill="rgba(255,255,255,0.03)" stroke="var(--palettePrimary)" stroke-width="1.5" stroke-dasharray="6 6"/>
              <circle cx="170" cy="70" r="38" fill="none" stroke="var(--paletteAccent)" stroke-width="2.5"/>
              <circle cx="170" cy="70" r="18" fill="var(--palettePrimary)" opacity="0.85"/>
              <line x1="60" y1="70" x2="110" y2="70" stroke="var(--paletteAccent)" stroke-width="2"/>
              <line x1="230" y1="70" x2="280" y2="70" stroke="var(--paletteAccent)" stroke-width="2"/>
            </svg>
          </div>
          <div class="pedagogical-callouts-box">
            {callout_cards_html}
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
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

        # Motion Design Procedural Neon Temático e Específico do Assunto Falado
        arch = el.get("visual_archetype") or scene.get("visual_archetype") or ""
        ch_title = scene.get("chapter_title") or ""
        theme_key, theme_label = detect_visual_theme(topic_text, raw_content, ch_title, explicit_archetype=arch)
        motion_html = generate_thematic_motion_html(theme_key, theme_label, raw_content, topic=topic_text, chapter_title=ch_title)

        # Camada Híbrida Inteligente: une Imagem Real/IA com Overlay de Motion Design Explicativo
        image_src = el.get("image_path") or el.get("image_url") or ""
        data_uri = _image_to_data_uri(image_src)

        if data_uri:
            credit = html.escape(str(el.get("image_credit") or "Domínio Público / CC"))
            # Extrai o elemento .motion-design-graphic interior para sobrepor na imagem
            inner_match = re.search(r'(<div class="motion-design-graphic\b[\s\S]*?</div>)\s*</div>\s*$', motion_html.strip())
            motion_inner = inner_match.group(1) if inner_match else motion_html

            media_html = f'''
      <div class="clip-right-media has-image-layer">
        <div class="media-image-frame">
          <img src="{data_uri}" alt="Ilustração">
          <div class="media-backdrop-scrim"></div>
          <div class="image-credit-badge" data-layout-ignore>Fonte: <b>{credit}</b></div>
        </div>
        <div class="media-motion-overlay">
          {motion_inner}
        </div>
      </div>'''
        else:
            media_html = motion_html

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