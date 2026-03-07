"""
Tests for the retrieval API (FastAPI).
Run from Phase 02- backend: pytest tests/ -v
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_retrieve_requires_query():
    r = client.post("/retrieve", json={})
    assert r.status_code == 422  # validation error


def test_retrieve_accepts_valid_body():
    r = client.post("/retrieve", json={"query": "What is the minimum SIP for ELSS?"})
    assert r.status_code == 200
    data = r.json()
    assert "chunks" in data
    assert "total" in data
    assert isinstance(data["chunks"], list)
    assert data["total"] == len(data["chunks"])
    if data["chunks"]:
        c = data["chunks"][0]
        assert "chunk_id" in c and "text" in c and "fund_name" in c
        assert "source_url" in c and "statement_url" in c and "score" in c


def test_retrieve_respects_top_k():
    r = client.post("/retrieve", json={"query": "expense ratio", "top_k": 2})
    assert r.status_code == 200
    assert len(r.json()["chunks"]) <= 2


def test_retrieve_empty_query_rejected():
    r = client.post("/retrieve", json={"query": ""})
    assert r.status_code == 422
