with open('scripts/long_video.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = '''SUPPORTED_ARCHETYPES = [
    "politics", "social", "psychology", "analytics", "history",
    "orbital", "infographic", "blueprint", "spectrum", "network", "timeline", "quantum", "formula"
]'''

new = '''SUPPORTED_ARCHETYPES = [
    # Vestibular, Concursos & Ciências da Natureza
    "bio_tissue", "biogenesis_cell", "biogenesis_pasteur", "biogenesis_redi",
    "biogenesis_microscope", "biogenesis_dna", "biogenesis_puzzle", "biogenesis_versus",
    "bio_ecology", "bio_neuron", "law_constitution", "law_limpe", "logic_venn",
    "logic_truth_table", "grammar_syntax", "redacao_enem", "math_cartesian",
    "physics_mechanics", "physics_circuits", "chemistry_organic", "chemistry_reaction",
    "history_brazil", "geo_plates",
    # Didática Geral, Gramática & Fixação
    "grammar", "lesson", "comparison", "finance",
    # Divulgação Científica
    "politics", "social", "psychology", "analytics", "history",
    "orbital", "infographic", "blueprint", "spectrum", "network", "timeline", "quantum", "formula"
]'''

assert old in c, 'old not found in long_video.py'
c = c.replace(old, new, 1)
with open('scripts/long_video.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('long_video.py updated!')

