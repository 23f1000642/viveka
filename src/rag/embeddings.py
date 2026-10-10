"""Shared helper for calling the Voyage AI embeddings API. Used by both
index.py (embedding the corpus) and retriever.py (embedding a user's
query) so the two never accidentally drift out of sync on model or API
version — they share one function instead of two copies of the same code.

Switched to a hosted embedding API instead of a local model
(sentence-transformers/torch) because the local install triggered a
Windows Application Control policy that blocked scikit-learn's compiled
DLL outright — not something this project should work around by touching
the machine's security settings. An API call needs nothing but `requests`.
"""
import os
import time

import requests
from dotenv import load_dotenv

from errors import ConfigError

load_dotenv()

API_URL = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-3-lite"
# A free Voyage account with no payment method on file is capped at 3
# requests/minute and 10K tokens/minute (Voyage returns this in an
# x-api-warning header). A small batch size and a pause between requests
# keeps us under both limits instead of just hoping we don't hit them.
BATCH_SIZE = 20
SECONDS_BETWEEN_REQUESTS = 21
MAX_RETRIES = 4


def _api_key() -> str:
    key = os.environ.get("VOYAGE_API_KEY")
    if not key:
        raise ConfigError(
            "VOYAGE_API_KEY not set. Create a .env file in the project root "
            "with a line: VOYAGE_API_KEY=your-key-here (see .env.example)."
        )
    return key


def _embed_batch(batch: list[str], input_type: str, headers: dict) -> list[list[float]]:
    delay = SECONDS_BETWEEN_REQUESTS
    for attempt in range(1, MAX_RETRIES + 1):
        resp = requests.post(
            API_URL,
            headers=headers,
            json={"input": batch, "model": MODEL, "input_type": input_type},
            timeout=60,
        )
        if resp.status_code == 429:
            if attempt == MAX_RETRIES:
                resp.raise_for_status()
            wait = int(resp.headers.get("Retry-After", delay))
            print(f"  rate-limited, waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]
    raise RuntimeError("unreachable")


def embed_texts(texts: list[str], input_type: str = "document") -> list[list[float]]:
    """input_type='document' for corpus chunks (index.py), 'query' for a
    user's question (retriever.py) — Voyage embeds these two differently
    ("asymmetric" embedding), which measurably improves retrieval quality
    over embedding both the same way."""
    headers = {"Authorization": f"Bearer {_api_key()}"}
    all_embeddings: list[list[float]] = []
    num_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(texts), BATCH_SIZE), start=1):
        batch = texts[i:i + BATCH_SIZE]
        print(f"  batch {batch_num}/{num_batches} ({len(batch)} texts)...")
        all_embeddings.extend(_embed_batch(batch, input_type, headers))
        if batch_num < num_batches:
            time.sleep(SECONDS_BETWEEN_REQUESTS)
    return all_embeddings
