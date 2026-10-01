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
                "required": ["principle", "score", "rationale", "mitigation"],
                "properties": {
                    "principle": {"type": "string", "enum": PRINCIPLES},
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "rationale": {"type": "string"},
                    "mitigation": {"type": "string"},
                },
            },
        },
        "overall_summary": {"type": "string"},
    },
}


def validate_scorecard(data: dict) -> list[str]:
    """Returns a list of problems (empty means valid). Returns errors
    instead of raising so score.py can decide whether to retry the model
    call or surface the error, rather than crashing on a malformed
    response or — worse — silently showing the user a broken scorecard."""
    errors = [e.message for e in Draft7Validator(SCORECARD_SCHEMA).iter_errors(data)]
    seen = {s.get("principle") for s in data.get("scores", []) if isinstance(s, dict)}
    missing = set(PRINCIPLES) - seen
    if missing:
        errors.append(f"missing principles: {sorted(missing)}")
    return errors
