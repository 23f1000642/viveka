# Viveka (विवेक)

An AI ethics advisor built on a retrieval corpus of classical Indian philosophy — the Bhagavad Gita, the Yoga Sutras, and the Arthashastra — reasoning about modern AI harm, transparency, and fairness through categories that predate the field by two thousand years.

## Why this project

Seven categories from classical Indian ethics map cleanly onto seven live problems in AI system design:

| Classical principle | Maps to |
|---|---|
| Ahimsa (अहिंसा) — non-harm | Non-maleficence / harm reduction |
| Satya (सत्य) — truthfulness | Transparency & honest capability claims |
| Dharma (धर्म) — right action in context | Accountability & context-aware duty |
| Nyaya (न्याय) — justice, right reasoning | Fairness & due process |
| Aparigraha (अपरिग्रह) — non-possessiveness | Data minimization |
| Seva (सेवा) — selfless service | Human-centered design |
| Viveka (विवेक) — discernment | Human oversight & the limits of automation |

Full mapping with citations lives in [`docs/MAPPING.md`](docs/MAPPING.md).

## Architecture

Public-domain texts → clean + chunk (verse-level) → embed (Voyage AI) → ChromaDB → retriever (top-k + principle boost) → Groq API / Llama 3.3 (grounded generation) → chat advisor & ethics scorecard → Streamlit UI.

Embeddings are a hosted API call (Voyage AI), not a local model — a local
`sentence-transformers`/`torch` install triggered a Windows Application
Control policy that blocked scikit-learn's compiled DLL outright. Generation
runs on Groq's free tier rather than the Claude API — a fresh Anthropic key
ships with zero free credits, and the RAG architecture doesn't depend on a
specific model vendor (`generate.py` isolates the one function that would
need to change to swap providers again). See `docs/LOG.md` (Days 8 and 10)
for both stories.

## Status

🚧 Week 2 in progress — RAG pipeline (embedding + retrieval) working.
Daily log in [`docs/LOG.md`](docs/LOG.md).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # then fill in VOYAGE_API_KEY and GROQ_API_KEY
python src/data_prep/clean.py
python src/data_prep/chunk.py
python src/rag/index.py     # one-time: embeds all chunks into ChromaDB (~8 min on the free tier)
streamlit run app.py
```

## License

MIT — see [LICENSE](LICENSE).
