"""
Phase 04 - Safety Layer: classify question as factual (allow) or not (refusal).
Returns allowed flag and refusal message if any. Facts-only; no educational links.
"""

from messages import get_refusal_message, get_refusal_message_pii
from classifier.rules import is_advice_or_opinion, is_pii_or_account


def check_safety(question: str) -> dict:
    """
    Classify the question. If factual -> allow. If advice/opinion or PII -> refuse.

    Returns:
        {
            "allowed": bool,           # True = proceed to retrieval + LLM
            "refusal_message": str | None,
            "educational_link": str | None,  # Always None (no investor education)
        }
    """
    q = (question or "").strip()
    if not q:
        return {
            "allowed": False,
            "refusal_message": "Please ask a factual question about the mutual funds in my sources.",
            "educational_link": None,
        }

    if is_pii_or_account(q):
        return {
            "allowed": False,
            "refusal_message": get_refusal_message_pii(),
            "educational_link": None,
        }

    if is_advice_or_opinion(q):
        return {
            "allowed": False,
            "refusal_message": get_refusal_message(),
            "educational_link": None,
        }

    return {
        "allowed": True,
        "refusal_message": None,
        "educational_link": None,
    }
