import re

def resolve_topic_domain(topic: str, chapter_title: str = "") -> str:
    text = f"{topic} {chapter_title}".lower()
    if re.search(r"(\bbiolog|célula|celular|tecido|histolog|conjuntiv|epitelial|ósseo|osseo|cartilag|muscular|sanguíneo|sanguineo|linfático|linfatico|adipos|fibroblasto|colágen|colagen|biogênese|biogenese|abiogênese|abiogenese|origem da vida|pasteur|redi|dna|genética|genetica|genoma|mitocôndria|mitocondria|mitose|meiose|organela|ecologia|trófic|trofic|cadeia alimentar|fotossíntese|fotossintese|respiração celular|respiracao celular|neurônio|neuronio|sinapse|sistema nervoso|imunologia|anticorpo|vacina|vírus|virus|bactéria|bacteria|evolução|darwin|seleção natural|anatomia|fisiologia)\b", text):
        return "BIOLOGY"
    if re.search(r"(\bcrase\b|acento grave|regência|regencia|concordância|concordancia|preposição|preposicao|artigo|substantivo|adjetivo|pronome|verbo|análise sintática|analise sintatica|sujeito|predicado|oração|oracao|período composto|pontuação|pontuacao|ortografia|acentuação|acentuacao|redação|redacao|dissertativo|enem nota 1000|língua portuguesa|lingua portuguesa|português|portugues)\b", text):
        return "GRAMMAR"
    if re.search(r"(\bdireito\b|constitucional|cf/88|artigo 5|direitos fundamentais|remédios constitucionais|habeas corpus|mandado de segurança|três poderes|judiciário|judiciario|legislativo|executivo|stf|stj|administrativo|limpe|legalidade|impessoalidade|moralidade|publicidade|eficiência|servidor público|ato administrativo|concurso público|concurso publico|licitação|licitacao|processo administrativo|penal|crime|pena|código civil|processo civil)\b", text):
        return "LAW"
    if re.search(r"(\bfísica\b|\bfisica\b|newton|leis de newton|plano inclinado|cinemática|cinematica|velocidade|aceleração|aceleracao|dinâmica|dinamica|gravitação|gravitacao|termodinâmica|termodinamica|calor|óptica|optica|espelho|lente|ondulatória|ondulatoria|frequência|comprimento de onda|eletricidade|circuito|resistor|ohm|voltagem|ampere|corrente elétrica|corrente eletrica|eletromagnetismo|indução|campo elétrico|campo magnético|mecânica quântica|mecanica quantica)\b", text):
        return "PHYSICS"
    if re.search(r"(\bquímica\b|\bquimica\b|tabela periódica|tabela periodica|ligação química|ligacao quimica|ligação covalente|ligação iônica|estequiometria|mol|massa molar|química orgânica|quimica organica|hidrocarboneto|benzeno|função orgânica|isomeria|álcool|termoquímica|entalpia|cinética química|ph|ácido|base|titulação|soluções|eletroquímica|pilha|eletrólise)\b", text):
        return "CHEMISTRY"
    if re.search(r"(\bmatemática\b|\bmatematica\b|função afim|função quadrática|parábola|bhaskara|vértice|geometria|trigonometria|seno|cosseno|tangente|matriz|determinante|probabilidade|análise combinatória|analise combinatoria|estatística|estatistica|média|mediana|moda|desvio padrão|raciocínio lógico|rlm|diagrama de venn|tabela-verdade|proposição|lógica proposicional)\b", text):
        return "MATH"
    return "GENERAL"

