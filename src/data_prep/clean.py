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
SKIP_RE = re.compile(r"^(Produced by|Transcriber|Etext prepared by|\[FN#)", re.IGNORECASE)


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
        # Inline footnote markers ("...death-water.[FN#1]") sit inside
        # otherwise-real verse text — strip the marker, keep the verse.
        para = re.sub(r"\[FN#\d+\]", "", para).strip()
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


ARTH_FILE = "arthashastra_shamasastry_raw.txt"
ARTH_SOURCE = "arthashastra_shamasastry"
# Only the chapters about justice and procedure (why: data/raw/SOURCES.md).
# Keys are (book number, chapter numeral) in Shamasastry's numbering.
ARTH_WANTED = {(1, "II"), (1, "III"), (1, "IV"), (1, "XIX"), (3, "I")}
ARTH_BOOK_LABELS = {1: "Book I", 3: "Book III"}
ARTH_CHAPTER_RE = re.compile(r"^CHAPTER ([IVXL]+)\.")
ARTH_FOOTER_RE = re.compile(r"^\[Thus ends", re.IGNORECASE)


def clean_arthashastra(text: str):
    """The Arthashastra file is an OCR of a PDF, not a Gutenberg ebook: runs
    of spaces, "[Thus ends Chapter ...]" footers after every chapter, and
    all-caps headings. Books are not labelled in the body, but each starts
    with a "CHAPTER I." heading, so the book number is counted from those
    (and sanity-checked against the book titles below)."""
    records, book_starts = [], []
    book_no, chapter, para_index = 0, None, 0
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        m = ARTH_CHAPTER_RE.match(para)
        if m:
            chapter = m.group(1)
            if chapter == "I":
                book_no += 1
                book_starts.append(para)
            continue
        if (book_no, chapter) not in ARTH_WANTED:
            continue
        # Drop OCR scraps, footers, and all-caps title fragments.
        if len(para) < 25 or ARTH_FOOTER_RE.match(para) or para == para.upper():
            continue
        para_index += 1
        records.append({
            "source": ARTH_SOURCE,
            "book": ARTH_BOOK_LABELS[book_no],
            "chapter": chapter,
            "verse": f"p{para_index}",
            "text": para,
        })

    assert "FORMATION OF VILLAGES" in book_starts[1], "book counting is off: Book II should start here"
    assert "DETERMINATION OF FORMS" in book_starts[2], "book counting is off: Book III should start here"
    found = {(r["book"], r["chapter"]) for r in records}
    expected = {(ARTH_BOOK_LABELS[b], c) for b, c in ARTH_WANTED}
    assert found == expected, f"missing chapters: {expected - found}"
    return records


def write_jsonl(source: str, records: list) -> None:
    out_path = OUT_DIR / f"{source}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{source}: {len(records)} records -> {out_path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, source in SOURCES.items():
        text = (RAW_DIR / filename).read_text(encoding="utf-8")
        write_jsonl(source, split_records(strip_boilerplate(text), source))

    arth_text = (RAW_DIR / ARTH_FILE).read_text(encoding="utf-8")
    write_jsonl(ARTH_SOURCE, clean_arthashastra(arth_text))


if __name__ == "__main__":
    main()
