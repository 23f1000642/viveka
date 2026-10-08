"""Wire retrieval (Day 8) and the grounded prompt (Day 9) to an LLM call —
the full question -> grounded answer pipeline.

Uses Groq's OpenAI-compatible chat API (free tier, Llama 3.3) rather than
Anthropic's — a fresh Anthropic API key ships with zero free credits, and
proving the RAG architecture works doesn't require a specific model
vendor. Swapping providers only touched this one function, because the
retrieval and prompt-formatting logic (retriever.py, prompts.py) doesn't
know or care which LLM eventually reads its output.
"""
import sys

import requests

# Windows' default console codepage (cp1252) can't print some characters an
# LLM commonly emits (curly quotes, em-dashes, narrow no-break spaces) —
# force UTF-8 stdout so printing an answer doesn't crash.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from llm import API_URL, MODEL, api_key
from retriever import retrieve
from prompts import SYSTEM_PROMPT, build_user_message
from scope import check_scope

MAX_TOKENS = 800

# Human-readable labels for the raw source slugs in chunks.jsonl — the UI
# (Week 4) shouldn't have to show someone "gita_arnold".
SOURCE_LABELS = {
    "gita_arnold": "Bhagavad Gita (trans. Edwin Arnold)",
    "yoga_sutras_johnston": "Yoga Sutras of Patanjali (trans. Charles Johnston)",
    "upanishads_paramananda": "The Upanishads (trans. Swami Paramananda)",
}


def _short_quote(text: str, max_len: int = 160) -> str:
    """A short excerpt for display next to a citation — full text still
    lives in the chunk itself; this is just for a human to glance at."""
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "..."


def generate_answer(query: str, top_k: int = 5) -> dict:
    category, reply = check_scope(query)
    if reply is not None:  # not an AI-ethics question: skip retrieval entirely
        return {
            "query": query,
            "scope": category,
            "detected_principles": [],
            "answer": reply,
            "sources": [],
        }

    detected_principles, chunks = retrieve(query, top_k=top_k)
    user_message = build_user_message(query, chunks)

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key()}"},
        json={
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    answer = resp.json()["choices"][0]["message"]["content"]

    return {
        "query": query,
        "scope": "in_scope",
        "detected_principles": sorted(detected_principles),
        "answer": answer,
        "sources": [
            {
                "n": i,
                "chunk_id": c["chunk_id"],
                "source": c["source"],
                "source_label": SOURCE_LABELS.get(c["source"], c["source"]),
                "book": c["book"],
                "verses": c["verses"],
                "reference": c["reference"],
                "quote": _short_quote(c["text"]),
            }
            for i, c in enumerate(chunks, start=1)
        ],
    }


if __name__ == "__main__":
    test_queries = [
        "Is it wrong for an AI system to collect more personal data than it needs?",
        "Should a hiring algorithm's decisions be explainable to the applicant?",
        "Is it okay for a recommendation system to be designed to be addictive?",
    ]
    for q in test_queries:
        result = generate_answer(q, top_k=3)
        print(f"Q: {q}")
        print(f"Detected: {result['detected_principles']}")
        print(f"A: {result['answer']}")
        print("Sources:")
        for s in result["sources"]:
            print(f"  [{s['n']}] {s['source_label']}, {s['reference']}")
            print(f"      \"{s['quote']}\"")
        print()
