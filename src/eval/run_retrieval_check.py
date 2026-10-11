"""Does the app's retrieval surface the Arthashastra when asked about justice,
and does it leave it out when asked about something else?

The Arthashastra chapters were ingested to give the Nyaya principle a real
source. Ingesting a text does nothing if retrieval never returns it. This
runs a small hand-written query set at several values of the retriever's
principle-tag boost and counts how many of the top 5 passages come from the
Arthashastra.

Both query sets and the idea of what counts as "justice" are my own, so this
is a sanity check on direction, not a benchmark. It costs one embedding call.
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "rag"))

from embeddings import embed_texts  # noqa: E402
from retriever import retrieve  # noqa: E402

JUSTICE = [
    "Should a person affected by an automated decision be able to contest it?",
    "Should an algorithm be penalised in proportion to the harm it caused, and impartially?",
    "Should a hiring algorithm's decisions be explainable to the applicant?",
    "Who should be able to review and overturn a decision made by an automated system?",
    "Is it fair to deny someone a loan without telling them the reason?",
    "Should evidence be examined before an AI system's accusation is accepted as true?",
    "Who judges the system when it wrongly flags an innocent person?",
    "Should the same rules apply impartially to a powerful customer and an ordinary one?",
]
CONTROLS = [  # not about justice: the Arthashastra should mostly stay out of these
    "Is it okay for a recommendation system to be designed to be addictive?",
    "Should a chatbot ever overstate what it's actually capable of?",
    "Is it wrong for an AI system to collect more personal data than it needs?",
    "Should a company test its AI for harms before releasing it?",
    "Should an AI product hide from customers that it is an AI?",
    "Should apps serve users' real goals rather than maximise screen time?",
]
BOOSTS = [0.0, 0.1, 0.25]


def arthashastra_in_top5(query, vector, boost):
    _, hits = retrieve(query, top_k=5, boost=boost, query_vector=vector)
    return sum(h["source"] == "arthashastra_shamasastry" for h in hits)


def main():
    queries = JUSTICE + CONTROLS
    vectors = embed_texts(queries, input_type="query")  # one request
    vec = dict(zip(queries, vectors))

    print(f"{'boost':>6} | justice queries with >=1 Arthashastra in top 5 | mean per query | controls: mean Arthashastra per query")
    for boost in BOOSTS:
        j = [arthashastra_in_top5(q, vec[q], boost) for q in JUSTICE]
        c = [arthashastra_in_top5(q, vec[q], boost) for q in CONTROLS]
        print(f"{boost:>6} | {sum(n >= 1 for n in j)} of {len(JUSTICE)}"
              f"{'':<34}| {sum(j) / len(j):.2f}{'':<9}| {sum(c) / len(c):.2f}   (per-query: {c})")


if __name__ == "__main__":
    main()
