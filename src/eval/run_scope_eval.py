"""Check scope.classify_scope against data/eval/scope_cases.jsonl.

The two errors that matter are not equally bad:
  - a personal_distress message NOT routed to the kind reply (someone
    struggling gets an AI-ethics answer or a brush-off), and
  - an in_scope question wrongly blocked (a legitimate user is turned away).
Plain accuracy hides which one happened, so they are reported separately.
"""
import json
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "rag"))

from scope import classify_scope  # noqa: E402

cases = [json.loads(line) for line in (ROOT / "data" / "eval" / "scope_cases.jsonl").open(encoding="utf-8")]

confusion = Counter()
wrong = []
for c in cases:
    try:
        got = classify_scope(c["message"])
    except Exception as e:
        got = f"ERROR ({type(e).__name__})"
    confusion[(c["expected"], got)] += 1
    if got != c["expected"]:
        wrong.append((c, got))

print(f"{len(cases) - len(wrong)} / {len(cases)} correct\n")
for (expected, got), n in sorted(confusion.items()):
    print(f"  expected {expected:<18} got {got:<18} x{n}")

missed_distress = [c for c, got in wrong if c["expected"] == "personal_distress" and got != "personal_distress"]
blocked = [c for c, got in wrong if c["expected"] == "in_scope" and got != "in_scope"]
print(f"\ndistress messages not routed to the kind reply: {len(missed_distress)}")
print(f"in-scope questions wrongly blocked:            {len(blocked)}")
for c, got in wrong:
    print(f"\n  MISS [{c['id']}] expected {c['expected']}, got {got}\n    {c['message']}")
