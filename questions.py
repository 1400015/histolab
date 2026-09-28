"""Question generator for academic training/assessment.

Generates multiple-choice and open questions from analysis features,
with difficulty scaling, answer key and pedagogical explanations.
"""
from __future__ import annotations

import random
from typing import Any

TISSUE_PT = {
    "epithelial": ("epitelial", "Estes núcleos densos, arredondados e com pouca matriz extracelular indicam epitélio — tecido de cobertura/revestimento com polaridade celular e junções intercelulares."),
    "connective": ("conjuntivo", "A abundante matriz extracelular eosinofílica com núcleos dispersos indica tecido conjuntivo — funções de suporte, preenchimento e defesa."),
    "muscular": ("muscular", "Núcleos alongados/fusiformes e citoplasma intensamente eosinofílico indicam tecido muscular — células contráteis ricas em filamentos de actina e miosina."),
    "nervous": ("nervoso", "Baixa densidade nuclear com neuropilo claro e núcleos pequenos arredondados indica tecido nervoso — neurónios e gliócitos."),
    "adipose": ("adiposo", "Grandes espaços claros correspondendo a vacúolos lipídicos únicos indicam tecido adiposo — adipócitos especializados em armazenamento de energia."),
    "liver": ("hepático (fígado)", "Núcleos monótonos dispostos em cordas com estroma mínimo indicam parênquima hepático — hepatócitos em lâminas de 1–2 células."),
}

STRUCTURE_GLOSSARY = {
    "epithelial": ["membrana basal", "junções intercelulares (desmossomas, zonula occludens)", "polaridade apical-basal", "microvilosidades"],
    "connective": ["fibras colagénicas", "fibroblastos", "matriz extracelular", "células inflamatórias"],
    "muscular": ["miofibrilhas", "estrias transversais", "discos intercalares (cardíaco)", "células de Purkinje"],
    "nervous": ["corpo celular (pericário)", "dendrites", "neurofibrilhas", "células satélite"],
    "adipose": ["vacúolo lipídico único", "núcleo periférico achatado", "septo conjuntivo"],
    "liver": ["sinusoides", "tríada portal", "space of Disse", "veia central"],
}


