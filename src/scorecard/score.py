"""Score an AI feature description against the seven principles.

Retrieves classical passages once (one embedding call — the free Voyage tier
allows only 3 requests/minute, so one retrieval per principle would crawl),
asks the LLM for a scorecard as JSON, and validates it against schema.py.
A response that fails validation is sent back to the model with the exact
errors and retried, rather than shown to a user as if it were trustworthy.
"""
import json
import sys
from pathlib import Path

import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")  # model text has characters cp1252 can't print

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rag"))

from llm import API_URL, MODEL, api_key
from prompts import format_context
from retriever import retrieve
from schema import PRINCIPLES, SCORE_SCALE, validate_scorecard

MAX_TOKENS = 3000
MAX_ATTEMPTS = 3

PRINCIPLE_DEFINITIONS = {
    "ahimsa": "non-harm — was the worst realistic failure weighed against the benefit?",
    "satya": "truthfulness — does the system represent what it is and can do, honestly?",
    "dharma": "right action in context — is someone accountable, and does behavior fit the context?",
    "nyaya": "justice and right reasoning — are the data, reasoning and outcomes fair "
    "(including biased or unrepresentative training data), and can affected people "
    "inspect and contest them?",
    "aparigraha": "non-possessiveness — does it collect and keep only what the task needs?",
    "seva": "selfless service — does it serve the user's real goal rather than an engagement metric?",
    "viveka": "discernment — does a human keep the judgment call where stakes or ambiguity are high?",
}

SYSTEM_PROMPT = (
    "You are Viveka, an advisor that audits AI features using seven categories from "
    "classical Indian philosophy. Score the feature the user describes on EACH of the "
    "seven principles, 1 to 5:\n\n"
    + "\n".join(f"{k}: {v}" for k, v in SCORE_SCALE.items())
    + "\n\nThe principles:\n"
    + "\n".join(f"- {p}: {d}" for p, d in PRINCIPLE_DEFINITIONS.items())
    + "\n\nRules:\n"
    "1. For each principle, first find the words in the description that bear on it. "
    '"evidence" is an exact, contiguous quote copied from the description (under 25 '
    'words), or exactly "none stated" if nothing in the description bears on that '
    "principle.\n"
    '2. "none stated" means the score is exactly 3. Do not treat the absence of a '
    "safeguard as evidence of a risk: a safeguard that isn't mentioned is simply not "
    "stated.\n"
    "3. A score of 1-2 needs a quoted risk; a score of 4-5 needs a quoted safeguard. "
    "Score only what the quote shows.\n"
    "4. Each rationale is ONE sentence explaining how the quote bears on the principle. "
    "Cite a supplied passage like [2] only when it genuinely supports the point; "
    "classical passages are analogy, not engineering instruction.\n"
    "5. Each mitigation is one concrete, actionable change.\n"
    "6. Respond with a single JSON object and nothing else, shaped exactly like:\n"
    '{"scores": [{"principle": "ahimsa", "evidence": "exact quote or none stated", '
    '"score": 3, "rationale": "...", "mitigation": "..."}, '
    "... one entry for each of the seven principles ...], "
    '"overall_summary": "two sentences at most"}'
)


def _call_llm(messages: list[dict]) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key()}"},
        json={
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "response_format": {"type": "json_object"},
            "messages": messages,
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"] or ""


def score_feature(description: str) -> dict:
    _, chunks = retrieve(description, top_k=6)
    user_message = (
        f"Passages:\n{format_context(chunks)}\n\nAI feature to audit:\n{description}"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    problems: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = _call_llm(messages)
        try:
            scorecard = json.loads(raw)
            problems = validate_scorecard(scorecard, description)
        except json.JSONDecodeError as e:
            problems = [f"not valid JSON: {e}"]
        if not problems:
            scorecard["scores"].sort(key=lambda s: PRINCIPLES.index(s["principle"]))
            return {
                "feature": description,
                "scorecard": scorecard,
                "sources": [
                    {"n": i, "chunk_id": c["chunk_id"], "source": c["source"], "verses": c["verses"]}
                    for i, c in enumerate(chunks, start=1)
                ],
                "attempts": attempt,
            }
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": "That response failed validation: " + "; ".join(problems)
            + ". Return the corrected JSON object only.",
        })
    raise ValueError(f"scorecard still invalid after {MAX_ATTEMPTS} attempts: {problems}")


if __name__ == "__main__":
    feature = (
        "A retail-store camera system that uses facial recognition to identify known "
        "shoplifters and alert staff. Faces of all shoppers are scanned and stored for "
        "90 days. Staff see only a match alert with a confidence percentage."
    )
    result = score_feature(feature)
    print(f"Feature: {feature}\n(valid after {result['attempts']} attempt(s))\n")
    for s in result["scorecard"]["scores"]:
        print(f"{s['principle']:<11} {s['score']}/5  {s['rationale']}")
        print(f"{'':<11} fix: {s['mitigation']}")
    print(f"\nSummary: {result['scorecard']['overall_summary']}")
