"""
Phase 04 - Safety Layer: refusal message templates.
Used when the question is classified as advice, recommendation, or opinion.
Facts-only; no investor education links.
"""

REFUSAL_MESSAGE = (
    "I'm here only for factual info on the schemes in my sources—no investment advice or recommendations. "
    "Please ask a factual question (e.g. expense ratio, lock-in, benchmark) and include the scheme name."
)

REFUSAL_MESSAGE_PII = (
    "I'm not able to help with personal or account details—I only answer factual questions about the mutual funds in my sources."
)


def get_refusal_message(educational_link: str = None) -> str:
    """Return the standard refusal message (facts-only; link ignored)."""
    return REFUSAL_MESSAGE


def get_refusal_message_pii() -> str:
    """Return refusal for personal/account-related questions (no advice link)."""
    return REFUSAL_MESSAGE_PII