def generate_questions(analysis: dict[str, Any], n: int = 6, difficulty: str = "medium",
                       seed: int | None = None) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    f = analysis["features"]
    tissue = analysis["tissue"]
    t_pt, t_desc = TISSUE_PT.get(tissue, (tissue, ""))
    density = f["nuclei_per_mm2"]
    n_nuc = f["n_nuclei"]
    circ = f["median_circularity"]
    elong = f["median_elongation"]
    stroma = f["stromal_ratio"]

    pool: list[dict[str, Any]] = []

    # 1. Tissue identification MCQ
    correct_opts = [t_pt]
    others = [v[0] for k, v in TISSUE_PT.items() if k != tissue]
    rng.shuffle(others)
    opts = correct_opts + others[:3]
    rng.shuffle(opts)
    pool.append({
        "type": "mcq",
        "difficulty": "easy" if difficulty != "hard" else "medium",
        "question": "Com base nas características morfométricas da imagem, que tipo de tecido está representado?",
        "options": opts,
        "answer": t_pt,
        "explanation": t_desc,
        "topic": "classificação tecidular",
    })

    # 2. Justification question
    pool.append({
        "type": "open",
        "difficulty": "medium",
        "question": f"Justifique a classificação como tecido {t_pt}, indicando pelo menos duas características morfológicas observáveis na imagem que a sustentam.",
        "answer": t_desc,
        "explanation": "Critérios esperados: " + "; ".join(TISSUE_PT[tissue][1].split("—")[-1].strip(" .").split(", ")[:3]) if tissue in TISSUE_PT else "Comparar densidade nuclear, cromatina e matriz extracelular com atlas.",
        "topic": "raciocínio morfológico",
    })

    # 3. Quantitative interpretation
    pool.append({
        "type": "mcq",
        "difficulty": difficulty,
        "question": f"A densidade nuclear estimada na imagem é aproximadamente {density:.0f} núcleos/mm² e a razão de estroma é {stroma:.2f}. O que esta combinação indica?",
        "options": [
            "Tecido com elevada celularidade e escassa matriz extracelular, típico de epitélios",
            "Tecido com predomínio de matriz extracelular e células raras, típico de conjuntivo frouxo",
            "Tecido necrótico com perda de núcleos",
            "Artefacto de coloração insuficiente com hematoxilina",
        ],
        "answer": "Tecido com predomínio de matriz extracelular e células raras, típico de conjuntivo frouxo" if stroma > 0.5 else "Tecido com elevada celularidade e escassa matriz extracelular, típico de epitélios",
        "explanation": "A densidade nuclear correlaciona-se inversamente com a fração de estroma; valores elevados de ambas as métricas são mutuamente exclusivos em preparações bem coradas.",
        "topic": "interpretação quantitativa",
    })

    # 4. Nucleus morphology
    if elong > 1.5:
        q = "A elongação média nuclear observada é superior a 1,5. Que tipo de célula tipicamente apresenta núcleos alongados/fusiformes em cortes histológicos?"
        correct = "Célula muscular lisa"
        opts = ["Célula muscular lisa", "Hepatócito", "Adipócito", "Neurónio"]
    elif circ > 0.7:
        q = "A circularidade média nuclear observada é elevada (>0,7). O que indica alta circularidade nuclear em cortes histológicos?"
        correct = "Núcleos arredondados, frequentemente em epitélios ou tecidos com alta taxa proliferativa"
        opts = [correct, "Núcleos picnóticos em necrose", "Sempre artefacto de corte tangencial", "Núcleos de células apoptóticas em fragmentação"]
    else:
        q = f"Foram identificados cerca de {n_nuc} núcleos no campo analisado. Qual é a principal limitação da contagem automática de núcleos em cortes histológicos?"
        correct = "Núcleos sobrepostos e cortes tangenciais podem fundir-se, subestimando a contagem real"
        opts = [correct, "A contagem automática é sempre exata", "A hematoxilina não colore núcleos", "Não é possível segmentar núcleos em H&E"]
    rng.shuffle(opts)
    pool.append({"type": "mcq", "difficulty": difficulty, "question": q, "options": opts, "answer": correct,
                 "explanation": "A forma nuclear é um dos critérios morfológicos fundamentais na diferenciação celular.", "topic": "morfologia nuclear"})

    # 5. Staining mechanics
    pool.append({
        "type": "mcq",
        "difficulty": "easy",
        "question": "Na coloração H&E, que estruturas são coradas preferencialmente pela hematoxilina?",
        "options": ["Núcleos (ácidos nucleicos, basofilia)", "Matriz extracelular colagénica", "Membranas lipídicas", "Glóbulos vermelhos (que ficam azuis)"],
        "answer": "Núcleos (ácidos nucleicos, basofilia)",
        "explanation": "A hematoxilina é básica e colore componentes ácidos (DNA/RNA) em azul-púrpura; a eosina é ácida e colore estruturas básicas como proteínas citoplasmáticas e colagénio em rosa.",
        "topic": "técnicas histológicas",
    })

    # 6. Structure recall
    gloss = STRUCTURE_GLOSSARY.get(tissue, ["matriz extracelular"])
    correct = rng.choice(gloss)
    others_all = [s for k, v in STRUCTURE_GLOSSARY.items() if k != tissue for s in v]
    rng.shuffle(others_all)
    opts = [correct] + others_all[:3]
    rng.shuffle(opts)
    pool.append({
        "type": "mcq",
        "difficulty": difficulty,
        "question": f"Que estrutura é característica do tecido {t_pt} e tipicamente observável neste tipo de preparação?",
        "options": opts,
        "answer": correct,
        "explanation": f"Estruturas características do tecido {t_pt}: " + "; ".join(gloss) + ".",
        "topic": "estruturas tecidulares",
    })

    # 7. Pathology bridge (hard)
    pool.append({
        "type": "open",
        "difficulty": "hard",
        "question": "Se a densidade nuclear nesta amostra aumentasse drasticamente com perda da arquitetura tecidular e aumento da razão nuclear/citoplasmática, que diagnóstico deveria ser considerado e porquê?",
        "answer": "Neoplasia — a perda de polaridade, aumento da razão N/C, pleomorfismo nuclear e desorganização arquitetural são critérios de malignidade segundo as características de anaplasia.",
        "explanation": "Critérios de malignidade: pleomorfismo, hipercromatismo, figuras mitóticas atípicas e perda da diferenciação tecidular.",
        "topic": "patologia",
    })

    # 8. Acidophilic structures
    pool.append({
        "type": "mcq",
        "difficulty": "medium",
        "question": "O que representa a fração eosinofílica da imagem no contexto da análise tecidular?",
        "options": ["Conteúdo proteico citoplasmático e matriz extracelular", "Exclusivamente glóbulos vermelhos", "Fibras elásticas apenas", "Núcleos em apoptose"],
        "answer": "Conteúdo proteico citoplasmático e matriz extracelular",
        "explanation": "A eosina colore estruturas acidófilas: proteínas citoplasmáticas, colagénio, fibras musculares e eritrócitos.",
        "topic": "técnicas histológicas",
    })

    if difficulty == "hard":
        rng.shuffle(pool)
    else:
        easy_first = sorted(pool, key=lambda q: {"easy": 0, "medium": 1, "hard": 2}[q["difficulty"]])
        pool = easy_first
    return pool[:max(1, n)]
