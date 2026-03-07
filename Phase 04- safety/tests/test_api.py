"""
Phase 04 - Safety: API tests.
Run from Phase 04- safety: pytest tests/ -v
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_check_factual_returns_allowed():
    r = client.post("/check", json={"query": "What is the lock in for ELSS?"})
    assert r.status_code == 200
    data = r.json()
    assert data["allowed"] is True
    assert data["refusal_message"] is None
    assert data["educational_link"] is None


def test_check_advice_returns_refusal_no_link():
    r = client.post("/check", json={"query": "Should I buy SBI ELSS?"})
    assert r.status_code == 200
    data = r.json()
    assert data["allowed"] is False
    assert data["refusal_message"] is not None
    assert data["educational_link"] is None  # Facts-only; no investor education


def test_check_requires_query():
    r = client.post("/check", json={})
    assert r.status_code == 422
