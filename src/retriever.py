"""
retriever.py
Handles query-time retrieval:
  1. Load FAISS index + chunk metadata from disk (cached after first load)
  2. Embed the user's query using the SAME SentenceTransformer model used in embedder.py
  3. Run cosine similarity search (FAISS IndexFlatIP on L2-normalised vectors)
  4. Return top-k chunks with their metadata

CRITICAL: The query MUST be embedded with the same model as the index.
  Index built with: SentenceTransformer("all-MiniLM-L6-v2")
  Query embedded with: SentenceTransformer("all-MiniLM-L6-v2")  ← same, always
"""

import pickle
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# Must match the model used in embedder.py — never change one without the other
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K   = 5


# ── Cached loaders (loaded once per process, reused on every query) ───────────

@lru_cache(maxsize=1)
def _load_index(index_path: str) -> faiss.Index:
    """Load and cache the FAISS index from disk."""
    path = Path(index_path)
    if not path.exists():
        raise FileNotFoundError(
            f"FAISS index not found: {path}\n"
            "Run pipeline/ingest.py first."
        )
    index = faiss.read_index(str(path))
    print(f"[retriever] FAISS index loaded — {index.ntotal} vectors")
    return index


@lru_cache(maxsize=1)
def _load_metadata(metadata_path: str) -> list[dict]:
    """Load and cache chunk metadata from disk."""
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Chunk metadata not found: {path}\n"
            "Run pipeline/ingest.py first."
        )
    with open(path, "rb") as f:
        chunks = pickle.load(f)
    print(f"[retriever] Metadata loaded — {len(chunks)} chunks")
    return chunks


@lru_cache(maxsize=1)
def _load_model(model_name: str) -> SentenceTransformer:
    """Load and cache the SentenceTransformer model."""
    print(f"[retriever] Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)


# ── Public API ────────────────────────────────────────────────────────────────

def retrieve(
    query:         str,
    top_k:         int  = DEFAULT_TOP_K,
    index_path:    str  = "data/faiss_index.bin",
    metadata_path: str  = "data/chunk_metadata.pkl",
    model_name:    str  = EMBEDDING_MODEL,
) -> list[dict]:
    """
    Retrieves the top-k most relevant chunks for a given query.

    Args:
        query:         The user's question (plain text)
        top_k:         Number of chunks to return (default 5)
        index_path:    Path to faiss_index.bin
        metadata_path: Path to chunk_metadata.pkl
        model_name:    SentenceTransformer model name — must match embedder.py

    Returns:
        List of chunk dicts, sorted by relevance (most relevant first).
        Each dict contains: chunk_id, start_sec, end_sec, text,
                            youtube_id, youtube_url, score
    """
    # Load cached resources
    index    = _load_index(index_path)
    metadata = _load_metadata(metadata_path)
    model    = _load_model(model_name)

    # Embed the query — task is "retrieval_query" conceptually but
    # SentenceTransformer doesn't distinguish; just encode and normalise
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)  # must normalise to match index vectors

    # Search
    scores, indices = index.search(query_vec, top_k)

    # Build results — filter out any -1 indices (FAISS returns -1 for empty slots)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = dict(metadata[idx])   # copy so we don't mutate the cached list
        chunk["score"] = round(float(score), 4)
        results.append(chunk)

    return results


def format_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a prompt-ready context string.
    Each chunk is prefixed with its timestamp so the LLM can cite it.

    Example output:
        [Chunk 1 | 1:15 – 2:00]
        So the first principle is to boil things down to their fundamental truths...

        [Chunk 2 | 4:30 – 5:15]
        Elon then explains how this applies to rocket manufacturing...
    """
    from src.youtube_utils import format_source_label  # local import to avoid circular

    parts = []
    for i, chunk in enumerate(chunks, 1):
        label = format_source_label(chunk["start_sec"], chunk["end_sec"])
        parts.append(f"[Chunk {i} | {label}]\n{chunk['text']}")

    return "\n\n".join(parts)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "What does Elon say about first principles thinking?"
    print(f"\nQuery: {query}\n")

    results = retrieve(query, top_k=3)
    for i, r in enumerate(results, 1):
        from src.youtube_utils import seconds_to_timestamp
        print(f"{'─'*60}")
        print(f"#{i}  Score: {r['score']}  |  {seconds_to_timestamp(r['start_sec'])}")
        print(f"    {r['text'][:200]}...")
        print(f"    {r['youtube_url']}")