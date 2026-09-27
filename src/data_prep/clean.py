"""Strip Project Gutenberg boilerplate from each raw text and split what's
left into small, tagged records (source, book, verse, text) that chunk.py
(Day 4) will later group into retrieval chunks.
"""
import json
import re
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

SOURCES = {
    "gita_arnold_raw.txt": "gita_arnold",
    "yogasutras_johnston_raw.txt": "yoga_sutras_johnston",
    "upanishads_paramananda_raw.txt": "upanishads_paramananda",
}

START_RE = re.compile(r"\*\*\*\s*START OF (THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE | re.DOTALL)
END_RE = re.compile(r"\*\*\*\s*END OF (THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*", re.IGNORECASE | re.DOTALL)

BOOK_RE = re.compile(r"^(BOOK|Book)\s+[IVXLC]+\.?\s*$")
VERSE_RE = re.compile(r"^(\d{1,3})\.\s+(.*)$", re.DOTALL)
SKIP_RE = re.compile(r"^(Produced by|Transcriber|Etext prepared by)", re.IGNORECASE)


def strip_boilerplate(text: str) -> str:
    """Cut everything before the START marker and after the END marker —
    every Gutenberg ebook wraps its actual content in these two lines."""
    start = START_RE.search(text)
    end = END_RE.search(text)
    body = text[start.end():end.start()] if start and end else text
    return body.strip("\n")


def split_records(body: str, source: str):
    """Split into blank-line-separated paragraphs. A paragraph starting
    with a number ("35. ...") is treated as a numbered verse/sutra; anything
    else gets a sequential paragraph id instead, since not every translator
    numbers their text."""
    records = []
    current_book = None
    para_index = 0
    for para in re.split(r"\n\s*\n", body):
        para = " ".join(line.strip() for line in para.splitlines()).strip()
        if not para or SKIP_RE.match(para):
            continue
        if BOOK_RE.match(para):
            current_book = para.title()
            continue
        m = VERSE_RE.match(para)
        if m:
            verse, rest = m.group(1), m.group(2)
        else:
            para_index += 1
            verse, rest = f"p{para_index}", para
        records.append({
            "source": source,
            "book": current_book,
            "verse": verse,
            "text": rest,
        })
    return records


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, source in SOURCES.items():
        raw_path = RAW_DIR / filename
        text = raw_path.read_text(encoding="utf-8")
        body = strip_boilerplate(text)
        records = split_records(body, source)

        out_path = OUT_DIR / f"{source}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        print(f"{source}: {len(records)} records -> {out_path}")


if __name__ == "__main__":
    main()
