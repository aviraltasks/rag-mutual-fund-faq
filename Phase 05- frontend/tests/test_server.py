"""
Phase 05 - Frontend: server tests (health, static, /chat with mocked backends).
Run from Phase 05- frontend: pytest tests/ -v
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_last_updated_returns_note():
    """GET /last-updated returns last_updated_note so footer can show date/time on load."""
    r = client.get("/last-updated")
    assert r.status_code == 200
    data = r.json()
    assert "last_updated_note" in data
    note = data["last_updated_note"]
    assert note and "Last Updated On" in note
    assert any(c.isdigit() for c in note), "must contain a date/time (digit)"


def test_index_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "Mutual Fund FAQ Assistant" in r.text


def test_static_assets():
    r = client.get("/static/styles.css")
    assert r.status_code == 200
    r = client.get("/static/app.js")
    assert r.status_code == 200


def test_chat_requires_query():
    r = client.post("/chat", json={})
    assert r.status_code == 422


def test_chat_refusal_when_safety_disallows():
    """When safety service returns allowed=False, /chat returns refusal (mocked)."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        if "check" in str(url):
            return MockResponse(200, {"allowed": False, "refusal_message": "I'm here only for factual info.", "educational_link": None})
        raise Exception("unexpected call")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "Should I invest in ELSS?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is True
    assert data.get("message")
    assert data.get("educational_link") is None  # Facts-only; no investor education link


