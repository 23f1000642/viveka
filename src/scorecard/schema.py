"""The Ethics Scorecard's data contract: a 1-5 score, a one-line rationale,
and a suggested mitigation for each of the seven principles. score.py
(Day 14) uses this both to build the prompt and to validate what the model
returns — a scorecard that fails validation gets retried rather than shown
to a user as if it were trustworthy.
"""
from jsonschema import Draft7Validator

PRINCIPLES = ["ahimsa", "satya", "dharma", "nyaya", "aparigraha", "seva", "viveka"]

# Anchors for what each score means — without these, "3/5" is meaningless
# and two runs of the same model could score the same feature differently
# for no principled reason.
SCORE_SCALE = {
    1: "Clear violation — significant risk, no meaningful safeguard evident",
    2: "Concerning — meaningful risk, safeguards are weak or incomplete",
    3: "Mixed — some real alignment, but notable gaps remain",
    4: "Mostly aligned — only minor concerns, well short of a violation",
    5: "Strongly aligned — no significant concern identified",
}

SCORECARD_SCHEMA = {
    "type": "object",
    "required": ["scores", "overall_summary"],
    "properties": {
        "scores": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "required": ["principle", "evidence", "score", "rationale", "mitigation"],
                "properties": {
                    "principle": {"type": "string", "enum": PRINCIPLES},
                    "evidence": {"type": "string", "minLength": 3},
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "rationale": {"type": "string"},
                    "mitigation": {"type": "string"},
                },
            },
        },
        "overall_summary": {"type": "string"},
    },
}

# The v1 eval showed the model scoring a principle 3 with "the description
# says nothing about fairness" when the description stated a fairness
# problem outright, and flagging ~5 of 7 principles on most bad features.
# `evidence` makes the model point at the exact words behind each score, and
# validate_scorecard() checks the quote really is in the description.
NO_EVIDENCE = "none stated"


def _norm(text: str) -> str:
    for old, new in (("‑", "-"), ("‐", "-"), ("–", "-"), ("—", "-"),
                     ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"')):
        text = text.replace(old, new)
    return " ".join(text.lower().split())


def validate_scorecard(data: dict, description: str | None = None) -> list[str]:
    """Returns a list of problems (empty means valid). Returns errors
    instead of raising so score.py can decide whether to retry the model
    call or surface the error, rather than crashing on a malformed
    response or — worse — silently showing the user a broken scorecard.

    Pass the feature `description` to also check each score's evidence:
    "none stated" is only allowed with a score of exactly 3, and anything
    else must be a verbatim quote from the description."""
    errors = [e.message for e in Draft7Validator(SCORECARD_SCHEMA).iter_errors(data)]
    entries = [s for s in data.get("scores", []) if isinstance(s, dict)]
    missing = set(PRINCIPLES) - {s.get("principle") for s in entries}
    if missing:
        errors.append(f"missing principles: {sorted(missing)}")
    if description is not None:
        haystack = _norm(description)
        for s in entries:
            evidence = s.get("evidence")
            if not isinstance(evidence, str):
                continue
            name = s.get("principle")
            if _norm(evidence) == NO_EVIDENCE:
                if s.get("score") != 3:
                    errors.append(f"{name}: evidence is '{NO_EVIDENCE}' so the score must be 3")
            elif _norm(evidence) not in haystack:
                errors.append(f"{name}: evidence is not a verbatim quote from the description")
    return errors
