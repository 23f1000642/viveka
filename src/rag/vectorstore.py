"""A small on-disk vector store, standard library only.

448 chunks do not need a database. Embeddings live in one float32 file and
the text/metadata in one JSON file; a query scans every vector. That is
about 230k multiplications, a few dozen milliseconds in plain Python.

Why not ChromaDB: it imports gRPC, whose compiled DLL this machine's
Windows Application Control policy started blocking part-way through the
project (see docs/LOG.md, Day 19). Everything here is pure Python, so there
is nothing native for a policy to block.

Distance is squared L2, the number ChromaDB returned by default, so the
boost value in retriever.py keeps the same meaning. Vectors are stored in the
machine's native byte order (little-endian on everything this runs on).
"""
import json
from array import array
from pathlib import Path

INDEX_DIR = Path(__file__).resolve().parents[2] / "data" / "index"
VECTORS_FILE = "vectors.f32"
RECORDS_FILE = "records.json"


def save(ids, documents, metadatas, embeddings, index_dir: Path = INDEX_DIR) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    dim = len(embeddings[0])
    if any(len(e) != dim for e in embeddings):
        raise ValueError("all embeddings must have the same length")
    flat = array("f")
    for e in embeddings:
        flat.extend(e)
    (index_dir / VECTORS_FILE).write_bytes(flat.tobytes())
    records = {
        "dim": dim,
        "items": [
            {"id": i, "document": d, "metadata": m}
            for i, d, m in zip(ids, documents, metadatas)
        ],
    }
    (index_dir / RECORDS_FILE).write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


def update_metadata(entries: dict[str, tuple[str, dict]], index_dir: Path = INDEX_DIR) -> None:
    """Rewrite each item's metadata without touching the vectors, so a new
    metadata field doesn't cost a full re-embedding. `entries` maps chunk id
    to (document text, new metadata). Refuses if the ids or any text differ
    from what the vectors were computed from: stale vectors would silently
    return wrong results."""
    path = index_dir / RECORDS_FILE
    records = json.loads(path.read_text(encoding="utf-8"))
    if {item["id"] for item in records["items"]} != set(entries):
        raise ValueError("chunk ids differ from the index; rebuild it with src/rag/index.py")
    for item in records["items"]:
        document, metadata = entries[item["id"]]
        if document != item["document"]:
            raise ValueError(f"text changed for {item['id']}; its vector is stale, rebuild the index")
        item["metadata"] = metadata
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")


class Store:
    def __init__(self, index_dir: Path = INDEX_DIR):
        records = json.loads((index_dir / RECORDS_FILE).read_text(encoding="utf-8"))
        self.dim: int = records["dim"]
        self.items: list[dict] = records["items"]
        self.vectors = array("f")
        self.vectors.frombytes((index_dir / VECTORS_FILE).read_bytes())
        if len(self.vectors) != self.dim * len(self.items):
            raise ValueError("index files are inconsistent; rebuild with src/rag/index.py")

    def count(self) -> int:
        return len(self.items)

    def query(self, vector: list[float], n: int) -> list[dict]:
        if len(vector) != self.dim:
            raise ValueError(f"query has {len(vector)} dims, index has {self.dim}")
        dim = self.dim
        scored = []
        for k in range(len(self.items)):
            v = self.vectors[k * dim:(k + 1) * dim]
            dist = 0.0
            for x, y in zip(vector, v):
                t = x - y
                dist += t * t
            scored.append((dist, k))
        scored.sort()
        return [
            {
                "id": self.items[k]["id"],
                "document": self.items[k]["document"],
                "metadata": self.items[k]["metadata"],
                "distance": dist,
            }
            for dist, k in scored[:n]
        ]
