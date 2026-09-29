"""Wire retrieval (Day 8) and the grounded prompt (Day 9) to an actual
Claude API call — the full question -> grounded answer pipeline.
"""
import os

import anthropic
from dotenv import load_dotenv

from retriever import retrieve
from prompts import SYSTEM_PROMPT, build_user_message

load_dotenv()

MODEL = "claude-sonnet-5"
MAX_TOKENS = 800


def generate_answer(query: str, top_k: int = 5) -> dict:
    detected_principles, chunks = retrieve(query, top_k=top_k)
    user_message = build_user_message(query, chunks)

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return {
        "query": query,
        "detected_principles": sorted(detected_principles),
        "answer": response.content[0].text,
        "sources": [
            {
                "n": i,
                "chunk_id": c["chunk_id"],
                "source": c["source"],
                "book": c["book"],
                "verses": c["verses"],
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
            print(f"  [{s['n']}] {s['source']} {s['book'] or ''} v.{s['verses']}")
        print()
