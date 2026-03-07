"""
Phase 05 - Frontend: orchestrator server.
Exposes POST /chat (calls Safety -> Retrieve -> LLM via HTTP) and serves static frontend.
Citation: one link per answer. Source URL for normal answers; Statement URL only when user asks for statements.
No citation when no mutual fund is mentioned in the query.
Response caching: in-memory LRU cache by normalized query to improve velocity for repeated questions.
"""

import os
import re
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx

from server.query_expansion import expand_query_for_retrieval

PHASE05 = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PHASE05.parent
STATIC_DIR = PHASE05 / "public"
# Phase 01 writes this when the data pipeline runs (last scraped date/time)
LAST_SCRAPED_FILE = PROJECT_ROOT / "Phase 01- data" / "last_scraped.txt"


def _last_updated_note() -> str:
    """Return 'Last Updated On <date time>' from Phase 01 last_scraped.txt, or current time. Never return placeholder."""
    try:
        if LAST_SCRAPED_FILE.exists():
            ts = LAST_SCRAPED_FILE.read_text(encoding="utf-8").strip()
            if ts:
                return f"Last Updated On {ts}"
    except Exception:
        pass
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        return f"Last Updated On {now.strftime('%d %b %Y, %I:%M %p IST')}"
    except Exception:
        pass
    now = datetime.now()
    return f"Last Updated On {now.strftime('%d %b %Y, %I:%M %p')}"

SAFETY_URL = os.getenv("SAFETY_URL", "http://127.0.0.1:8002")
RETRIEVE_URL = os.getenv("RETRIEVE_URL", "http://127.0.0.1:8000")
LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:8001")

# Fund names / keywords to detect if user is asking about a specific scheme (for citation)
FUND_KEYWORDS = [
    "sbi elss", "elss tax saver", "sbi nifty", "nifty index",
    "sbi flexicap", "flexicap", "sbi large cap", "large cap",
    "sbi us", "us specific equity", "fof fund",
]

# We only have SBI schemes. If user asks about another AMC, refuse with a clear message.
UNSUPPORTED_AMC_KEYWORDS = [
    "icici", "hdfc", "axis", "kotak", "uti", "nippon",
    "aditya birla", "birla sun", "mirae", "ppfas", "quant",
    "tata ", "idfc", "dsp ", "edelweiss", "sundaram", "l&t", "lt ",
]
COVERED_SCHEMES_LIST = (
    "SBI ELSS Tax Saver Fund, SBI Nifty Index Fund, SBI Flexicap Fund, "
    "SBI Large Cap Fund, SBI US Specific Equity Active FoF Fund."
)

STATEMENT_QUESTION_WORDS = ["download", "statement", "factsheet", "fact sheet", "documents", "kim", "sid"]

CANNED_STATEMENT_ANSWER = (
    "You can download the factsheet or statements from the link below. "
    "Open the link and go to the Documents tab on the scheme page to download."
)

# Response cache: same JSON shape, no breaking change. Key = normalized query, value = (expiry_ts, response_dict).
CACHE_MAX_SIZE = int(os.getenv("CHAT_CACHE_SIZE", "200"))
CACHE_TTL_SECONDS = int(os.getenv("CHAT_CACHE_TTL_SEC", "300"))


# Rule-based normalization: (regex_pattern, replacement) applied in order. Aligns user input with chunk phrasing for all 5 schemes.
_QUERY_NORMALIZE_RULES: list[tuple[str, str]] = [
    # AMC
    (r"\bsb\b", "sbi"),
    # Large Cap (typos, variants, former name)
    (r"\blar\s+cap\b", "large cap"),
    (r"\blargecap\b", "large cap"),
    (r"\bbluechip\b", "large cap"),
    (r"\bblue\s*chip\b", "large cap"),
    # Flexicap
    (r"\bflexicap\b", "flexi cap"),
    (r"\bflexi\s*cap\b", "flexi cap"),
    # ELSS / Tax Saver (and former name SBI Long Term Equity)
    (r"\belss\b", "elss tax saver"),
    (r"\blong\s*term\s*equity\b", "elss tax saver"),
    (r"\btax\s*saver\b", "elss tax saver"),
    # Nifty Index
    (r"\bnifty\s*50\b", "nifty index"),
    (r"\bnifty\s*index\s*fund\b", "nifty index"),
    (r"\bnifty\s*index\b", "nifty index"),
    (r"\bindex\s*fund\b", "nifty index"),  # when we only have SBI Nifty Index as index fund
    # US FoF (we only have SBI US Specific Equity Active FoF)
    (r"\bus\s*specific\s*equity\s*(?:active\s*)?fof\b", "us specific equity fof"),
    (r"\bus\s*specific\s*equity\b", "us specific equity fof"),
    (r"\bus\s*equity\b", "us specific equity fof"),
    (r"\bus\s*fof\b", "us specific equity fof"),
    (r"\bfof\s*fund\b", "us specific equity fof"),
]


