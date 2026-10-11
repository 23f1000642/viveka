import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src" / "rag", ROOT / "src" / "scorecard", ROOT / "src" / "data_prep"):
    sys.path.insert(0, str(p))  # inserted at the front so our `chunk.py` wins over the stdlib module of that name
