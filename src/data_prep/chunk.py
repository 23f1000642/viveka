"""Group the verse/paragraph-level records from clean.py into small
multi-verse chunks, and tag each chunk with candidate principles using
keyword matching. These tags are a first pass ("weak supervision") — Day 5
hand-reviews a sample and fixes the mistakes before anything gets trusted.
"""
import json
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
    "dharma": ["duty", "dharma", "righteous", "obligation"],
    "nyaya": ["justice", "judge", "judgment", "law", "punish"],
    "aparigraha": ["greed", "covet", "possess", "desire", "attachment", "renunciation", "aparigraha"],
    "seva": ["service", "serve", "welfare", "sacrifice", "selfless", "seva"],
    "viveka": ["discrimination", "discern", "wisdom", "knowledge", "ignorance", "viveka"],
}


def tag_principles(text: str):
    lowered = text.lower()
    return [p for p, keywords in PRINCIPLE_KEYWORDS.items() if any(k in lowered for k in keywords)]


def load_records(filename: str):
    path = PROCESSED_DIR / filename
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


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
            chunks.append({
                "chunk_id": f"{source}:{batch[0]['verse']}-{batch[-1]['verse']}",
                "source": source,
                "book": book,
                "verses": [r["verse"] for r in batch],
                "text": text,
                "principles": tag_principles(text),
            })
    return chunks


def main():
    all_chunks = []
    for filename in SOURCE_FILES:
        records = load_records(filename)
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