def _normalize_query_for_retrieval(query: str) -> str:
    """Light cleaning + rule-based normalization for all input texts. Used for cache key and retrieve only."""
    if not query:
        return ""
    s = re.sub(r"\s+", " ", query.strip()).lower()
    for pattern, replacement in _QUERY_NORMALIZE_RULES:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)
    return s


def _cache_key(query: str) -> str:
    """Normalize for cache: use retrieval normalization so equivalent queries hit same cache."""
    return _normalize_query_for_retrieval(query)


def _response_cache_get(key: str):
    """Return cached response if present and not expired. Side-effect: removes expired entry."""
    if not key:
        return None
    entry = _response_cache.pop(key, None)
    if entry is None:
        return None
    expiry_ts, response = entry
    if time.monotonic() > expiry_ts:
        return None
    # Re-insert so this key is at end (LRU)
    _response_cache[key] = entry
    return response


def _response_cache_set(key: str, response: dict) -> None:
    """Store response; evict oldest if over capacity."""
    if not key:
        return
    expiry = time.monotonic() + CACHE_TTL_SECONDS
    while len(_response_cache) >= CACHE_MAX_SIZE and _response_cache:
        _response_cache.popitem(last=False)
    _response_cache[key] = (expiry, response)


_response_cache: OrderedDict = OrderedDict()

app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    description="Facts-only chatbot. One /chat endpoint.",
    version="0.1.0",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)


def _query_asks_for_statement(query: str) -> bool:
    q = query.lower()
    return any(w in q for w in STATEMENT_QUESTION_WORDS)


def _query_mentions_fund(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in FUND_KEYWORDS)


def _query_mentions_unsupported_fund(query: str) -> bool:
    """True if the query mentions an AMC/fund we don't have in our database."""
    q = query.lower()
    return any(amc in q for amc in UNSUPPORTED_AMC_KEYWORDS)


# Suggested "Try typing..." for failure responses: infer intent + scheme from query.
# Include typo-friendly hints (e.g. "lar cap") so "SB lar cap" maps to SBI Large Cap, not default ELSS.
_SCHEME_HINTS = [
    ("fof", "us specific", "us equity"),
    ("nifty", "nifty index", "index fund"),
    ("flexicap", "flexi cap"),
    ("elss", "tax saver"),
    ("large cap", "largecap", "lar cap", "sb large", "sbi large"),
]
_SCHEME_NAMES = [
    "SBI US Specific Equity Active FoF Fund",
    "SBI Nifty Index Fund",
    "SBI Flexicap Fund",
    "SBI ELSS Tax Saver Fund",
    "SBI Large Cap Fund",
]


