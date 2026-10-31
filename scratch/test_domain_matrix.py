import re

def resolve_topic_domain(topic: str, chapter_title: str = "") -> str:
    text = f" {topic} {chapter_title} ".lower()
    
    # 1. DIREITO & ADMINISTRAÇÃO PÚBLICA (CONCURSOS)
    if re.search(r"(\bdireito\b|constitucional|cf/88|cf\s*88|artigo\s*\d+|art\.\s*\d+|direitos\s+fundamentais|remédios\s+constitucionais|habeas\s+corpus|mandado\s+de\s+segurança|três\s+poderes|judiciário|legislativo|executivo|stf|stj|administrativo|limpe|legalidade|impessoalidade|moralidade|publicidade|eficiência|servidor\s+público|ato\s+administrativo|concurso\s+público|licitação|processo\s+disciplinar|órgão\s+público|oab)", text):
        return "LAW"

    # 2. GRAMÁTICA, LÍNGUA PORTUGUESA & REDAÇÃO
    if re.search(r"(\bcrase\b|acento\s+grave|regência|regencia|concordância|concordancia|preposição|preposicao|artigo\s+definido|artigo\s+indefinido|artigo\s+feminino|artigo\s+masculino|substantivo|adjetivo|pronome|verbo|análise\s+sintática|analise\s+sintatica|sujeito|predicado|oração|oracao|período\s+composto|pontuação|pontuacao|ortografia|acentuação|acentuacao|redação\s+enem|redacao\s+enem|nota\s+1000|língua\s+portuguesa|lingua\s+portuguesa|\bportuguês\b|\bportugues\b)", text):
        return "GRAMMAR"

    # 3. BIOLOGIA & SAÚDE
    if re.search(r"(\bbiologia\b|\bbiolog|célula|celular|tecido|histologia|histolog|conjuntiv|epitelial|ósseo|osseo|cartilag|muscular|sanguíneo|sanguineo|linfático|linfatico|adipos|fibroblasto|colágen|colagen|biogênese|biogenese|abiogênese|abiogenese|origem\s+da\s+vida|pasteur|redi|dna|genética|genetica|genoma|mitocôndria|mitocondria|mitose|meiose|organela|ecologia|trófic|trofic|cadeia\s+alimentar|fotossíntese|fotossintese|respiração\s+celular|respiracao\s+celular|neurônio|neuronio|sinapse|sistema\s+nervoso|imunologia|anticorpo|vacina|vírus|virus|bactéria|bacteria|\bevolução\b|\bevolucao\b|darwin|seleção\s+natural|anatomia|fisiologia)", text):
        return "BIOLOGY"

    # 4. FÍSICA
    if re.search(r"(\bfísica\b|\bfisica\b|newton|leis\s+de\s+newton|plano\s+inclinado|cinemática|cinematica|velocidade|aceleração|aceleracao|dinâmica|dinamica|gravitação|gravitacao|termodinâmica|termodinamica|óptica|optica|espelho|lente|ondulatória|ondulatoria|comprimento\s+de\s+onda|eletricidade|circuito|resistor|\bohm\b|voltagem|corrente\s+elétrica|corrente\s+eletrica|eletromagnetismo|indução|campo\s+magnético|mecânica\s+quântica|mecanica\s+quantica)", text):
        return "PHYSICS"

    # 5. QUÍMICA
    if re.search(r"(\bquímica\b|\bquimica\b|tabela\s+periódica|tabela\s+periodica|ligação\s+química|ligacao\s+quimica|ligação\s+covalente|ligação\s+iônica|estequiometria|\bmol\b|massa\s+molar|química\s+orgânica|quimica\s+organica|hidrocarboneto|benzeno|função\s+orgânica|isomeria|álcool|termoquímica|entalpia|cinética\s+química|\bph\b|ácido|base|titulação|soluções|eletroquímica|pilha|eletrólise)", text):
        return "CHEMISTRY"

    # 6. MATEMÁTICA & RACIOCÍNIO LÓGICO
    if re.search(r"(\bmatemática\b|\bmatematica\b|função\s+afim|função\s+quadrática|parábola|bhaskara|vértice|geometria|trigonometria|seno|cosseno|tangente|matriz|determinante|probabilidade|análise\s+combinatória|analise\s+combinatoria|estatística|estatistica|desvio\s+padrão|raciocínio\s+lógico|rlm|diagrama\s+de\s+venn|tabela[- ]verdade|lógica\s+proposicional)", text):
        return "MATH"

    # 7. HISTÓRIA
    if re.search(r"(\bhistória\b|\bhistoria\b|brasil\s+colônia|brasil\s+império|brasil\s+república|era\s+vargas|ditadura\s+militar|revolução|revolucao|século|seculo|idade\s+média|idade\s+moderna|feudalismo|iluminismo|primeira\s+guerra|segunda\s+guerra|guerra\s+fria)", text):
        return "HISTORY"

    # 8. GEOGRAFIA
    if re.search(r"(\bgeografia\b|placas\s+tectônicas|placas\s+tectonicas|tectônica|deriva\s+continental|relevo|orogênese|crosta|manto|vulcão|terremoto|clima|cartografia|bioma|demografia|urbanização|geopolítica)", text):
        return "GEOGRAPHY"

    # 9. FINANÇAS & MERCADO FINANCEIRO
    if re.search(r"(\bfinanças\b|\bfinancas\b|bolsa\s+de\s+valores|ibovespa|\bações\b|investimento|renda\s+fixa|selic|cdi|fundo\s+imobiliário|criptomoeda|bitcoin|balanço\s+patrimonial|valuation|dividendos)", text):
        return "FINANCE"

    # 10. PSICOLOGIA & COMPORTAMENTO
    if re.search(r"(\bpsicologia\b|psicanálise|psicanalise|freud|jung|saúde\s+mental|saude\s+mental|neurociência|neurociencia|viés\s+cognitivo|vies\s+cognitivo|behaviorismo)", text):
        return "PSYCHOLOGY"

    # 11. ASTRONOMIA & ASTROFÍSICA
    if re.search(r"(\bastronomia\b|astrofísica|astrofisica|quasar|buraco\s+negro|singularidade|horizonte\s+de\s+eventos|via\s+láctea|exoplaneta|telescópio\s+james\s+webb|cosmologia|supernova)", text):
        return "ASTRONOMY"

    return "GENERAL"

test_topics = [
    ("Crie um video explicação sobre tecido conjuntivo", "BIOLOGY"),
    ("Explique o uso da Crase", "GRAMMAR"),
    ("Princípios Constitucionais do Artigo 37 da CF/88", "LAW"),
    ("Leis de Newton e Forças", "PHYSICS"),
    ("Química Orgânica e Benzeno", "CHEMISTRY"),
    ("Função Quadrática e Bhaskara", "MATH"),
    ("Revolução Francesa e Século XVIII", "HISTORY"),
    ("Tectônica de Placas e Relevo", "GEOGRAPHY"),
    ("Investimentos em Ações e Renda Fixa", "FINANCE"),
    ("Psicologia e Vieses Cognitivos", "PSYCHOLOGY"),
    ("Astrofísica e Buracos Negros", "ASTRONOMY"),
]

all_passed = True
for topic, expected in test_topics:
    res = resolve_topic_domain(topic)
    match = res == expected
    status = "OK" if match else f"FAIL (got {res})"
    if not match:
        all_passed = False
    print(f"{topic:50s} -> {res:12s} [{status}]")

print(f"\nMatrix test result: {'ALL PASSED!' if all_passed else 'FAILED'}")
