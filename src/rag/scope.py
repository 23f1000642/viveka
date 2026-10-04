"""Decide whether a message is something Viveka should answer at all.

Viveka audits the design of AI systems. A public demo will get other things
typed into it: a personal struggle, a cricket question. Without this check,
a message about feeling ignored got a verse-backed "AI ethics" reply that
talked about "breaking the cycle of attention-seeking" (see docs/LOG.md,
Day 18).

This runs first, before the rate-limited embedding call. The two non-answer
replies below are fixed text, not model output: someone who is struggling
should get a predictable, reviewed message, not whatever the model produces
that day.
"""
import json

import requests

from llm import API_URL, MODEL, api_key

CATEGORIES = ("in_scope", "personal_distress", "off_topic")

REPLIES = {
    "personal_distress": (
        "That sounds really hard, and I'm sorry you're feeling this way. I'm not the "
        "right place for it, though: I'm a tool for reasoning about how AI systems are "
        "designed, not a counsellor, and I don't want to answer you with philosophy "
        "when what you need is a person. If you can, talk to someone you trust today. "
        "If you ever feel you might hurt yourself, please contact your local emergency "
        "number or a crisis line (findahelpline.com lists them by country)."
    ),
    "off_topic": (
        "I only answer questions about the ethics of AI systems and features, for "
        "example 'Should a hiring algorithm explain its decisions to applicants?', or a "
        "description of an AI feature you want audited. That one is outside what I can "
        "help with."
    ),
}

CLASSIFIER_PROMPT = """You triage messages sent to Viveka, a tool that reasons \
about the ethics of AI systems and features (for example "Should a hiring \
algorithm explain its decisions?", or a description of an AI feature to audit).

Classify the message as exactly one of:
- "in_scope": a question about, or description of, an AI or software system: its \
design, data use, fairness, safety, transparency or oversight. If the message asks \
about an AI system, it is in_scope even when the writer mentions personal feelings \
or experiences.
- "personal_distress": the writer is mainly expressing their own emotional pain or \
personal struggle (loneliness, sadness, hopelessness, anxiety, feeling ignored) and \
is not asking about an AI system or its design.
- "off_topic": anything else (general knowledge, coding help, creative writing, \
chit-chat).

If unsure between in_scope and off_topic, choose in_scope: don't block a legitimate \
user. If unsure whether a message is personal_distress, choose personal_distress: a \
kind reply in the wrong place costs far less than ignoring someone who is struggling.

Respond with a single JSON object and nothing else: {"category": "<one of the three>"}"""


def classify_scope(message: str) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key()}"},
        json={
            "model": MODEL,
            "max_tokens": 600,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": f"Message to classify:\n<<<\n{message}\n>>>"},
            ],
        },
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"] or ""
    try:
        category = json.loads(content).get("category")
    except (json.JSONDecodeError, AttributeError):
        return "in_scope"  # fail open: an unreadable verdict shouldn't block a real question
    return category if category in CATEGORIES else "in_scope"


def check_scope(message: str) -> tuple[str, str | None]:
    """Returns (category, reply). reply is None when the message is in scope
    and should go on to the normal pipeline."""
    category = classify_scope(message)
    return category, REPLIES.get(category)


class OutOfScope(Exception):
    def __init__(self, category: str, reply: str):
        super().__init__(category)
        self.category = category
        self.reply = reply
