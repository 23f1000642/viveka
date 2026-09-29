"""Embed every chunk from chunk.py and persist the vectors to a local
ChromaDB collection. This is the "index" that retriever.py (next) searches
against — build it once, then retriever.py just queries it.
"""
import json
from pathlib import Path

import chromadb

from embeddings import embed_texts

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"
CHROMA_DIR = PROJECT_ROOT / "data" / "processed" / "chroma"
COLLECTION_NAME = "viveka_chunks"


def load_chunks():
    with CHUNKS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks via Voyage AI (input_type=document)...")
    embeddings = embed_texts(texts, input_type="document")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Fresh index each run — chunk.py's output can change, so this script
    # is meant to be re-run from scratch, not appended to.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # Chroma metadata values must be str/int/float/bool — lists (verses,
    # principles) get joined into comma-separated strings.
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

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"Indexed {collection.count()} chunks into '{COLLECTION_NAME}' at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
