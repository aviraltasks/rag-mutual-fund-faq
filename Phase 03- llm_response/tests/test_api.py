"""
Phase 03 - LLM Response: API tests.
Run from Phase 03- llm_response: pytest tests/ -v
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


def test_answer_requires_query():
    r = client.post("/answer", json={"chunks": []})
    assert r.status_code == 422


def test_answer_with_empty_chunks():
    r = client.post("/answer", json={"query": "What is the lock in?", "chunks": []})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "citation_url" in data
    assert "last_updated_note" in data
    assert data["citation_url"] == ""


def test_answer_with_chunks_returns_citation():
    payload = {
        "query": "What is the lock in for ELSS?",
        "chunks": [
            {
                "chunk_id": "c1",
                "text": "SBI ELSS Tax Saver Fund. Lock In: 3 Years.",
                "fund_name": "SBI ELSS Tax Saver Fund",
                "source_url": "https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth-2754",
                "statement_url": "https://www.sbimf.com/elss",
            }
        ],
    }
    r = client.post("/answer", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["citation_url"] == "https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth-2754"
    assert "Last updated" in data["last_updated_note"]
