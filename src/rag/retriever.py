"""Retrieve the most relevant chunks for a query: embedding similarity first,
then re-ranked with a boost for chunks whose principle tags match the query.

The boost exists because of what Day 7 found: a 2026 AI-ethics question and
a 1912 translation of the Yoga Sutras don't sit close together in embedding
space on vocabulary alone. So this file keeps a SEPARATE keyword lexicon —
modern AI-ethics terms, not the ancient-text terms chunk.py uses — just to
guess which of the seven principles a query is actually about.
"""
from embeddings import embed_texts
from vectorstore import Store

# Modern AI/tech-ethics vocabulary -> principle. Deliberately separate from
# chunk.py's PRINCIPLE_KEYWORDS, which is tuned to 100-year-old scripture
# translations and would miss almost every query a real user types.
QUERY_KEYWORDS = {
    "ahimsa": ["harm", "hurt", "unsafe", "danger", "injury", "hurts people", "safety"],
    "satya": ["transparen", "honest", "lie", "deceiv", "mislead", "false", "overstate"],
    "dharma": ["accountab", "responsib", "duty", "who is at fault", "role"],
    "nyaya": ["fair", "bias", "discrimina", "justice", "appeal", "explainable", "explain the decision"],
    "aparigraha": ["data collection", "personal data", "privacy", "hoard", "excess data", "retain data"],
    "seva": ["user's best interest", "engagement", "addictive", "manipulat", "dark pattern", "welfare"],
    "viveka": ["human oversight", "human in the loop", "automat", "autonomous decision", "override"],
}

_store = None


def _get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def detect_query_principles(query: str):
    lowered = query.lower()
    return [p for p, keywords in QUERY_KEYWORDS.items() if any(k in lowered for k in keywords)]


def retrieve(query: str, top_k: int = 5, fetch_k: int = 20, boost: float = 0.25):
    """Fetch fetch_k candidates by raw similarity, then re-rank the top_k by
    subtracting `boost` from a candidate's distance for every principle it
    shares with the query (lower distance = more similar = ranked higher)."""
    store = _get_store()

    query_principles = set(detect_query_principles(query))
    q_emb = embed_texts([query], input_type="query")[0]

    candidates = []
    for hit in store.query(q_emb, fetch_k):
        doc, meta, dist, chunk_id = hit["document"], hit["metadata"], hit["distance"], hit["id"]
        chunk_principles = set(meta["principles"].split(",")) if meta["principles"] else set()
        overlap = len(query_principles & chunk_principles)
        adjusted_score = dist - boost * overlap
        candidates.append({
            "chunk_id": chunk_id,
            "text": doc,
            "source": meta["source"],
            "book": meta["book"],
            "verses": meta["verses"],
            "reference": meta["reference"],
            "principles": sorted(chunk_principles),
            "raw_distance": dist,
            "adjusted_score": adjusted_score,
        })

    candidates.sort(key=lambda c: c["adjusted_score"])
    return query_principles, candidates[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Is it wrong for an AI system to collect more personal data than it needs?",
        "Should a hiring algorithm's decisions be explainable to the applicant?",
        "Is it okay for a recommendation system to be designed to be addictive?",
        "Should a chatbot ever overstate what it's actually capable of?",
        "When should a human take over from an automated decision?",
    ]
    for q in test_queries:
        principles, hits = retrieve(q, top_k=1)
        top = hits[0]
        print(f"Q: {q}")
        print(f"  detected principles: {sorted(principles) or 'none'}")
        print(f"  top hit: {top['chunk_id']} tags={top['principles']} "
              f"(raw={top['raw_distance']:.3f}, adjusted={top['adjusted_score']:.3f})")
        print(f"  text: {top['text'][:140].strip()}...")
        print()
