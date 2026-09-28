# 🔬 Histolab — HistoIA

Aplicação web para **análise automática de imagens histológicas** (H&E) com fins educacionais: identificação de constituintes celulares, classificação de tecidos, geração de perguntas académicas e chatbot de histologia — tudo **offline e gratuito** (sem APIs pagas).

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **📷 Análise de Imagem** | Submissão por drag-and-drop → desconvolução de cor H&E, segmentação de núcleos, 10 métricas morfométricas, classificação do tecido com confiança e evidência, e sobreposição visual da segmentação. |
| **📝 Perguntas & Avaliação** | Geração automática de MCQ e perguntas abertas a partir das métricas da imagem analisada, com 3 níveis de dificuldade, resposta-modelo e explicação pedagógica. |
| **📚 Galeria de Tecidos** | 12 micrografias H&E de referência (Wikimedia Commons, CC) — epitélio, conjuntivo, muscular, nervoso, adiposo e hepático — com descrição e análise on-demand. |
| **💬 Chatbot** | Tutor offline baseado em regras e glossário de histologia; usa a imagem analisada como contexto (tecido + métricas). Sugestões de perguntas incluídas. |

## Pipeline de análise (como reconhecer e classificar)

1. **Desconvolução de cor** (Ruifrok & Johnston): separa canais de hematoxilina (núcleos) e eosina (citoplasma/matriz) no espaço de densidade ótica, normalizados por p99.
2. **Segmentação de núcleos**: Otsu no canal H → morfologia (abertura/fecho) → componentes conexos com área válida (15–4000 px).
3. **Morfometria por núcleo**: área, perímetro, circularidade e elongação (elipse ajustada, com filtragem de degenerados).
4. **Features globais**: densidade nuclear/mm², área mediana, CV, circularidade/elongação medianas, razão de estroma (eosina não-nuclear), razão de espaços claros (vacúolos/lúmen), médias H e E.
5. **Classificação por regras** com pontuação ponderada por tecido: epitelial, conjuntivo, muscular, nervoso, adiposo e hepático; devolve confiança normalizada e critérios morfológicos que sustentam a decisão.

**Precisão na galeria de referência: 11/12 (92%)** — avaliada contra os rótulos curados.

## Como executar

```bash
pip install flask numpy opencv-python-headless pillow
python3 app.py
# abre http://127.0.0.1:8765
```

Para (re)descarregar a galeria do Wikimedia Commons:

```bash
python3 fetch_gallery.py
```

## API

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/analyze` | POST | `{image: dataURL}` → análise completa |
| `/api/questions` | POST | `{analysis, n, difficulty}` → perguntas |
| `/api/chat` | POST | `{message, tissue?, features?}` → resposta do tutor |
| `/api/gallery` | GET | itens da galeria de referência |
| `/api/gallery/<key>/analysis` | GET | análise pré-computada de um item |

## Estrutura

```
histolab/
├── app.py              # servidor Flask + API
├── analyzer.py         # pipeline de análise (CV)
├── questions.py        # gerador de perguntas académicas
├── chatbot.py          # tutor offline por regras
├── gallery_source.py   # definição da galeria curada
├── fetch_gallery.py    # descarregador (Wikimedia Commons API)
├── gallery_meta.json   # metadados + atribuição de imagens
└── static/
    ├── index.html      # SPA (4 abas, PT-PT)
    └── gallery/        # 12 micrografias H&E
```

## Limitações

- Ferramenta **educacional**: não substitui diagnóstico patológico.
- Coloração H&E assumida; outras técnicas (PAS, tricrómico, IHQ) não são otimizadas.
- A precisão depende da qualidade do corte e da coloração; espaços em branco do slide podem inflar a razão de espaços claros.

## Créditos

Imagens: Wikimedia Commons (CC BY / CC BY-SA / domínio público — ver `gallery_meta.json` para atribuição por imagem).
