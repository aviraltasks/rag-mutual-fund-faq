"""
Query expansion for retrieval: rewrite abbreviated queries into canonical natural-language
questions so vector similarity matches chunk phrasing. Used only for the string sent to
Phase 02 /retrieve. Original user query is still sent to Safety and LLM.

Expand only when exactly one scheme and one intent are detected; otherwise return
the normalized query (fallback). No new dependencies; deterministic and rule-based.
"""

from __future__ import annotations

# Fund alias hints (order matters: first match wins). Same canonical set as orchestrator.
_SCHEME_HINTS = [
    ("fof", "us specific", "us equity"),
    ("nifty", "nifty index", "index fund"),
    ("flexicap", "flexi cap", "flexi"),
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

# Intent: (keywords that trigger this intent, canonical question template with {scheme})
_INTENTS = [
    (["tell me about", "about this fund", "what is this fund"], "What is the fund objective and about section for {scheme}?"),
    (["manager", "fund manager", "kaun", "who manages"], "Who is the fund manager of {scheme}?"),
    (["lock", "lock-in", "lock period", "lockin"], "What is the lock-in period for {scheme}?"),
    (["expense", "expense ratio"], "What is the expense ratio of {scheme}?"),
    (["nav"], "What is the NAV of {scheme}?"),
    (["benchmark"], "What is the benchmark of {scheme}?"),
    (["sip", "minimum sip", "min investment", "minimum investment"], "What is the minimum SIP for {scheme}?"),
    (["investment steps", "steps to invest", "how do i invest", "how to invest", "guide me invest"], "How do I invest in {scheme}?"),
    (["risk", "riskometer"], "What is the risk for {scheme}?"),
    (["exit load"], "What is the exit load for {scheme}?"),
    (["aum", "assets under management"], "What is the AUM of {scheme}?"),
    (["inception", "inception date"], "What is the inception date of {scheme}?"),
    (["turnover", "turn over"], "What is the turnover of {scheme}?"),
    (["returns", "performance"], "What are the returns of {scheme}?"),
    (["pros and cons", "positives and negatives", "positive and negative"], "What are the Fund Pros and Cons for {scheme}?"),
    (["ranking", "rank"], "What is the ranking of {scheme}?"),
    (["vs competition", "fund vs competition", "versus competition"], "What is the Fund vs Competition for {scheme}?"),
]


def _detect_scheme(q: str) -> str | None:
    """Return the first matching canonical scheme name, or None if no hint matches."""
    if not q:
        return None
    q = q.lower()
    for i, hints in enumerate(_SCHEME_HINTS):
        if any(h in q for h in hints):
            return _SCHEME_NAMES[i]
    return None


def _detect_intent(q: str) -> str | None:
    """Return the first matching intent template (with {scheme} placeholder), or None."""
    if not q:
        return None
    q = q.lower()
    for keywords, template in _INTENTS:
        if any(kw in q for kw in keywords):
            return template
    return None


def expand_query_for_retrieval(normalized_query: str) -> str:
    """
    Expand a normalized user query into a canonical natural-language question when
    exactly one scheme and one intent are detected. Otherwise return the input unchanged.

    Used only for the query sent to retrieval. Original query is still passed to LLM.
    """
    if not normalized_query or not normalized_query.strip():
        return normalized_query or ""
    q = normalized_query.strip().lower()
    scheme = _detect_scheme(q)
    template = _detect_intent(q)
    if scheme is None or template is None:
        return normalized_query
    return template.format(scheme=scheme)
