import re

content = open("scripts/build_composition.py", "r", encoding="utf-8").read()

# 1. Update imports
old_imp = '''from scripts.educational_vectors import (
    detect_vestibular_concurso_archetype,
    svg_law_constitution, svg_law_limpe, svg_logic_venn, svg_logic_truth_table,'''

new_imp = '''from scripts.educational_vectors import (
    detect_vestibular_concurso_archetype,
    resolve_topic_domain,
    svg_bio_tissue,
    svg_law_constitution, svg_law_limpe, svg_logic_venn, svg_logic_truth_table,'''

assert old_imp in content, "old_imp not found"
content = content.replace(old_imp, new_imp, 1)

# 2. Add bio_tissue to VESTIBULAR_SVGS in generate_thematic_motion_html
old_vest = '''    VESTIBULAR_SVGS = {
        "law_constitution": ("DIREITO CONSTITUCIONAL // CF/88 & ESTADO DEMOCRÁTICO", svg_law_constitution),'''

new_vest = '''    VESTIBULAR_SVGS = {
        "bio_tissue": ("HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ EXTRACELULAR", svg_bio_tissue),
        "law_constitution": ("DIREITO CONSTITUCIONAL // CF/88 & ESTADO DEMOCRÁTICO", svg_law_constitution),'''

assert old_vest in content, "old_vest not found"
content = content.replace(old_vest, new_vest, 1)

# 3. Add bio_tissue callouts to extract_pedagogical_callouts
old_callouts_top = '''    # 1. BIOGÊNESE, ABIOGÊNESE & ORIGEM DA VIDA
    if theme in ("biogenesis", "biology") or re.search(r"(biogênese|biogenese|abiogênese|abiogenese|geração espontânea|geracao espontanea|origem da vida|pasteur|redi)", combined):'''

new_callouts_top = '''    # 1. HISTOLOGIA & TECIDO CONJUNTIVO
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
    elif theme in ("biogenesis", "biology") or re.search(r"(biogênese|biogenese|abiogênese|abiogenese|geração espontânea|geracao espontanea|origem da vida|pasteur|redi)", combined):'''

assert old_callouts_top in content, "old_callouts_top not found"
content = content.replace(old_callouts_top, new_callouts_top, 1)

# 4. Replace detect_visual_theme with Domain-Locked implementation
detect_start = content.find("def detect_visual_theme(")
assert detect_start != -1, "detect_visual_theme not found"
detect_end = content.find("def _render_callout_cards(", detect_start)
assert detect_end != -1, "_render_callout_cards not found"

new_detect_visual_theme = '''def detect_visual_theme(
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
        if re.search(r"(\bcrase\b|acento grave|regência|regencia|preposição|preposicao|artigo)", c_text):
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
    if re.search(r"(\bmoeda\s+real\b|\bcâmbio\b|\bdólar\b|\binflação\b|\bselic\b|\bibovespa\b|\bbolsa\s+de\s+valores\b|\bações\s+da\s+empresa\b)", c_text):
        return "finance", f"MERCADO & RISCO // {label_suffix}"
    if re.search(r"(\be\s*=\s*mc|\bf\s*=\s*g|\br_s\s*=|lei da grav|incerteza de heisenberg)", c_text):
        return "formula", f"EQUAÇÃO FUNDAMENTAL // {label_suffix}"
    if re.search(r"(\b\d+([.,]\d+)?\s*(%|vezes|km/s|anos-luz)\b|estatística rigorosa)", c_text):
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


'''

content = content[:detect_start] + new_detect_visual_theme + content[detect_end:]

with open("scripts/build_composition.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated scripts/build_composition.py successfully!")

