import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src" / "rag", ROOT / "src" / "scorecard"):
    sys.path.insert(0, str(p))
