"""Offline histology tutor chatbot.

Rule/intent-based NLU over a curated histology knowledge base —
no external API, completely free to run.
"""
from __future__ import annotations

import re
from typing import Any

KB: dict[str, dict[str, Any]] = {
    "hematoxilina": {
        "keywords": ["hematoxilina", "basofilia", "basófilo", "basofilo", "azul", "cora.*núcleo", "cora.*nucleo", "h&e", "he染色"],
        "answer": "A **hematoxilina** é um corante básico (basófilo) da coloração H&E. Cora componentes ácidos — sobretudo **ácidos nucleicos** (DNA cromatina, RNA) — conferindo aos núcleos um aspeto **azul-violeta**. Estruturas basófilas: núcleos, corpos de Nissl, matriz metacromática (com corantes adequados).",
        "links": ["Qual a diferença entre basofilia e acidofilia?", "Como funciona a desconvolução de cor?"],
    },
    "eosina": {
        "keywords": ["eosina", "eosin", "acidofilia", "acidófilo", "acidofilo", "rosa", "vermelho"],
        "answer": "A **eosina** é um corante ácido (acidófilo/eosinófilo). Cora componentes básicos — **proteínas citoplasmáticas**, **colagénio**, **fibras musculares**, **eritrócitos** — conferindo o aspeto **rosa-avermelhado** típico do citoplasma e da matriz extracelular.",
        "links": ["O que cora a hematoxilina?", "Que estruturas correspondem ao estroma na análise?"],
    },
    "epitélio": {
        "keywords": ["epit[ée]lio", "epitelial", "polaridade", "membrana basal", "junç[õo]es", "desmossomo", "microvilosidade"],
        "answer": "**Epitélio**: tecido de revestimento e absorção. Critérios morfológicos: células justapostas com **polaridade apical-basal**, **junções intercelulares** (zonula occludens, desmossomas), **membrana basal** subjacente, escassa matriz extracelular e elevada densidade nuclear em cortes. Classifica-se em simples, estratificado, pseudoestratificado, e por forma: pavimentoso, cúbico, cilíndrico; ainda transitório (urotélio).",
        "links": ["Como distinguir epitélio de conjuntivo?", "O que é o urotélio?"],
    },
    "conjuntivo": {
        "keywords": ["conjuntivo", "colag[ée]nio", "colageno", "estroma", "fibroblasto", "matriz extracelular", "frouxo", "denso"],
        "answer": "**Tecido conjuntivo**: células dispersas em abundante **matriz extracelular**. O conjuntivo frouxo tem fibras finas, fibroblastos e células inflamatórias; o denso é rico em feixes de **colagénio** (eosinofílicos, ondulados). Funções: suporte, defesa, nutrição, reparação. Na análise automática, corresponde à fração eosinofílica **não nuclear** (razão de estroma elevada).",
        "links": ["Como identificar fibras colagénicas?", "Que células se encontram no conjuntivo frouxo?"],
    },
    "muscular": {
        "keywords": ["muscular", "músculo", "musculo", "miosina", "actina", "estriado", "liso", "card[íi]aco", "sarc[óo]mero"],
        "answer": "**Tecido muscular**: células alongadas (**fusiformes** no liso, cilíndricas no esquelético/cardíaco) com núcleos periféricos (esquelético) ou centrais (liso, cardíaco). O esquelético e cardíaco apresentam **estrias transversais** pela organização em sarcómeros; o cardíaco tem **discos intercalares**. Citoplasma intensamente **eosinófilo** por abundância de proteínas contrácteis — na análise, elongação nuclear elevada e eosinofilia marcada.",
        "links": ["Como distinguir músculo liso de esquelético?", "O que são discos intercalares?"],
    },
    "nervoso": {
        "keywords": ["nervoso", "neur[óo]nio", "neuronio", "gli[óa]", "neurópilo", "neuropilo", "nissl", "dendrite", "ax[óo]nio"],
        "answer": "**Tecido nervoso**: **neurónios** (corpo celular/pericário com núcleo grande e vesicular, citoplasma basófilo com corpos de Nissl) e **gliócitos** (núcleos pequenos, picnóticos). O **neuropilo** é o fundo claro de processos celulares e fibras. A densidade nuclear é tipicamente baixa em cortes de córtex/gânglios, com predomínio de pequenos núcleos de gliócitos.",
        "links": ["O que são corpos de Nissl?", "Como reconhecer um gânglio?"],
    },
    "adiposo": {
        "keywords": ["adiposo", "adipócito", "adipocito", "gordo", "lip[íi]deo", "lipideo", "vacúolo", "vacuolo", "septo"],
        "answer": "**Tecido adiposo**: adipócitos com **vacúolo lipídico único** que desloca o núcleo para a periferia. Em H&E, a gordura é extraída na preparação, deixando **grandes espaços claros** com núcleo achatado na margem — o sinal de maior peso na nossa análise automática (razão de espaços claros elevada). Adipócitos uniloculares (branco) vs. multiloculares (castanho).",
        "links": ["Porque aparecem espaços brancos em H&E?", "Diferença entre adiposo branco e castanho?"],
    },
    "fígado": {
        "keywords": ["f[íi]gado", "hep[áa]tic", "hepatócito", "hepatocito", "sinusoide", "tr[íi]ada portal", "lobulo hepático", "lóbulo hepático"],
        "answer": "**Fígado (parênquima hepático)**: **hepatócitos** em lâminas/cordas de 1–2 células com núcleos grandes e **monótonos**, citoplasma eosinófilo abundante, **sinusoides** entre as cordas, **tríada portal** (artéria, veia porta, ducto bilífero) e **veia central** no centro do lóbulo. Estroma mínimo — na análise: densidade nuclear moderada-alta com coeficiente de variação baixo.",
        "links": ["O que é a tríada portal?", "Que funções tem o hepatócito?"],
    },
    "núcleo": {
        "keywords": ["n[úu]cleo", "nucleo", "cromatina", "mitose", "caricose", "picnose", "apoptose"],
        "answer": "**Núcleos em H&E**: basófilos (azul) por causa da cromatina. Critérios de avaliação: **tamanho**, **forma** (arredondado vs. alongado), **razão nuclear/citoplasmática**, **textura da cromatina** (fina/vesicular vs. grosseira/hipercromática), **nucleolos** proeminentes. Alterações: **picnose** (condensação), **cariorrexe** (fragmentação), **cariólise** (dissolução) — marcadores de necrose; **figuras mitóticas** atípicas sugerem malignidade.",
        "links": ["O que é hipercromatismo?", "Como reconhecer apoptose vs. necrose?"],
    },
    "classificação": {
        "keywords": ["classificar", "classifica", "identificar tecido", "diferenciar", "distinguir", "reconhecer"],
        "answer": "**Estratégia de classificação tecidular** em 4 passos: 1) **Baixa ampliação**: arquitetura global (camadas, feixes, lóbulos); 2) **Coloração**: núcleos azuis (basófilos) vs. matriz rosada (acidófila); 3) **Células**: densidade, forma e disposição dos núcleos; 4) **Matriz**: abundância e tipo (colagénio, reticulares, elásticas). Critérios objetivos usados pela análise automática: densidade nuclear/mm², circularidade e elongação médias, razão de estroma e razão de espaços claros.",
        "links": ["Como funciona a segmentação automática de núcleos?", "Que critérios diferenciam epitélio de conjuntivo?"],
    },
    "análise automática": {
        "keywords": ["an[áa]lise automatica", "segmenta", "algoritm", "como funciona.*an[áa]lise", "precis", "acur[áa]cia", "detec[çt][ãa]o"],
        "answer": "**Como funciona a análise automática**: 1) **Desconvolução de cor** (Ruifrok & Johnston) separa os canais de hematoxilina e eosina no espaço de densidade ótica; 2) **Otsu + morfologia + watershed** segmenta núcleos individuais; 3) Extração de **features morfométricas** (áreas, perímetros, circularidades, elongação, razões de estroma/espaço); 4) Um **classificador baseado em regras** pontua cada tipo de tecido e devolve confiança com evidência morfológica. Para máxima precisão clínica, este sistema deve ser usado como ferramenta educacional, não como diagnóstico.",
        "links": ["O que é a desconvolução de cor?", "Como são extraídas as features?"],
    },
    "estroma": {
        "keywords": ["estroma", "fração estromal", "razão de estroma"],
        "answer": "Na análise automática, a **razão de estroma** é a fração de pixels com eosinofilia significativa **não atribuídos a núcleos**. Corresponde ao conteúdo proteico da matriz extracelular + citoplasma não nuclear. Valores altos (>0,5) apontam para conjuntivo; baixos (<0,3) para epitélios ou parênquimas celulares densos.",
        "links": ["Que estruturas correspondem à fração eosinofílica?", "Como classificar o tecido automaticamente?"],
    },
    "mitose": {
        "keywords": ["mitose", "mit[óo]tic", "figura mit[óo]tica", "prolifera"],
        "answer": "**Figuras mitóticas** em H&E: cromatina condensada em massas escuras, às vezes com aspeto de placa metafásica. A contagem de mitoses por 10 campos de grande aumento é o **índice mitótico**, parâmetro chave de graduação tumoral. Na análise automática, mitoses aparecem como núcleos com área e densidade ótica atípicamente elevadas — este sistema sinaliza outliers morfométricos para revisão manual.",
        "links": ["Como reconhecer malignidade?", "O que é o índice mitótico?"],
    },
}


