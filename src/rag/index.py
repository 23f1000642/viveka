"""Embed every chunk from chunk.py and write the vectors and text to the
on-disk index in data/index/ (see vectorstore.py). This is what retriever.py
searches: build it once, then retriever.py just queries it.

    python src/rag/index.py                  full build: embeds every chunk
                                             (~8 minutes on the free Voyage tier)
    python src/rag/index.py --metadata-only  refresh metadata (e.g. a new
                                             `reference` field) and keep the
                                             existing vectors; fails if any
                                             chunk's text changed

The index is small (about 1 MB) and is committed to the repo, so a fresh
checkout or a deployed copy of the app can search straight away without
re-running the embedding job.
"""
import json
import sys
from pathlib import Path

from embeddings import embed_texts
from vectorstore import INDEX_DIR, save, update_metadata

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"


def load_chunks():
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_metadata(chunk: dict) -> dict:
    # verses/principles stay comma-joined strings: retriever.py was written
    # against that shape (it was a ChromaDB restriction originally) and
    # nothing gained by changing it.
    return {
        "source": chunk["source"],
        "book": chunk["book"] or "",
        "verses": ",".join(chunk["verses"]),
        "principles": ",".join(chunk["principles"]),
        "reference": chunk["reference"],
    }


def main():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    if "--metadata-only" in sys.argv:
        update_metadata({c["chunk_id"]: (c["text"], build_metadata(c)) for c in chunks})
        print(f"Updated metadata for {len(chunks)} chunks; vectors unchanged")
        return

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks via Voyage AI (input_type=document)...")
    embeddings = embed_texts(texts, input_type="document")

    save([c["chunk_id"] for c in chunks], texts, [build_metadata(c) for c in chunks], embeddings)
    print(f"Indexed {len(chunks)} chunks at {INDEX_DIR}")


if __name__ == "__main__":
    main()
