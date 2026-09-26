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

Full mapping with citations lives in [`docs/MAPPING.md`](docs/MAPPING.md) (coming Day 1).

## Architecture

Public-domain texts → clean + chunk (verse-level) → embed (sentence-transformers) → ChromaDB → retriever (top-k + principle boost) → Claude API (grounded generation) → chat advisor & ethics scorecard → Streamlit UI.

## Status

🚧 Day 0 — project scaffolded. Roadmap and daily log in [`docs/LOG.md`](docs/LOG.md).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

## License

MIT — see [LICENSE](LICENSE).
