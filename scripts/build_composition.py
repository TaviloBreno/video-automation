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

from scripts.educational_vectors import (
    detect_vestibular_concurso_archetype,
    resolve_topic_domain,
    svg_bio_tissue,
    svg_law_constitution, svg_law_limpe, svg_logic_venn, svg_logic_truth_table,
    svg_grammar_syntax, svg_redacao_enem, svg_math_cartesian, svg_physics_mechanics,
    svg_physics_circuits, svg_chemistry_organic, svg_chemistry_reaction,
    svg_bio_ecology, svg_bio_neuron, svg_history_brazil, svg_geo_plates
)

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

    # 1. HISTOLOGIA & TECIDO CONJUNTIVO
    if theme == "bio_tissue" or re.search(r"(tecido\s+conjuntivo|colágen|colagen|matriz\s+extracelular|fibroblasto|fibra\s+elástica|sustentação)", combined):
        if re.search(r"(o que é|significa|conceito|fundamental|importante|dúvida|duvida)", c_lower):
            items.append({
                "num": "01",
                "tag": "DEFINIÇÃO HISTOLÓGICA",
                "title": "TECIDO DE SUSTENTAÇÃO",
                "desc": "Tecido mais abundante do corpo que conecta, sustenta e preenche espaços entre órgãos."
            })
            items.append({
                "num": "02",
                "tag": "COMPOSIÇÃO",
                "title": "MATRIZ & FIBROBLASTOS",
                "desc": "Formado por matriz rica em colágeno, fibras elásticas, líquido intersticial e células ativas."
            })
            items.append({
                "num": "03",
                "tag": "IMPORTÂNCIA VITAL",
                "title": "NUTRIÇÃO & PROTEÇÃO",
                "desc": "Amortece impactos, transporta nutrientes por capilares e abriga células do sistema imune."
            })
        elif re.search(r"(função|funcao|estrutura|unir|sustentar|fibras)", c_lower):
            items.append({
                "num": "01",
                "tag": "FUNÇÃO MECÂNICA",
                "title": "COESÃO E SUSTENTAÇÃO",
                "desc": "Suporte estrutural firme para pele, ossos, tendões, cartilagens e músculos."
            })
            items.append({
                "num": "02",
                "tag": "BIOSSÍNTESE",
                "title": "COLÁGENO & ELASTINA",
                "desc": "Proteínas sintetizadas pelos fibroblastos garantindo flexibilidade e resistência à tração."
            })
            items.append({
                "num": "03",
                "tag": "HOMEOSTASE",
                "title": "ABSORÇÃO DE IMPACTO",
                "desc": "Dissipa choques mecânicos e protege órgãos internos vitais contra traumas."
            })
        elif re.search(r"(lesão|lesao|inflamação|inflamacao|cicatriz|defesa|infecção|infeccao)", c_lower):
            items.append({
                "num": "01",
                "tag": "REGENERAÇÃO",
                "title": "RESPOSTA A LESÕES",
                "desc": "Fibroblastos migram e sintetizam novas fibras para regenerar áreas lesionadas."
            })
            items.append({
                "num": "02",
                "tag": "DEFESA IMUNITÁRIA",
                "title": "AÇÃO DE MACRÓFAGOS",
                "desc": "Macrófagos fagocitam bactérias e detritos celulares em casos de infecção."
            })
            items.append({
                "num": "03",
                "tag": "CICATRIZAÇÃO",
                "title": "RESTABELECIMENTO",
                "desc": "Prevenção de hemorragias e reorganização da matriz tecidual para rápida recuperação."
            })
        else:
            items.append({
                "num": "01",
                "tag": "CONCEITO-CHAVE",
                "title": "TECIDO CONJUNTIVO",
                "desc": f"{cleaned[:75]}..." if len(cleaned) > 75 else cleaned
            })
            items.append({
                "num": "02",
                "tag": "ORGANIZAÇÃO",
                "title": "FIBROBLASTOS & MATRIZ",
                "desc": "Células especializadas imersas na substância fundamental amorfa e fibras proteicas."
            })
            items.append({
                "num": "03",
                "tag": "APLICAÇÃO PRÁTICA",
                "title": "FISIOLOGIA HUMANA",
                "desc": "Manutenção da integridade celular e preservação da arquitetura biológica corporal."
            })

    # 2. BIOGÊNESE, ABIOGÊNESE & ORIGEM DA VIDA
    elif theme in ("biogenesis", "biology") or re.search(r"(biogênese|biogenese|abiogênese|abiogenese|geração espontânea|geracao espontanea|origem da vida|pasteur|redi)", combined):
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
    sentence_index: int = 0,
) -> tuple[str, str]:
    """Detecta o campo do conhecimento com isolamento rígido de disciplina para garantir Motion Design condizente."""
    raw_sub = re.sub(r"[^\w\s]", "", chapter_title or topic).strip()
    if len(raw_sub) > 36:
        cutoff = raw_sub[:36].rfind(" ")
        clean_sub = raw_sub[:cutoff].upper() if cutoff > 18 else raw_sub[:36].upper()
    else:
        clean_sub = raw_sub.upper()
    label_suffix = clean_sub if clean_sub else "DADOS & CONCEITO"

    c_text = (content or "").lower()
    combined_domain = f"{topic} {chapter_title}".lower()
    macro_domain = resolve_topic_domain(topic, chapter_title)

    # 1. Se um arquétipo explícito válido for fornecido, honra-o se condizente com a macro-disciplina
    if explicit_archetype:
        arch = explicit_archetype.lower().strip()
        # Blindagem: se o domínio é biológico, bloqueia gráficos matemáticos ou financeiros
        if macro_domain == "BIOLOGY" and arch in ("math_cartesian", "finance", "law_constitution", "law_limpe", "grammar_syntax", "redacao_enem"):
            arch = ""
        elif macro_domain == "GRAMMAR" and arch in ("math_cartesian", "finance", "bio_ecology", "bio_neuron", "bio_tissue"):
            arch = ""
        elif macro_domain == "LAW" and arch in ("math_cartesian", "bio_tissue", "bio_neuron"):
            arch = ""

        if arch:
            arch_labels = {
                "bio_tissue": ("bio_tissue", f"HISTOLOGIA // {label_suffix}"),
                "biogenesis_pasteur": ("biogenesis_pasteur", f"EXPERIMENTO DE PASTEUR // {label_suffix}"),
                "biogenesis_redi": ("biogenesis_redi", f"EXPERIMENTO DE REDI // {label_suffix}"),
                "biogenesis_microscope": ("biogenesis_microscope", f"MICRORGANISMOS // {label_suffix}"),
                "biogenesis_dna": ("biogenesis_dna", f"CÓDIGO GENÉTICO // {label_suffix}"),
                "biogenesis_puzzle": ("biogenesis_puzzle", f"MECANISMO VITAL // {label_suffix}"),
                "biogenesis_versus": ("biogenesis_versus", f"ABIOGÊNESE vs BIOGÊNESE // {label_suffix}"),
                "biogenesis_cell": ("biogenesis_cell", f"DIVISÃO CELULAR // {label_suffix}"),
                "biogenesis": ("biogenesis_cell", f"BIOGÊNESE & VIDA // {label_suffix}"),
                "biology": ("biogenesis_cell", f"BIOLOGIA CELULAR // {label_suffix}"),
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

    # 2. Verificação com Isolamento Rígido de Domínio (Vestibulares, Concursos e Disciplinas)
    edu_arch, edu_label = detect_vestibular_concurso_archetype(content, topic=topic, chapter_title=chapter_title, sentence_index=sentence_index)
    if edu_arch:
        return edu_arch, f"{edu_label} // {label_suffix}"

    # 3. BIOLOGIA & SAÚDE (Totalmente Blindada contra Contaminação)
    if macro_domain == "BIOLOGY":
        if re.search(r"(tecido\s+conjuntivo|colágen|colagen|matriz|fibroblasto|fibra|sustentação|sustentar|tendão|tendões|ligamento|cartilag|adipos|ósseo|absorver\s+choque|lesão|cicatriz|derme)", c_text):
            return "bio_tissue", f"HISTOLOGIA // {label_suffix}"
        if re.search(r"(pasteur|pescoço de cisne|caldo fervido|fervura|esterilização)", c_text):
            return "biogenesis_pasteur", f"EXPERIMENTO DE PASTEUR // {label_suffix}"
        if re.search(r"(redi|francesco|mosca|moscas|larva|larvas|pote|potes|carne)", c_text):
            return "biogenesis_redi", f"EXPERIMENTO DE REDI // {label_suffix}"
        if re.search(r"(microscópio|microscopio|bactéria|bacteria|vírus|virus|micróbio|microrganismo|infecção|infeccao|combater)", c_text):
            return "biogenesis_microscope", f"MICRORGANISMOS & CÉLULAS // {label_suffix}"
        if re.search(r"(dna|genética|genetica|gene|genes|código genético|dupla hélice|replicação)", c_text):
            return "biogenesis_dna", f"CÓDIGO GENÉTICO // {label_suffix}"
        if re.search(r"(célula|celular|mitose|divisão celular|citoplasma|membrana|organela|mitocôndria)", c_text):
            return "biogenesis_cell", f"DIVISÃO CELULAR // {label_suffix}"

        bio_variations = [
            ("bio_tissue", f"HISTOLOGIA // {label_suffix}"),
            ("biogenesis_cell", f"DIVISÃO CELULAR // {label_suffix}"),
            ("biogenesis_microscope", f"MICRORGANISMOS // {label_suffix}"),
            ("bio_tissue", f"MATRIZ & COLÁGENO // {label_suffix}"),
            ("biogenesis_dna", f"CÓDIGO GENÉTICO // {label_suffix}"),
            ("bio_neuron", f"FISIOLOGIA TECIDUAL // {label_suffix}"),
        ]
        return bio_variations[sentence_index % len(bio_variations)]

    # 4. GRAMÁTICA, LÍNGUA PORTUGUESA & CRASE
    if macro_domain == "GRAMMAR":
        if re.search(r"(crase|acento grave|regência|regencia|preposição|preposicao|artigo)", c_text):
            return "grammar", f"NORMA PADRÃO & GRAMÁTICA // {label_suffix}"
        if re.search(r"(certo ou errado|correto ou incorreto|nunca use|evite)", c_text):
            return "comparison", f"CERTO vs ERRADO // {label_suffix}"
        return "grammar", f"LÍNGUA PORTUGUESA // {label_suffix}"

    # 5. DIREITO & ADMINISTRAÇÃO PÚBLICA
    if macro_domain == "LAW":
        if re.search(r"(constituição|cf/88|artigo 5|direitos fundamentais)", c_text):
            return "law_constitution", f"DIREITO CONSTITUCIONAL // {label_suffix}"
        if re.search(r"(administrativo|limpe|legalidade|servidor)", c_text):
            return "law_limpe", f"DIREITO ADMINISTRATIVO // {label_suffix}"
        return "law_constitution", f"DIREITO PÚBLICO // {label_suffix}"

    # 6. FÍSICA
    if macro_domain == "PHYSICS":
        if re.search(r"(newton|dinâmica|força|atrito|gravidade)", c_text):
            return "physics_mechanics", f"FÍSICA MECÂNICA // {label_suffix}"
        if re.search(r"(circuito|resistor|ohm|voltagem|corrente)", c_text):
            return "physics_circuits", f"ELETRODINÂMICA // {label_suffix}"
        return "formula", f"FÍSICA FUNDAMENTAL // {label_suffix}"

    # 7. QUÍMICA
    if macro_domain == "CHEMISTRY":
        if re.search(r"(orgânica|benzeno|anel|carbono|hidrocarboneto)", c_text):
            return "chemistry_organic", f"QUÍMICA ORGÂNICA // {label_suffix}"
        if re.search(r"(ph|ácido|base|reação|entalpia)", c_text):
            return "chemistry_reaction", f"FÍSICO-QUÍMICA // {label_suffix}"
        return "chemistry_reaction", f"QUÍMICA GERAL // {label_suffix}"

    # 8. MATEMÁTICA
    if macro_domain == "MATH":
        if re.search(r"(função|funcao|parábola|cartesiano|vértice)", c_text):
            return "math_cartesian", f"MATEMÁTICA // {label_suffix}"
        if re.search(r"(conjuntos|venn)", c_text):
            return "logic_venn", f"RACIOCÍNIO LÓGICO // {label_suffix}"
        return "analytics", f"MATEMÁTICA // {label_suffix}"

    # 9. Fallbacks gerais para temas abertos / gerais
    if re.search(r"(moeda\s+real|câmbio|dólar|inflação|selic|ibovespa|bolsa\s+de\s+valores|ações\s+da\s+empresa)", c_text):
        return "finance", f"MERCADO & RISCO // {label_suffix}"
    if re.search(r"(e\s*=\s*mc|f\s*=\s*g|r_s\s*=|lei da grav|incerteza de heisenberg)", c_text):
        return "formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"
    if re.search(r"(\d+([.,]\d+)?\s*(%|vezes|km/s|anos-luz)|estatística rigorosa)", c_text):
        return "analytics", f"DADOS ESTATÍSTICOS // {label_suffix}"
    if re.search(r"(partícula subatômica|bóson|quarks|fóton|mecânica quântica)", c_text):
        return "quantum", f"MECÂNICA QUÂNTICA // {label_suffix}"
    if re.search(r"(século\s+[xvi]+|evolução histórica ao longo dos séculos|linha do tempo histórica)", c_text):
        return "timeline", f"LINHA DO TEMPO // {label_suffix}"
    if re.search(r"(eleição presidencial|partido político|poder executivo e judiciário)", c_text):
        return "politics", f"CENÁRIO INSTITUCIONAL // {label_suffix}"
    if re.search(r"(buraco negro|singularidade|horizonte de eventos|quasar|galáxia)", c_text):
        return "orbital", f"ASTROFÍSICA // {label_suffix}"
    if re.search(r"(viés cognitivo|psicologia cognitiva|psicanálise freudiana)", c_text):
        return "psychology", f"PSICOLOGIA // {label_suffix}"

    return "lesson", f"AULA & SÍNTESE // {label_suffix}"


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

    VESTIBULAR_SVGS = {
        "bio_tissue": ("HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ EXTRACELULAR", svg_bio_tissue),
        "law_constitution": ("DIREITO CONSTITUCIONAL // CF/88 & ESTADO DEMOCRÁTICO", svg_law_constitution),
        "law_limpe": ("DIREITO ADMINISTRATIVO // PRINCÍPIOS L.I.M.P.E.", svg_law_limpe),
        "logic_venn": ("RACIOCÍNIO LÓGICO // DIAGRAMAS DE VENN & CONJUNTOS", svg_logic_venn),
        "logic_truth_table": ("LÓGICA PROPOSICIONAL // TABELA-VERDADE", svg_logic_truth_table),
        "grammar_syntax": ("NORMA CULTA // ANÁLISE SINTÁTICA DA ORAÇÃO", svg_grammar_syntax),
        "redacao_enem": ("REDAÇÃO NOTA 1000 // COMPETÊNCIAS ENEM", svg_redacao_enem),
        "math_cartesian": ("MATEMÁTICA // FUNÇÕES & GRÁFICO CARTESIANO", svg_math_cartesian),
        "physics_mechanics": ("FÍSICA MECÂNICA // DINÂMICA & LEIS DE NEWTON", svg_physics_mechanics),
        "physics_circuits": ("ELETRODINÂMICA // CIRCUITO & 1ª LEI DE OHM", svg_physics_circuits),
        "chemistry_organic": ("QUÍMICA ORGÂNICA // CADEIAS & RESSONÂNCIA", svg_chemistry_organic),
        "chemistry_reaction": ("FÍSICO-QUÍMICA // pH & CINÉTICA", svg_chemistry_reaction),
        "bio_ecology": ("ECOLOGIA // PIRÂMIDE TRÓFICA & ENERGIA", svg_bio_ecology),
        "bio_neuron": ("FISIOLOGIA HUMANA // NEURÔNIO & SINAPSE", svg_bio_neuron),
        "history_brazil": ("HISTORIOGRAFIA // CRONOLOGIA & MARCOS", svg_history_brazil),
        "geo_plates": ("GEOGRAFIA FÍSICA // TECTÔNICA & RELEVO", svg_geo_plates),
    }

    if theme in VESTIBULAR_SVGS:
        badge_title, svg_fn = VESTIBULAR_SVGS[theme]
        stage_svg = svg_fn()
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-vestibular">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>{badge_title}</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.1 BIOGÊNESE // FRASCO PESCOÇO DE CISNE DE PASTEUR
    if theme == "biogenesis_pasteur":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="pasteur-flask-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <linearGradient id="brothGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#b45309" stop-opacity="0.95"/>
          </linearGradient>
          <filter id="flaskGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>
        <!-- Suporte do frasco / Tripé -->
        <line x1="160" y1="155" x2="260" y2="155" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
        <line x1="210" y1="145" x2="210" y2="155" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
        <!-- Corpo esférico do Frasco de Pasteur -->
        <circle cx="210" cy="115" r="32" fill="rgba(56, 189, 248, 0.06)" stroke="var(--palettePrimary)" stroke-width="2.5" filter="url(#flaskGlow)"/>
        <!-- Caldo nutritivo fervido estéril -->
        <path d="M 182 125 Q 210 135 238 125 A 32 32 0 0 1 182 125 Z" fill="url(#brothGrad)"/>
        <!-- Bolhas de fervura subindo -->
        <circle class="pasteur-bubble b1" cx="205" cy="122" r="2.5" fill="#fef08a"/>
        <circle class="pasteur-bubble b2" cx="218" cy="118" r="3" fill="#fef08a"/>
        <circle class="pasteur-bubble b3" cx="210" cy="128" r="2" fill="#fef08a"/>
        <!-- Gargalo curvado em Pescoço de Cisne (Curva em S alongada) -->
        <path class="swan-neck-path" d="M 210 83 L 210 55 C 210 25, 270 25, 270 55 C 270 85, 330 95, 345 65"
              fill="none" stroke="var(--palettePrimary)" stroke-width="3" stroke-linecap="round"/>
        <path d="M 210 83 L 210 55 C 210 25, 270 25, 270 55 C 270 85, 330 95, 345 65"
              fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.2" stroke-linecap="round"/>
        <!-- Microrganismos e poeira retidos na curva inferior do gargalo -->
        <circle class="trapped-dust d1" cx="270" cy="55" r="3" fill="#ef4444"/>
        <circle class="trapped-dust d2" cx="275" cy="60" r="2.5" fill="#f97316"/>
        <circle class="trapped-dust d3" cx="265" cy="58" r="2.5" fill="#ef4444"/>
        <line x1="285" y1="45" x2="310" y2="35" stroke="var(--paletteAccent)" stroke-width="1.5" stroke-dasharray="2 2"/>
        <text x="315" y="38" fill="var(--paletteAccent)" font-size="10" font-weight="700">POEIRA & GERMES RETIDOS</text>
        <!-- Ar puro entrando livremente -->
        <path class="air-flow-arrow" d="M 370 65 L 350 65" stroke="#10b981" stroke-width="2" stroke-linecap="round" marker-end="url(#arrow)"/>
        <text x="375" y="68" fill="#10b981" font-size="9" font-weight="700">AR PURO</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> EXPERIMENTO DE PASTEUR // FRASCO PESCOÇO DE CISNE
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>EXPERIMENTO DE PASTEUR // CALDO NUTRITIVO</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.2 BIOGÊNESE // EXPERIMENTO DE FRANCESCO REDI
    elif theme == "biogenesis_redi":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="redi-jars-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <filter id="rediGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>
        <!-- Pote 1 (Aberto - Moscas entram e geram larvas) -->
        <rect x="90" y="50" width="80" height="90" rx="8" fill="rgba(239, 68, 68, 0.05)" stroke="#ef4444" stroke-width="2"/>
        <ellipse cx="130" cy="50" rx="40" ry="10" fill="none" stroke="#ef4444" stroke-width="2"/>
        <rect x="105" y="110" width="50" height="22" rx="4" fill="#7f1d1d" opacity="0.8"/>
        <!-- Moscas no Pote Aberto -->
        <circle class="redi-fly f1" cx="120" cy="35" r="3.5" fill="#fca5a5"/>
        <circle class="redi-fly f2" cx="140" cy="40" r="3" fill="#fca5a5"/>
        <circle class="redi-fly f3" cx="130" cy="85" r="2.5" fill="#f87171"/>
        <text x="130" y="158" fill="#ef4444" font-size="10" font-weight="800" text-anchor="middle">POTE ABERTO: LARVAS</text>

        <!-- Divisor Central -->
        <line x1="230" y1="35" x2="230" y2="150" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-dasharray="4 4"/>

        <!-- Pote 2 (Vedado com Gaze - Moscas bloqueadas) -->
        <rect x="290" y="50" width="80" height="90" rx="8" fill="rgba(16, 185, 129, 0.05)" stroke="#10b981" stroke-width="2"/>
        <!-- Rede de gaze protetora -->
        <ellipse cx="330" cy="50" rx="40" ry="10" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" stroke-width="2"/>
        <line x1="295" y1="50" x2="365" y2="50" stroke="#10b981" stroke-width="1.5" stroke-dasharray="2 2"/>
        <rect x="305" y="110" width="50" height="22" rx="4" fill="#064e3b" opacity="0.8"/>
        <!-- Moscas bloqueadas do lado de fora -->
        <circle class="redi-fly f4" cx="320" cy="28" r="3.5" fill="#6ee7b7"/>
        <circle class="redi-fly f5" cx="345" cy="32" r="3" fill="#6ee7b7"/>
        <!-- Escudo de Bloqueio -->
        <path d="M 326 42 L 334 42 L 334 48 L 330 52 L 326 48 Z" fill="#10b981"/>
        <text x="330" y="158" fill="#10b981" font-size="10" font-weight="800" text-anchor="middle">COM GAZE: SEM LARVAS</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> EXPERIMENTO DE REDI // BLOQUEIO BIOLÓGICO
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>EXPERIMENTO DE REDI // TESTE DOS FRASCOS</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.3 BIOGÊNESE // MICRORGANISMOS & CAMPO DO MICROSCÓPIO
    elif theme == "biogenesis_microscope":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="microscope-viewport-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <radialGradient id="microGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#0284c7" stop-opacity="0.25"/>
            <stop offset="80%" stop-color="#0369a1" stop-opacity="0.05"/>
            <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
          </radialGradient>
        </defs>
        <!-- Lente do Microscópio (Campo Visual Circular) -->
        <circle cx="230" cy="85" r="68" fill="url(#microGlow)" stroke="var(--palettePrimary)" stroke-width="3"/>
        <circle cx="230" cy="85" r="62" fill="none" stroke="var(--paletteAccent)" stroke-width="1" stroke-dasharray="4 6"/>
        <!-- Retículo Óptico / Mira de Medição -->
        <line x1="230" y1="20" x2="230" y2="150" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <line x1="165" y1="85" x2="295" y2="85" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <!-- Bactérias Bacilos nadando -->
        <rect class="bacteria-cell b-bacillus-1" x="200" y="60" width="22" height="9" rx="4.5" transform="rotate(25 211 64)" fill="#38bdf8" stroke="#bae6fd" stroke-width="1.5"/>
        <rect class="bacteria-cell b-bacillus-2" x="240" y="95" width="26" height="10" rx="5" transform="rotate(-35 253 100)" fill="#a855f7" stroke="#e9d5ff" stroke-width="1.5"/>
        <!-- Bactérias Cocos (esféricas) -->
        <circle class="bacteria-cell b-coccus-1" cx="195" cy="105" r="6" fill="#10b981" stroke="#a7f3d0" stroke-width="1.5"/>
        <circle class="bacteria-cell b-coccus-2" cx="260" cy="65" r="5" fill="#f59e0b" stroke="#fef3c7" stroke-width="1.5"/>
        <circle class="bacteria-cell b-coccus-3" cx="225" cy="80" r="4" fill="#38bdf8" stroke="#bae6fd" stroke-width="1.5"/>
        <!-- Telemetria óptica lateral -->
        <text x="315" y="75" fill="var(--paletteAccent)" font-size="11" font-weight="800">1000x ZOOM</text>
        <text x="315" y="92" fill="#94a3b8" font-size="9" font-weight="600">CAMPO ÓPTICO</text>
        <text x="315" y="105" fill="#10b981" font-size="9" font-weight="700">● VIDA ATIVA</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> OBSERVAÇÃO MICROSCÓPICA // BACTÉRIAS E MICRÓBIOS
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>CAMPO MICROSCÓPICO // MICRÓBIOS & BACTÉRIAS</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.4 BIOGÊNESE // DUPLA HÉLICE DE DNA
    elif theme == "biogenesis_dna":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="dna-helix-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <linearGradient id="dnaGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#38bdf8"/>
            <stop offset="100%" stop-color="#818cf8"/>
          </linearGradient>
          <linearGradient id="dnaGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#a855f7"/>
            <stop offset="100%" stop-color="#ec4899"/>
          </linearGradient>
        </defs>
        <!-- Fitas senoidais da dupla hélice -->
        <path class="dna-strand s1" d="M 60 85 Q 110 35 160 85 T 260 85 T 360 85 T 420 85" fill="none" stroke="url(#dnaGrad1)" stroke-width="3" stroke-linecap="round"/>
        <path class="dna-strand s2" d="M 60 85 Q 110 135 160 85 T 260 85 T 360 85 T 420 85" fill="none" stroke="url(#dnaGrad2)" stroke-width="3" stroke-linecap="round"/>
        <!-- Pontes de hidrogênio (pares de bases) -->
        <line class="dna-rung r1" x1="110" y1="48" x2="110" y2="122" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="3 3"/>
        <line class="dna-rung r2" x1="160" y1="85" x2="160" y2="85" stroke="#ffffff" stroke-width="3"/>
        <line class="dna-rung r3" x1="210" y1="48" x2="210" y2="122" stroke="var(--palettePrimary)" stroke-width="2" stroke-dasharray="3 3"/>
        <line class="dna-rung r4" x1="260" y1="85" x2="260" y2="85" stroke="#ffffff" stroke-width="3"/>
        <line class="dna-rung r5" x1="310" y1="48" x2="310" y2="122" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="3 3"/>
        <line class="dna-rung r6" x1="360" y1="85" x2="360" y2="85" stroke="#ffffff" stroke-width="3"/>
        <!-- Nós de replicação com brilho -->
        <circle class="dna-node" cx="110" cy="48" r="5" fill="#38bdf8"/>
        <circle class="dna-node" cx="110" cy="122" r="5" fill="#ec4899"/>
        <circle class="dna-node" cx="210" cy="48" r="5" fill="#a855f7"/>
        <circle class="dna-node" cx="210" cy="122" r="5" fill="#38bdf8"/>
        <circle class="dna-node" cx="310" cy="48" r="5" fill="#818cf8"/>
        <circle class="dna-node" cx="310" cy="122" r="5" fill="#ec4899"/>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> DUPLA HÉLICE DE DNA // CÓDIGO & REPLICAÇÃO
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>CÓDIGO GENÉTICO // DUPLA HÉLICE & REPLICAÇÃO</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.5 BIOGÊNESE // MECANISMO INTEGRADO / PUZZLE MOLECULAR
    elif theme == "biogenesis_puzzle":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="bio-puzzle-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Engrenagens moleculares / Sistema integrado -->
        <g class="gear-wheel g1" transform="translate(180, 85)">
          <circle cx="0" cy="0" r="32" fill="none" stroke="var(--palettePrimary)" stroke-width="2.5" stroke-dasharray="6 4"/>
          <circle cx="0" cy="0" r="14" fill="rgba(56, 189, 248, 0.2)" stroke="var(--palettePrimary)" stroke-width="2"/>
          <line x1="-32" y1="0" x2="32" y2="0" stroke="var(--palettePrimary)" stroke-width="2"/>
          <line x1="0" y1="-32" x2="0" y2="32" stroke="var(--palettePrimary)" stroke-width="2"/>
        </g>
        <g class="gear-wheel g2" transform="translate(250, 85)">
          <circle cx="0" cy="0" r="28" fill="none" stroke="var(--paletteAccent)" stroke-width="2.5" stroke-dasharray="5 3"/>
          <circle cx="0" cy="0" r="12" fill="rgba(168, 85, 247, 0.2)" stroke="var(--paletteAccent)" stroke-width="2"/>
          <line x1="-28" y1="0" x2="28" y2="0" stroke="var(--paletteAccent)" stroke-width="2"/>
          <line x1="0" y1="-28" x2="0" y2="28" stroke="var(--paletteAccent)" stroke-width="2"/>
        </g>
        <!-- Conexões moleculares tipo puzzle -->
        <path d="M 100 85 L 148 85 M 278 85 L 340 85" stroke="rgba(255,255,255,0.3)" stroke-width="2" stroke-dasharray="4 4"/>
        <circle cx="100" cy="85" r="8" fill="#10b981"/>
        <circle cx="340" cy="85" r="8" fill="#f59e0b"/>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> MECANISMO INTEGRADO // SISTEMA VITAL
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>SISTEMA VITAL // ENGRENAGENS MOLECULARES</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.6 BIOGÊNESE // CONFRONTO HISTÓRICO: ABIOGÊNESE vs BIOGÊNESE
    elif theme == "biogenesis_versus":
        stage_svg = '''
    <div class="bio-vector-stage">
      <svg class="bio-versus-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Lado Esquerdo: Abiogênese (Refutado) -->
        <rect x="60" y="30" width="140" height="110" rx="14" fill="rgba(239, 68, 68, 0.06)" stroke="#ef4444" stroke-width="1.8"/>
        <circle cx="130" cy="65" r="18" fill="rgba(239, 68, 68, 0.2)" stroke="#ef4444" stroke-width="2"/>
        <text x="130" y="72" fill="#ef4444" font-size="18" font-weight="900" text-anchor="middle">✖</text>
        <text x="130" y="105" fill="#fca5a5" font-size="11" font-weight="800" text-anchor="middle">ABIOGÊNESE</text>
        <text x="130" y="122" fill="#94a3b8" font-size="9" text-anchor="middle">Geração do nada (FALSO)</text>

        <!-- Divisor Central VS -->
        <circle cx="230" cy="85" r="18" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.3)" stroke-width="1.5"/>
        <text x="230" y="90" fill="#ffffff" font-size="11" font-weight="900" text-anchor="middle">VS</text>

        <!-- Lado Direito: Biogênese (Comprovado) -->
        <rect x="260" y="30" width="140" height="110" rx="14" fill="rgba(16, 185, 129, 0.06)" stroke="#10b981" stroke-width="1.8"/>
        <circle cx="330" cy="65" r="18" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" stroke-width="2"/>
        <text x="330" y="72" fill="#10b981" font-size="18" font-weight="900" text-anchor="middle">✔</text>
        <text x="330" y="105" fill="#86efac" font-size="11" font-weight="800" text-anchor="middle">BIOGÊNESE</text>
        <text x="330" y="122" fill="#94a3b8" font-size="9" text-anchor="middle">Vida gera vida (REAL)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> CONFRONTO HISTÓRICO // ABIOGÊNESE vs BIOGÊNESE
      </div>
    </div>'''
        return f'''
      <div class="clip-right-media">
        <div class="motion-design-graphic motion-biogenesis">
          <div class="bio-header-badge">
            <span class="hud-sub-badge" data-layout-ignore>RUPTURA CIENTÍFICA // ABIOGÊNESE vs BIOGÊNESE</span>
          </div>
          <div class="bio-stage-layout">
            {stage_svg}
            <div class="pedagogical-callouts-box">
              {callout_cards_html}
            </div>
          </div>
          <div class="hud-label" data-layout-ignore>{label}</div>
        </div>
      </div>'''

    # 1.7 BIOGÊNESE // CITOCINESE & DIVISÃO CELULAR (PADRÃO MITOSE)
    elif theme in ("biogenesis_cell", "biogenesis", "biology", "origin_of_life", "cell_division"):
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
                <path class="cell-membrane" d="M 130 20 C 190 20, 195 65, 230 65 C 265 65, 270 20, 330 20 C 390 20, 420 50, 420 85 C 420 120, 390 150, 330 150 C 270 150, 265 105, 230 105 C 195 105, 190 150, 130 150 C 70 150, 40 120, 40 85 C 40 50, 70 20, 130 20 Z"
                      fill="rgba(56, 189, 248, 0.05)" stroke="var(--palettePrimary)" stroke-width="2.5" filter="url(#bioFilterGlow)"/>
                <line class="contractile-ring" x1="230" y1="60" x2="230" y2="110" stroke="var(--paletteAccent)" stroke-width="2.5" stroke-dasharray="3 3"/>
                <circle class="cell-nucleus nuc-left" cx="135" cy="85" r="26" fill="url(#nucGlowLeft)"/>
                <circle cx="135" cy="85" r="11" fill="#bae6fd" opacity="0.85"/>
                <path class="chromatin-coil" d="M 128 80 Q 135 76 142 82 T 136 92" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
                <circle class="cell-nucleus nuc-right" cx="325" cy="85" r="26" fill="url(#nucGlowRight)"/>
                <circle cx="325" cy="85" r="11" fill="#e9d5ff" opacity="0.85"/>
                <path class="chromatin-coil" d="M 318 80 Q 325 76 332 82 T 326 92" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>
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
        theme_key, theme_label = detect_visual_theme(topic_text, raw_content, ch_title, explicit_archetype=arch, sentence_index=index - 1)
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