"""
Load chunks and embedding vectors from Data Phase artifacts.
"""

import json
from pathlib import Path

import numpy as np

from config import CHUNKS_PATH, VECTORS_PATH


def load_chunks(path: Path | None = None) -> list[dict]:
    """Load chunks from chunks.json. Each item: chunk_id, text, fund_name, source_url, statement_url."""
    p = path or CHUNKS_PATH
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["chunks"]


def load_vectors(path: Path | None = None) -> np.ndarray:
    """Load embedding vectors (float32, shape (n_chunks, dim))."""
    p = path or VECTORS_PATH
    return np.load(p)


def load_store(chunks_path: Path | None = None, vectors_path: Path | None = None) -> tuple[list[dict], np.ndarray]:
    """Load chunks and vectors. Order of chunks must match rows of vectors."""
    chunks = load_chunks(chunks_path)
    vectors = load_vectors(vectors_path)
    if len(chunks) != len(vectors):
        raise ValueError(f"Chunk count {len(chunks)} != vector count {len(vectors)}")
    return chunks, vectors
