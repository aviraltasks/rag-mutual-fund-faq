"""
Similarity search: embed query with same model as Data Phase, return top-k chunks by cosine similarity.
"""

import numpy as np

from config import EMBEDDING_MODEL, DEFAULT_TOP_K
from retrieval.store import load_store


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between one vector and each row of a matrix. a: (dim,), b: (n, dim)."""
    a_norm = a / (np.linalg.norm(a) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return np.dot(b_norm, a_norm)


def get_embedder():
    """Lazy-load the embedding model (same as Phase 01)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    chunks: list[dict] | None = None,
    vectors: np.ndarray | None = None,
    embedder=None,
) -> list[dict]:
    """
    Return top-k chunks most similar to the query.
    Each result: chunk_id, text, fund_name, source_url, statement_url, score (cosine similarity).
    """
    if chunks is None or vectors is None:
        chunks, vectors = load_store()
    if embedder is None:
        embedder = get_embedder()

    q_vec = embedder.encode(query, convert_to_numpy=True).astype(np.float32)
    scores = _cosine_similarity(q_vec, vectors)
    idx = np.argsort(scores)[::-1][:top_k]

    results = []
    for i in idx:
        c = chunks[i].copy()
        c["score"] = float(scores[i])
        results.append(c)
    return results