def test_chat_full_flow_factual_answer_with_mocked_backends():
    """All phases together (mocked): Safety allows -> Retrieve returns chunks -> LLM returns answer -> /chat returns answer + citation."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    call_count = [0]

    async def mock_post(url, **kwargs):
        call_count[0] += 1
        url_s = str(url)
        if "8002" in url_s or "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "8000" in url_s or "retrieve" in url_s:
            return MockResponse(200, {
                "chunks": [
                    {
                        "chunk_id": "c1",
                        "text": "Expense ratio: 0.89%\n\nLock In: 3 Years",
                        "fund_name": "SBI ELSS",
                        "source_url": "https://indmoney.com/elss",
                        "statement_url": "https://sbimf.com/elss",
                        "score": 0.9,
                    }
                ],
                "total": 1,
            })
        if "8001" in url_s or "answer" in url_s:
            return MockResponse(200, {
                "answer": "The expense ratio of SBI ELSS Tax Saver Fund is 0.89%.",
                "citation_url": "https://indmoney.com/elss",
                "last_updated_note": "Last Updated On 06 Mar 2025",
            })
        raise Exception(f"unexpected url: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "What is the expense ratio of SBI ELSS Tax Saver Fund?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is not True
    assert "answer" in data and len(data["answer"]) > 0
    assert "citation_url" in data
    note = data.get("last_updated_note", "")
    assert note, "last_updated_note must be non-empty"
    assert "Last Updated On" in note, "last_updated_note must contain 'Last Updated On'"
    assert any(c.isdigit() for c in note), "last_updated_note must contain a date/time (digit), not placeholder like —"
    assert "0.89" in data["answer"] or "expense" in data["answer"].lower()


def test_chat_response_cache_returns_same_for_repeated_query():
    """Repeated same query gets same response from cache (no extra backend calls)."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    call_count = [0]

    async def mock_post(url, **kwargs):
        call_count[0] += 1
        url_s = str(url)
        if "8002" in url_s or "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "8000" in url_s or "retrieve" in url_s:
            return MockResponse(200, {
                "chunks": [{"chunk_id": "c1", "text": "NAV: 120.50", "fund_name": "SBI Flexicap", "source_url": "https://x.com", "statement_url": ""}],
                "total": 1,
            })
        if "8001" in url_s or "answer" in url_s:
            return MockResponse(200, {"answer": "The NAV is 120.50.", "citation_url": "https://x.com", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    query = "What is the NAV of SBI Flexicap Fund?"
    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r1 = client.post("/chat", json={"query": query})
        r2 = client.post("/chat", json={"query": query})
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert d1.get("answer") == d2.get("answer")
    assert d1.get("citation_url") == d2.get("citation_url")
    assert d1.get("refusal") == d2.get("refusal")
    # First request triggers 3 backend calls (safety, retrieve, LLM); second is cache hit
    assert call_count[0] == 3, "Second request should be served from cache (no extra backend calls)"


def test_chat_unsupported_fund_returns_clear_message():
    """When user asks about a fund we don't have (e.g. ICICI), return clear message without wrong data."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        raise Exception("Retrieve should not be called for unsupported fund")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "What is NAV of ICICI large cap fund?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is not True
    assert "don't have that fund" in data.get("answer", "").lower() or "only cover" in data.get("answer", "").lower()
    assert "SBI" in data.get("answer", "")


def test_chat_empty_chunks_returns_clear_message():
    """When retrieval returns no chunks, /chat returns helpful message without calling LLM."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {"chunks": [], "total": 0})
        raise Exception("LLM should not be called when chunks are empty")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "What is the expense ratio of XYZ Unknown Fund?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is not True
    assert "No matching data" in data.get("answer", "") or "include the scheme name" in data.get("answer", "").lower()
    note = data.get("last_updated_note", "")
    assert note and "Last Updated On" in note, "last_updated_note must be present and contain date label"
    assert "suggested_query" in data and data["suggested_query"], "failure response must include suggested_query for try typing"


def test_chat_no_info_from_llm_includes_suggested_query():
    """When LLM returns no-info answer, response includes suggested_query for try typing."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {"chunks": [{"text": "Some text.", "source_url": "https://x.com", "chunk_id": "1"}], "total": 1})
        if "answer" in url_s:
            return MockResponse(200, {"answer": "I don't have that information in my sources.", "citation_url": "", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "kaun he manager SBI large cap ka?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "don't have that information" in data.get("answer", "").lower()
    assert data.get("suggested_query"), "no-info response must include suggested_query"
    assert "manager" in data["suggested_query"].lower() or "SBI" in data["suggested_query"]


def test_failure_lock_period_sbi_fof_returns_suggested_adjacent_query():
    """Failure: 'what is lock period for SBI FOF?' returns suggested_query (adjacent question)."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {"chunks": [], "total": 0})
        raise Exception("LLM should not be called when chunks are empty")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "what is lock period for SBI FOF ?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "No matching data" in data.get("answer", "") or "don't have" in data.get("answer", "").lower()
    assert data.get("suggested_query"), "failure must include suggested_query"
    assert "lock-in" in data["suggested_query"].lower() or "lock" in data["suggested_query"].lower()
    assert "SBI" in data["suggested_query"] and ("FoF" in data["suggested_query"] or "US" in data["suggested_query"])


def test_failure_hinglish_manager_returns_suggested_adjacent_query():
    """Failure: 'kaun he manager SBI large cap ka?' returns suggested_query (English adjacent question)."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {"chunks": [{"text": "Other content.", "source_url": "https://x.com", "chunk_id": "1"}], "total": 1})
        if "answer" in url_s:
            return MockResponse(200, {"answer": "I don't have that information in my sources.", "citation_url": "", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "kaun he manager SBI large cap ka?"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "don't have that information" in data.get("answer", "").lower()
    assert data.get("suggested_query"), "failure must include suggested_query"
    assert "manager" in data["suggested_query"].lower()
    assert "SBI" in data["suggested_query"] and "Large Cap" in data["suggested_query"]


def test_suggested_lock_in_query_succeeds():
    """Using suggested adjacent question for lock-in: sending it returns success (no failure, no suggested_query)."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {
                "chunks": [{
                    "chunk_id": "c1",
                    "text": "Lock In: No Lock-in\n\nMinimum SIP: --",
                    "source_url": "https://indmoney.com/us-fof",
                    "statement_url": "",
                    "fund_name": "SBI US Specific Equity Active FoF Fund",
                }],
                "total": 1,
            })
        if "answer" in url_s:
            return MockResponse(200, {"answer": "The Lock-in period is No Lock-in.", "citation_url": "https://indmoney.com/us-fof", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    suggested = "What is the lock-in period for SBI US Specific Equity Active FoF Fund?"
    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": suggested})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is not True
    assert "No Lock-in" in data.get("answer", "") or "lock-in" in data.get("answer", "").lower()
    assert "don't have that information" not in data.get("answer", "").lower()
    assert data.get("suggested_query") is None or data.get("suggested_query") == ""


def test_suggested_fund_manager_query_succeeds():
    """Using suggested adjacent question for fund manager: sending it returns success with manager name."""
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            return MockResponse(200, {
                "chunks": [{
                    "chunk_id": "c1",
                    "text": "Fund Manager: Saurabh Pant\n\nHow Do I Invest: 1. Download the app.",
                    "source_url": "https://indmoney.com/largecap",
                    "statement_url": "",
                    "fund_name": "SBI Large Cap Fund",
                }],
                "total": 1,
            })
        if "answer" in url_s:
            return MockResponse(200, {"answer": "The Fund manager is Saurabh Pant.", "citation_url": "https://indmoney.com/largecap", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    suggested = "Who is the fund manager of SBI Large Cap Fund?"
    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": suggested})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("refusal") is not True
    assert "Saurabh Pant" in data.get("answer", "")
    assert "don't have that information" not in data.get("answer", "").lower()
    assert data.get("suggested_query") is None or data.get("suggested_query") == ""


def test_chat_sends_expanded_query_to_retrieval():
    """Orchestrator sends expanded (canonical) query to retrieval, not raw abbreviated input."""
    retrieve_request = []

    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
        def json(self):
            return self._json

    async def mock_post(url, **kwargs):
        url_s = str(url)
        if "check" in url_s:
            return MockResponse(200, {"allowed": True, "refusal_message": None, "educational_link": None})
        if "retrieve" in url_s:
            retrieve_request.append(kwargs.get("json") or {})
            return MockResponse(200, {
                "chunks": [{"chunk_id": "c1", "text": "Fund Manager: Saurabh Pant.", "fund_name": "SBI Large Cap Fund", "source_url": "https://x.com", "statement_url": ""}],
                "total": 1,
            })
        if "answer" in url_s:
            return MockResponse(200, {"answer": "The fund manager is Saurabh Pant.", "citation_url": "https://x.com", "last_updated_note": "Last Updated On 01 Jan 2025"})
        raise Exception(f"unexpected: {url_s}")

    mock_instance = AsyncMock()
    mock_instance.post = mock_post
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_instance
    mock_client.__aexit__.return_value = None

    with patch("server.app.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/chat", json={"query": "sb lar cap manager"})
    assert r.status_code == 200, r.text
    assert len(retrieve_request) == 1, "retrieve must be called once"
    query_sent = retrieve_request[0].get("query", "")
    assert "Who is the fund manager of SBI Large Cap Fund" in query_sent, (
        f"retrieval must receive expanded query, got: {query_sent!r}"
    )
    assert "sb lar cap" not in query_sent or "SBI Large Cap Fund" in query_sent, (
        "retrieval should get canonical question, not raw abbreviation"
    )