def _normalize_for_compare(s: str) -> str:
    """Normalize for similarity: lowercase, collapse spaces, remove punctuation."""
    if not s:
        return ""
    s = re.sub(r"[^\w\s]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _suggest_try_typing(query: str) -> str:
    """Return a suggested question for no-info responses so user can try an adjacent phrasing.
    Always suggest an actionable question (never a tip like 'Try including the scheme name').
    Avoids suggesting the same question the user just asked (prevents loop)."""
    q = (query or "").lower().strip()
    qn = _normalize_for_compare(q)
    scheme = None
    for i, hints in enumerate(_SCHEME_HINTS):
        if any(h in q for h in hints):
            scheme = _SCHEME_NAMES[i]
            break
    if not scheme:
        scheme = "SBI ELSS Tax Saver Fund"

    # If user literally typed our old generic tip, suggest a real question instead (prevents loop).
    if "try including" in q and "scheme name" in q:
        return f"What is the expense ratio of {scheme}?"
    if "including the scheme name" in q:
        return f"What is the expense ratio of {scheme}?"

    # If user already asked the exact "Who is the fund manager of X?" we would suggest, return an alternative to avoid loop.
    canonical_fm = _normalize_for_compare(f"Who is the fund manager of {scheme}?")
    if qn == canonical_fm:
        return f"What is the expense ratio of {scheme}?"
    for name in _SCHEME_NAMES:
        if name.lower() in q and _normalize_for_compare(f"Who is the fund manager of {name}?") == qn:
            return f"What is the expense ratio of {name}?"

    if any(w in q for w in ["lock", "lock-in", "lock period"]):
        return f"What is the lock-in period for {scheme}?"
    if any(w in q for w in ["manager", "kaun", "who manages", "fund manager"]):
        return f"Who is the fund manager of {scheme}?"
    if any(w in q for w in ["expense", "expense ratio"]):
        return f"What is the expense ratio of {scheme}?"
    if any(w in q for w in ["nav"]):
        return f"What is the NAV of {scheme}?"
    if any(w in q for w in ["benchmark"]):
        return f"What is the benchmark of {scheme}?"
    if any(w in q for w in ["sip", "minimum", "min investment"]):
        return f"What is the minimum SIP for {scheme}?"
    if any(w in q for w in ["risk", "riskometer"]):
        return f"What is the risk for {scheme}?"
    if any(w in q for w in ["exit load"]):
        return f"What is the exit load for {scheme}?"
    # Default: suggest a concrete question (not a tip), so clicking it returns a real answer and avoids loop.
    return f"What is the expense ratio of {scheme}?"


def _is_no_info_answer(answer: str) -> bool:
    """True if the answer is the generic no-information message."""
    if not answer:
        return False
    a = answer.strip().lower()
    return "don't have that information" in a or "do not have that information" in a


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/last-updated")
def last_updated():
    """Return last updated note for footer (date/time). Used by frontend on load so date/time appears without a chat response."""
    return {"last_updated_note": _last_updated_note()}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Run safety -> retrieve -> LLM. One citation per answer (Source or Statement). No citation if no fund mentioned."""
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    query_for_retrieval = _normalize_query_for_retrieval(query)
    query_for_retrieval = expand_query_for_retrieval(query_for_retrieval)
    cache_key = _cache_key(query)
    cached = _response_cache_get(cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1) Safety check
        try:
            r = await client.post(f"{SAFETY_URL.rstrip('/')}/check", json={"query": query})
            safety = r.json() if r.status_code == 200 else {}
        except Exception:
            raise HTTPException(status_code=503, detail="Safety service unavailable.")
        if not safety.get("allowed", True):
            out = {
                "refusal": True,
                "message": safety.get("refusal_message") or "I'm here only for factual info on the schemes in my sources.",
                "educational_link": safety.get("educational_link"),
            }
            _response_cache_set(cache_key, out)
            return out

        # We only have SBI schemes; don't return data for other AMCs (e.g. ICICI, HDFC)
        if _query_mentions_unsupported_fund(query):
            out = {
                "refusal": False,
                "answer": f"We don't have that fund in our sources. We only cover: {COVERED_SCHEMES_LIST}",
                "citation_url": "",
                "last_updated_note": _last_updated_note(),
            }
            _response_cache_set(cache_key, out)
            return out

        # 2) Retrieve chunks
        try:
            r = await client.post(f"{RETRIEVE_URL.rstrip('/')}/retrieve", json={"query": query_for_retrieval, "top_k": 15})
            if r.status_code != 200:
                raise HTTPException(status_code=503, detail="Retrieval unavailable.")
            data = r.json()
            chunks = data.get("chunks", [])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503, detail="Retrieval unavailable.")

    # ROBUST: No chunks → clear message; do not call LLM with empty context
    if not chunks:
        out = {
            "refusal": False,
            "answer": "No matching data for this query. Please include the scheme name (e.g. SBI ELSS Tax Saver Fund) and try again.",
            "citation_url": "",
            "last_updated_note": _last_updated_note(),
            "suggested_query": _suggest_try_typing(query),
        }
        _response_cache_set(cache_key, out)
        return out

    top = chunks[0] if chunks else {}
    source_url = (top.get("source_url") or "").strip()
    statement_url = (top.get("statement_url") or "").strip()
    mentions_fund = _query_mentions_fund(query)
    asks_for_statement = _query_asks_for_statement(query)

    # Statement-only path: user asked for download/statements and we have a link → canned answer, one citation = statement URL
    if asks_for_statement and statement_url:
        citation = statement_url if mentions_fund else ""
        out = {
            "refusal": False,
            "answer": CANNED_STATEMENT_ANSWER,
            "citation_url": citation,
            "last_updated_note": _last_updated_note(),
        }
        _response_cache_set(cache_key, out)
        return out

    # 3) LLM answer for normal queries
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(f"{LLM_URL.rstrip('/')}/answer", json={"query": query, "chunks": chunks})
            if r.status_code != 200:
                raise HTTPException(status_code=503, detail="Answer service unavailable.")
            result = r.json()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503, detail="Answer service unavailable.")

    answer = result.get("answer", "")
    # One citation: Source URL only (IND money). No citation if user didn't mention a fund.
    citation_url = source_url if mentions_fund else ""
    out = {
        "refusal": False,
        "answer": answer,
        "citation_url": citation_url,
        "last_updated_note": _last_updated_note(),
    }
    if _is_no_info_answer(answer):
        out["suggested_query"] = _suggest_try_typing(query)
    _response_cache_set(cache_key, out)
    return out


@app.get("/")
def index():
    """Serve the single-page app."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")
    return {"message": "Static files not found. Ensure public/index.html exists."}
