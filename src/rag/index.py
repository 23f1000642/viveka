"""Embed every chunk from chunk.py and write the vectors and text to the
on-disk index in data/index/ (see vectorstore.py). This is what retriever.py
searches: build it once, then retriever.py just queries it.

The index is small (about 1 MB) and is committed to the repo, so a fresh
checkout or a deployed copy of the app can search straight away without
re-running the ~8 minute embedding job.
"""
import json
from pathlib import Path

from embeddings import embed_texts
from vectorstore import INDEX_DIR, save

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"


def load_chunks():
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks via Voyage AI (input_type=document)...")
    embeddings = embed_texts(texts, input_type="document")

    # verses/principles stay comma-joined strings: retriever.py was written
    # against that shape (it was a ChromaDB restriction originally) and
    # nothing gained by changing it.
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "source": c["source"],
            "book": c["book"] or "",
            "verses": ",".join(c["verses"]),
            "principles": ",".join(c["principles"]),
        }
        for c in chunks
    ]

    save(ids, texts, metadatas, embeddings)
    print(f"Indexed {len(chunks)} chunks at {INDEX_DIR}")


if __name__ == "__main__":
    main()
