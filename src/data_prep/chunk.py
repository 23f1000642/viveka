"""Group the verse/paragraph-level records from clean.py into small
multi-verse chunks, and tag each chunk with candidate principles using
keyword matching. These tags are a first pass ("weak supervision") — Day 5
hand-reviews a sample and fixes the mistakes before anything gets trusted.
"""
import json
import re
from pathlib import Path
from itertools import groupby

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
CHUNK_SIZE = 3

SOURCE_FILES = [
    "gita_arnold.jsonl",
    "yoga_sutras_johnston.jsonl",
    "upanishads_paramananda.jsonl",
]

# Keyword lexicon for weak-supervision tagging. Matching is a case-insensitive
# substring check against the chunk text — deliberately simple, deliberately
# noisy. Day 5 exists specifically to correct what this gets wrong.
PRINCIPLE_KEYWORDS = {
    "ahimsa": ["non-injury", "noninjury", "harm", "hurt", "injur", "violence", "cruel", "kill"],
    "satya": ["truth", "false", "falsehood", "lie", "lying", "honest", "deceit", "untrue"],
    "dharma": ["duty", "dharma", "righteous", "obligation", "task", "one's own work", "own work"],
    "nyaya": ["justice", "judge", "judgment", "law", "punish"],
    "aparigraha": ["greed", "covet", "possess", "desire", "attachment", "renunciation", "aparigraha"],
    "seva": ["service", "serve", "welfare", "sacrifice", "selfless", "seva"],
    "viveka": ["discrimination", "discern", "ignorance", "viveka"],
}


def tag_principles(text: str):
    lowered = text.lower()
    return [p for p, keywords in PRINCIPLE_KEYWORDS.items() if any(k in lowered for k in keywords)]


def load_records(filename: str):
    path = PROCESSED_DIR / filename
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


CHAPTER_RE = re.compile(r"^CHAPTER ([IVXLC]+)$")
UPANISHAD_HEADINGS = {"Isa-Upanishad", "Katha-Upanishad", "Kena-Upanishad"}


def assign_sections(records):
    """Walk a source's records in order and tag each with the chapter (Gita)
    or Upanishad it sits in, switching whenever a heading record appears.
    This only annotates records; chunk boundaries and ids are untouched."""
    section = None
    for r in records:
        text = r["text"].strip()
        if r["source"] == "gita_arnold":
            m = CHAPTER_RE.match(text)
            if m:
                section = f"Chapter {m.group(1)}"
        elif r["source"] == "upanishads_paramananda" and text in UPANISHAD_HEADINGS:
            section = text.replace("-", " ")
        r["section"] = section
    return records


def _format_numbers(nums: list[int]) -> str:
    if nums == list(range(nums[0], nums[-1] + 1)):
        return str(nums[0]) if len(nums) == 1 else f"{nums[0]}-{nums[-1]}"
    return ", ".join(map(str, nums))


def build_reference(source: str, book, sections: list, verses: list) -> str:
    """A reference a reader could look up, built only from structure the
    cleaning step really found. The `pNN` verse ids are this project's own
    paragraph counters, not positions in any printed edition, so they never
    appear here."""
    if source == "yoga_sutras_johnston":
        label = "Book " + book.split()[1].upper() if book else "Introduction"
        nums = sorted(int(v) for v in verses if v.isdigit())
        if not nums or not book:
            return f"{label}, commentary" if book else label
        noun = "sutra" if len(nums) == 1 else "sutras"
        has_commentary = any(not v.isdigit() for v in verses)
        return f"{label}, {noun} {_format_numbers(nums)}" + (" with commentary" if has_commentary else "")
    present = list(dict.fromkeys(s for s in sections if s))
    return " to ".join(present) if present else "Introduction"


def make_chunks(records):
    chunks = []
    # Group consecutive records by (source, book) so a chunk never crosses
    # a book boundary — an Ahimsa chunk shouldn't accidentally splice in a
    # sentence from an unrelated book.
    for (source, book), group in groupby(records, key=lambda r: (r["source"], r["book"])):
        group = list(group)
        for i in range(0, len(group), CHUNK_SIZE):
            batch = group[i:i + CHUNK_SIZE]
            text = " ".join(r["text"] for r in batch)
            book_tag = (book or "intro").replace(" ", "_").lower()
            chunks.append({
                "chunk_id": f"{source}:{book_tag}:{batch[0]['verse']}-{batch[-1]['verse']}",
                "source": source,
                "book": book,
                "verses": [r["verse"] for r in batch],
                "reference": build_reference(
                    source, book, [r.get("section") for r in batch], [r["verse"] for r in batch]
                ),
                "text": text,
                "principles": tag_principles(text),
            })
    return chunks


def main():
    all_chunks = []
    for filename in SOURCE_FILES:
        records = assign_sections(load_records(filename))
        all_chunks.extend(make_chunks(records))

    out_path = PROCESSED_DIR / "chunks.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    tagged = [c for c in all_chunks if c["principles"]]
    print(f"{len(all_chunks)} chunks total, {len(tagged)} with at least one principle tag -> {out_path}")

    counts = {}
    for c in all_chunks:
        for p in c["principles"]:
            counts[p] = counts.get(p, 0) + 1
    for p, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {p}: {n}")


if __name__ == "__main__":
    main()
