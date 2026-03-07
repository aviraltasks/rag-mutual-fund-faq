"""
Tests for retrieval: store load and similarity search.
Run from Phase 02- backend: pytest tests/ -v
"""

import sys
from pathlib import Path

# Ensure backend root is on path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
import pytest

from config import CHUNKS_PATH, VECTORS_PATH, DATA_PHASE_DIR
from retrieval.store import load_chunks, load_vectors, load_store
from retrieval.search import search, _cosine_similarity, get_embedder


@pytest.fixture(scope="module")
def chunks_and_vectors():
    """Load once per module."""
    return load_store()


def test_data_phase_artifacts_exist():
    assert DATA_PHASE_DIR.exists(), "Phase 01 data dir should exist"
    assert CHUNKS_PATH.exists(), "chunks.json should exist"
    assert VECTORS_PATH.exists(), "vectors.npy should exist"


def test_load_chunks(chunks_and_vectors):
    chunks, vectors = chunks_and_vectors
    assert len(chunks) >= 5
    first = chunks[0]
    assert "chunk_id" in first
    assert "text" in first
    assert "fund_name" in first
    assert "source_url" in first
    assert "statement_url" in first


def test_load_vectors(chunks_and_vectors):
    chunks, vectors = chunks_and_vectors
    assert vectors.dtype in (np.float32, np.float64)
    assert vectors.ndim == 2
    assert vectors.shape[0] == len(chunks)
    assert vectors.shape[1] == 384  # all-MiniLM-L6-v2


def test_cosine_similarity():
    a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    b = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    sim = _cosine_similarity(a, b)
    assert len(sim) == 2
    assert abs(sim[0] - 1.0) < 1e-5
    assert abs(sim[1]) < 1e-5


def test_search_returns_top_k(chunks_and_vectors):
    chunks, vectors = chunks_and_vectors
    results = search("What is the lock in period for ELSS?", top_k=3, chunks=chunks, vectors=vectors)
    assert len(results) == 3
    for r in results:
        assert "chunk_id" in r and "text" in r and "score" in r
        assert "source_url" in r and r["source_url"].startswith("http")
        assert r["score"] >= -1.0 and r["score"] <= 1.0


def test_search_scores_descending(chunks_and_vectors):
    chunks, vectors = chunks_and_vectors
    results = search("expense ratio and benchmark", top_k=5, chunks=chunks, vectors=vectors)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_elss_lock_in_returns_relevant_chunk(chunks_and_vectors):
    chunks, vectors = chunks_and_vectors
    results = search("ELSS lock in period", top_k=5, chunks=chunks, vectors=vectors)
    combined = " ".join(r["text"] for r in results).lower()
    assert "lock" in combined or "3 years" in combined or "elss" in combined


def test_search_expense_ratio_returns_chunk_with_expense_ratio(chunks_and_vectors):
    """Retrieval returns at least one chunk containing 'Expense ratio' for expense-ratio query."""
    chunks, vectors = chunks_and_vectors
    results = search("What is the expense ratio of SBI ELSS?", top_k=8, chunks=chunks, vectors=vectors)
    combined = " ".join(r["text"] for r in results)
    assert "Expense ratio" in combined or "expense ratio" in combined.lower(), (
        "Expected at least one chunk to contain expense ratio for ELSS query"
    )
