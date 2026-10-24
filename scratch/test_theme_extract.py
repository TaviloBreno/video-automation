import re

THEME_MAP = [
    (r"(câncer|tumor|carcinoma|oncol|célula|biópsia)", ["Cancer_cell", "Mitosis", "Tumor", "Cell_biology"]),
    (r"(imunoterap|sistema imune|anticorpo|linfócit|t-cell)", ["Immunotherapy", "T_cell", "Antibody"]),
    (r"(dna|genoma|mutação|gene|genétic|crispr)", ["DNA", "Gene_editing", "Mutation", "Chromosome"]),
    (r"(quasar|quásar|buraco negro|singularidade|acrec|horizonte de eventos)", ["Quasar", "Black_hole", "Accretion_disk"]),
    (r"(galáxia|universo|hubble|james webb|telescópio|estrela|supernova)", ["Galaxy", "James_Webb_Space_Telescope", "Supernova", "Nebula"]),
    (r"(inteligência artificial|rede neural|algoritmo|deep learning|robô)", ["Artificial_intelligence", "Artificial_neural_network", "Robotics"]),
    (r"(átomo|quântic|elétron|próton|física de partículas)", ["Atom", "Quantum_mechanics", "Particle_physics"]),
    (r"(cérebro|neurônio|sinapse|neurociência)", ["Neuron", "Brain", "Synapse"]),
]

def extract_terms(topic: str, title: str, narration: str) -> list[str]:
    combined = f"{topic} {title} {narration}".lower()
    candidates = []
    for pattern, terms in THEME_MAP:
        if re.search(pattern, combined):
            for t in terms:
                if t not in candidates:
                    candidates.append(t)
    return candidates

ch_title = "O despertar do tumor: como uma única célula se rebela"
ch_narration = "Tudo começa no DNA. Uma mutação sutil engana o sistema de defesa e a célula se multiplica sem freios."
terms = extract_terms("Câncer: a cura está próxima?", ch_title, ch_narration)
print("Termos extraídos:", terms)