def _match_intent(message: str) -> str | None:
    m = message.lower()
    scores: list[tuple[float, str]] = []
    for key, entry in KB.items():
        score = 0.0
        for pat in entry["keywords"]:
            if re.search(pat, m):
                score += 2 if re.search(pat, m).group(0) == m.strip() else 1
        # simple word overlap
        for w in re.findall(r"\w{4,}", m):
            for pat in entry["keywords"]:
                if w in pat or pat in w:
                    score += 0.5
        if score > 0:
            scores.append((score, key))
    if not scores:
        return None
    scores.sort(reverse=True)
    return scores[0][1]


FALLBACK = "Posso ajudar com **histologia e a análise desta imagem**! Tenta perguntar, por exemplo:\n- «O que cora a hematoxilina?»\n- «Como classificar tecido conjuntivo?»\n- «O que significa a densidade nuclear elevada?»\n- «Quais os critérios de malignidade nuclear?»"

CONTEXT_PREFIX = {
    "epithelial": "Considerando a tua imagem classificada como **tecido epitelial** (confiança alta): ",
    "connective": "Considerando a tua imagem classificada como **tecido conjuntivo**: ",
    "muscular": "Considerando a tua imagem classificada como **tecido muscular**: ",
    "nervous": "Considerando a tua imagem classificada como **tecido nervoso**: ",
    "adipose": "Considerando a tua imagem classificada como **tecido adiposo**: ",
    "liver": "Considerando a tua imagem classificada como **parênquima hepático**: ",
}