test_sentences = [
    ("Introdução ao Tecido Conjuntivo", "Você já teve alguma dúvida sobre o que é tecido conjuntivo? Muitas pessoas estão confusas sobre essa questão fundamental."),
    ("Introdução ao Tecido Conjuntivo", "Mas hoje vamos esclarecer isso de uma forma simples e prática."),
    ("Introdução ao Tecido Conjuntivo", "O tecido conjuntivo, também conhecido como colágeno, é um dos tipos mais importantes de tecidos no nosso corpo."),
    ("Introdução ao Tecido Conjuntivo", "Ele desempenha um papel crucial na manutenção da estrutura e função das nossas células, ossos, pele e outros tecidos."),
    ("Estrutura e Função do Tecido Conjuntivo", "O tecido conjuntivo é um dos três principais tipos de tecidos que compõem o nosso corpo."),
    ("Estrutura e Função do Tecido Conjuntivo", "É responsável por unir e sustentar as células, ossos, pele e outros tecidos. Vamos entender melhor sua estrutura e função."),
    ("Estrutura e Função do Tecido Conjuntivo", "O tecido conjuntivo é formado por colágeno, uma proteína que liga as células e os fibrões entre si, além de gordura e água."),
    ("Estrutura e Função do Tecido Conjuntivo", "Ele ajuda a manter a estrutura e a forma do nosso corpo, como a pele, ossos e tendões."),
    ("Estrutura e Função do Tecido Conjuntivo", "Além disso, o tecido conjuntivo é responsável por absorver choques físicos e químicos, protegendo os órgãos internos do nosso corpo."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "E agora que sabemos o que é tecido conjuntivo e como funciona, vamos aplicar esses conhecimentos em situações reais."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "Lembre-se de que o tecido conjuntivo é responsável por absorver choques físicos e químicos, protegendo os órgãos internos do nosso corpo."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "Por exemplo, se você sofrer uma lesão, o tecido conjuntivo ajuda a prevenir hemorragias e inflamação, permitindo que o corpo recupere mais rapidamente."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "Além disso, em casos de infecções, o tecido conjuntivo produz células que ajudam a combatê-las."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "É fundamental entender essa função para tomar medidas preventivas adequadas."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "Vamos praticar algumas situações reais com esse conhecimento."),
    ("Aplicando o Conhecimento: Exemplos e Casos Reais", "Qual é um exemplo do papel do tecido conjuntivo em sua vida diária? Por favor, compartilhe nos comentários abaixo.")
]

topic = "Crie um video explicação sobre tecido conjuntivo"
domain = resolve_topic_domain(topic)
print(f"Topic Domain resolved: {domain}")

def simulate_theme_detection(topic, title, content, idx):
    c_lower = content.lower()
    d = resolve_topic_domain(topic, title)
    
    if d == "BIOLOGY":
        # Biology-specific archetype matchers
        if re.search(r"(tecido\s+conjuntivo|colágeno|colageno|matriz|fibroblasto|fibra|fibras|sustentação|sustentar|tendão|tendões|pele|ossos|ligamento|cartilagem|adiposo|absorver\s+choque|lesão|cicatrização)", c_lower):
            return "bio_tissue", "HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ EXTRACELULAR"
        if re.search(r"(célula|celular|mitose|membrana|organela|mitocôndria|proteína|proteina)", c_lower):
            return "biogenesis_cell", "BIOLOGIA // ESTRUTURA CELULAR"
        if re.search(r"(microscóp|microscop|infecção|infeccao|bactéria|bacteria|micróbio|combater|defesa|imun)", c_lower):
            return "biogenesis_microscope", "MICROSCOPIA // DEFESA & CÉLULAS"
        if re.search(r"(neurônio|neuronio|sinapse|sistema nervoso)", c_lower):
            return "bio_neuron", "FISIOLOGIA // TECIDO NERVOSO"
        if re.search(r"(dna|genética|gene)", c_lower):
            return "biogenesis_dna", "GENÉTICA // DUPLA HÉLICE"
        if re.search(r"(ecologia|cadeia|trófica|energia)", c_lower):
            return "bio_ecology", "ECOLOGIA // FLUXO TRÓFICO"
        if re.search(r"(pasteur|pescoço de cisne|caldo)", c_lower):
            return "biogenesis_pasteur", "EXPERIMENTO DE PASTEUR"
        if re.search(r"(redi|francesco|mosca|larva)", c_lower):
            return "biogenesis_redi", "EXPERIMENTO DE REDI"
        
        # Rotational biological suite
        bio_rot = [
            ("bio_tissue", "HISTOLOGIA // MATRIZ & SUSTENTAÇÃO"),
            ("biogenesis_cell", "BIOLOGIA // CITOLOGIA & CÉLULAS"),
            ("biogenesis_microscope", "MICROSCOPIA // ESTRUTURA TECIDUAL"),
            ("bio_tissue", "HISTOLOGIA // FIBRAS & ELASTICIDADE"),
            ("biogenesis_dna", "GENÉTICA // CÓDIGO CELULAR"),
        ]
        return bio_rot[idx % len(bio_rot)]

    return "general", "GERAL"

print("\n--- RESULTS FOR ALL 16 REAL SENTENCES ---")
for i, (title, text) in enumerate(test_sentences):
    th, lbl = simulate_theme_detection(topic, title, text, i)
    print(f"[{i+1:02d}] {th:22s} | {lbl}")

