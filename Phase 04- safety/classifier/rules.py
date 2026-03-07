"""
Phase 04 - Safety Layer: classification rules.
Factual vs. advice/recommendation/opinion and out-of-scope (e.g. PII).
"""

import re

# Patterns that indicate advice, recommendation, or opinion (not factual)
ADVICE_PATTERNS = [
    r"\bshould\s+i\b",
    r"\bcan\s+you\s+(recommend|suggest|advise)\b",
    r"\b(recommend|suggest)\s+(me\s+)?(a\s+)?(fund|scheme)\b",
    r"\bwhich\s+(fund|scheme|one)\s+(is\s+best|should\s+i|to\s+invest)\b",
    r"\bis\s+it\s+(good|worth)\s+to\s+invest\b",
    r"\b(advice|advise)\b",
    r"\brecommendation\b",
    r"\bmy\s+portfolio\b",
    r"\bwhat\s+should\s+i\s+(do|invest|choose)\b",
    r"\bbuy\s+or\s+sell\b",
    r"\bsell\s+or\s+buy\b",
    r"\bwhich\s+one\s+should\s+i\b",
    r"\bhelp\s+me\s+(choose|decide|invest)\b",
    r"\btell\s+me\s+(which|what)\s+to\s+invest\b",
    r"\bgood\s+for\s+(me|my\s+goal)\b",
    r"\bbest\s+fund\s+to\s+invest\b",
    r"\bworth\s+investing\b",
    r"\bwhere\s+(to\s+)?invest\b",
    r"\bkahan\s+karun\s+invest\b",
    r"\bkaun\s+(sa\s+)?fund\b",
    r"\b(where|kahan)\s+.*(invest|paise)\b",
]

# Patterns that indicate personal/account/PII (out of scope)
PII_PATTERNS = [
    r"\bpan\s*(number)?\b",
    r"\baadhaar\b",
    r"\baadhar\b",  # common spelling
    r"\baccount\s*number\b",
    r"\botp\b",
    r"\bkyc\b",
    r"\b(my\s+)?(aadhar|aadhaar)\s*(data|number|card)?\b",
    r"\b(aadhar|aadhaar)\s*(data|number|card)?\b",
    r"\bupdate\s+(my\s+)?(email|mobile|phone)\b",
    r"\bmy\s+email\b",
    r"\bmy\s+phone\b",
    r"\bmy\s+mobile\b",
    r"\bregister\b",
    r"\blogin\b",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    for pat in patterns:
        if re.search(pat, t, re.I):
            return True
    return False


def is_advice_or_opinion(question: str) -> bool:
    """True if the question asks for advice, recommendation, or opinion."""
    return _matches_any(question, ADVICE_PATTERNS)


def is_pii_or_account(question: str) -> bool:
    """True if the question appears to be about personal info or account (out of scope)."""
    return _matches_any(question, PII_PATTERNS)