def chat_reply(message: str, tissue: str | None = None, features: dict | None = None) -> dict[str, Any]:
    """Return a tutor reply for a student question. Context is image-derived."""
    intent = _match_intent(message)
    if intent:
        answer = KB[intent]["answer"]
        if tissue and tissue in CONTEXT_PREFIX:
            answer = CONTEXT_PREFIX[tissue] + answer
        if features and intent in ("núcleo", "classificação", "análise automática", "estroma"):
            answer += f"\n\n**Métricas da tua imagem**: {features.get('n_nuclei')} núcleos, densidade {features.get('nuclei_per_mm2')}/mm², circularidade média {features.get('median_circularity')}, estroma {features.get('stromal_ratio')}."
        return {"reply": answer, "suggestions": KB[intent]["links"]}
    # Generic numeric question
    if re.search(r"\b(densidade|nucleo|núcleo|quantos)\b", message.lower()):
        if features:
            return {"reply": f"Nesta imagem foram identificados **{features.get('n_nuclei')} núcleos** (≈{features.get('nuclei_per_mm2')}/mm²), com área média de {features.get('median_nucleus_area')} px² e circularidade média {features.get('median_circularity')}. A fração de estroma é {features.get('stromal_ratio')} e a de espaços claros {features.get('empty_ratio')}.", "suggestions": ["O que cora a hematoxilina?", "Como classificar o tecido?"]}
    return {"reply": FALLBACK, "suggestions": ["O que cora a hematoxilina?", "Como classificar tecidos?", "Que critérios indicam malignidade?"]}
