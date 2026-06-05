"""
embedder.py

Reads chunks.json, creates embeddings using SentenceTransformers,
and stores them in a FAISS index.

Outputs:
    data/faiss_index.bin
    data/chunk_metadata.pkl

Usage:
    python src/embedder.py
"""

import argparse
import json
import pickle
import time
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_embedding_model():
    print(f"[embedder] Loading model: {EMBEDDING_MODEL}")
    start = time.time()

    model = SentenceTransformer(EMBEDDING_MODEL)

    elapsed = time.time() - start
    print(f"[embedder] Model loaded in {elapsed:.1f}s")

    return model


def build_faiss_index(
    input_path="data/chunks.json",
    index_path="data/faiss_index.bin",
    metadata_path="data/chunk_metadata.pkl",
):
    chunks_file = Path(input_path)

    if not chunks_file.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {chunks_file}"
        )

    chunks = json.loads(
        chunks_file.read_text(encoding="utf-8")
    )

    print(
        f"[embedder] Loaded {len(chunks)} chunks "
        f"from {chunks_file}"
    )

    texts = [chunk["text"] for chunk in chunks]

    model = load_embedding_model()

    print(
        f"[embedder] Generating embeddings "
        f"for {len(texts)} chunks..."
    )

    start = time.time()

    vectors_np = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    elapsed = time.time() - start

    print(
        f"[embedder] Generated embeddings "
        f"in {elapsed:.1f}s"
    )

    vectors_np = np.asarray(
        vectors_np,
        dtype=np.float32
    )

    embedding_dim = vectors_np.shape[1]

    print(
        f"[embedder] Embedding dimension: "
        f"{embedding_dim}"
    )

    # Cosine similarity
    index = faiss.IndexFlatIP(
        embedding_dim
    )

    index.add(vectors_np)

    print(
        f"[embedder] FAISS index built "
        f"with {index.ntotal} vectors"
    )

    Path(index_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        index_path
    )

    with open(metadata_path, "wb") as f:
        pickle.dump(chunks, f)

    print(
        f"[embedder] Saved index -> "
        f"{index_path}"
    )

    print(
        f"[embedder] Saved metadata -> "
        f"{metadata_path}"
    )

    index_size_mb = (
        Path(index_path).stat().st_size
        / (1024 * 1024)
    )

    metadata_size_kb = (
        Path(metadata_path).stat().st_size
        / 1024
    )

    print("\n[embedder] Done.")
    print(
        f"           FAISS index: "
        f"{index_size_mb:.2f} MB"
    )
    print(
        f"           Metadata: "
        f"{metadata_size_kb:.1f} KB"
    )
    print(
        f"           Chunks: "
        f"{len(chunks)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build FAISS index from transcript chunks"
    )

    parser.add_argument(
        "--input",
        default="data/chunks.json"
    )

    parser.add_argument(
        "--index",
        default="data/faiss_index.bin"
    )

    parser.add_argument(
        "--meta",
        default="data/chunk_metadata.pkl"
    )

    args = parser.parse_args()

    build_faiss_index(
        input_path=args.input,
        index_path=args.index,
        metadata_path=args.meta,
    )