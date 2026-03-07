"""
Phase 03 - LLM Response: Gemini client.
Calls Gemini with system + context + question; returns answer, one citation URL, and last-updated note.
Citation is taken from the top retrieved chunk (source_url), not from LLM output.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from config import GEMINI_API_KEY, GEMINI_MODEL, LAST_UPDATED_PREFIX
from prompts import SYSTEM_INSTRUCTIONS, build_user_message

# Fallback when no context or API error
NO_INFO_MESSAGE = "I don't have that information in my sources."
OUT_OF_SCOPE_MESSAGE = "That is out of scope for this assistant. I only answer factual questions about the mutual funds in my sources."
DEFAULT_LAST_UPDATED = "Last updated from sources: see citation link."


def _format_last_updated() -> str:
    """Return a human-readable 'Last updated' string with current date and time (IST)."""
    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        return f"Last updated: {now.strftime('%d %b %Y, %I:%M %p IST')}"
    except Exception:
        now = datetime.utcnow()
        return f"Last updated: {now.strftime('%d %b %Y, %H:%M UTC')}"

# When LLM says "no info" but context has the fact, extract from context (question pattern, label, context pattern)
# Covers Info 1-17 from data_review / chunks so diverse user phrasings still return answers.
CONTEXT_EXTRACT_PATTERNS = [
    (r"expense\s*ratio|expense\s*ration", "Expense ratio", r"Expense ratio:\s*([^\n]+?)(?:\n|$)"),
    (r"lock\s*in|lock-in|lock\s*period", "Lock-in period", r"Lock In:\s*([^\n]+?)(?:\n|$)"),
    (r"minimum\s*sip|min\s*sip|minimum\s*investment|min\s*investment", "Minimum SIP", r"Minimum SIP:\s*([^\n]+?)(?:\n|$)"),
    (r"exit\s*load", "Exit load", r"Exit Load:\s*([^\n]+?)(?:\n|$)"),
    (r"risk|riskometer", "Risk", r"Risk:\s*([^\n]+?)(?:\n|$)"),
    (r"benchmark|benchamark", "Benchmark", r"Benchmark:\s*([^\n]+?)(?:\n|$)"),
    (r"aum", "AUM", r"AUM:\s*([^\n]+?)(?:\n|$)"),
    (r"inception|when\s+(?:was|did)|started|launch(?:ed)?", "Inception date", r"Inception Date:\s*([^\n]+?)(?:\n|$)"),
    (r"nav\b", "NAV", r"NAV:\s*([^\n]+?)(?:\n|$)"),
    (r"fund\s*manager|who\s+is\s+(?:the\s+)?(?:fund\s+)?manager|manager\s+of|who\s+manages|manages\s+(?:this\s+)?(?:the\s+)?fund|kaun\s+(?:he|hai)\s+manager|manager\s+.*\s+ka\b|kaun.*manager", "Fund manager", r"Fund Manager:\s*([^\n]+?)(?:\n|$)"),
    (r"turnover|turn\s*over", "Turnover", r"TurnOver:\s*([^\n]+?)(?:\n|$)"),
    (r"how\s+do\s+i\s+invest|how\s+to\s+invest|how\s+can\s+i\s+invest", "How do I invest", r"How Do I Invest:\s*([^\n]+)"),
    (r"investment\s+steps|steps\s+to\s+invest|steps\s+for\s+investing|tell\s+(?:me\s+)?(?:the\s+)?(?:investment\s+)?steps|guide\s+(?:me\s+)?(?:on\s+)?(?:how\s+)?(?:to\s+)?invest", "How do I invest", r"How Do I Invest:\s*([^\n]+)"),
    (r"about\s*(?:the\s+)?fund|what\s+is\s+this\s+fund|fund\s+objective", "About (Fund)", r"About \(Fund\):\s*([^\n]+)"),
    (r"tell\s+me\s+about|about\s+.+\s+fund", "About (Fund)", r"About \(Fund\):\s*([^\n]+)"),
    (r"fund\s+vs\s+competition|vs\s+competition|performance|comparison", "Fund vs Competition", r"Fund vs Competition:\s*([^\n]+)"),
    (r"how\s+does\s+.+\s+do\s+vs\s+competition|do\s+vs\s+competition|versus\s+competition", "Fund vs Competition", r"Fund vs Competition:\s*([^\n]+)"),
    (r"ranking|peer\s+comparison|rank\s+(?:of|among)|fund\s+comparison", "Fund Comparison", r"(?:Fund Comparison|Fund Ranking and Peer Comparison):\s*([^\n]+)"),
    (r"positive\s+and\s+negative|pros\s+and\s+cons|ranking\s+positive|positives\s+and\s+negatives", "Fund Pros and Cons", r"(?:Fund Pros and Cons|Fund Ranking \(Positive and Negative\)):\s*([^\n]+)"),
    (r"returns\s+calculator|absolute\s+return|sip\s+return", "Fund Returns Calculator", r"Fund Returns Calculator:\s*([^\n]+)"),
]


def _extract_from_context_if_present(question: str, context: str) -> str | None:
    """If the question asks for a known field and context contains it, return a short answer sentence; else None."""
    q = (question or "").lower()
    ctx = (context or "").strip()
    if not ctx:
        return None
    for q_pattern, label, ctx_pattern in CONTEXT_EXTRACT_PATTERNS:
        if re.search(q_pattern, q, re.I):
            m = re.search(ctx_pattern, ctx, re.I)
            if m:
                value = m.group(1).strip()
                max_len = 400
                if value and len(value) <= max_len:
                    return f"The {label} is {value}."
                if value and len(value) > max_len:
                    value = value[: max_len - 3].rstrip() + "..."
                    return f"The {label} is {value}."
    return None


def _chunks_to_context(chunks: list[dict]) -> str:
    """Turn list of chunk dicts (with 'text') into a single context string."""
    if not chunks:
        return ""
    return "\n\n".join(c.get("text", "") for c in chunks if c.get("text"))


def _citation_from_chunks(chunks: list[dict]) -> str:
    """Return source_url of the top chunk (IND money link) for citation."""
    if not chunks:
        return ""
    return (chunks[0].get("source_url") or "").strip()


def generate_response(question: str, chunks: list[dict]) -> dict:
    """
    Generate a factual answer from retrieved chunks using Gemini.

    Args:
        question: User question.
        chunks: List of chunk dicts from retrieval (each with 'text', 'source_url', etc.).

    Returns:
        {
            "answer": str,
            "citation_url": str,   # IND money source URL from top chunk
            "last_updated_note": str,
        }
    """
    citation_url = _citation_from_chunks(chunks)
    last_updated_note = DEFAULT_LAST_UPDATED
    context = _chunks_to_context(chunks)

    if not context.strip():
        return {
            "answer": NO_INFO_MESSAGE,
            "citation_url": "",
            "last_updated_note": last_updated_note,
        }

    # ROBUST: Try extraction first whenever we have context (works without LLM / when LLM fails)
    extracted = _extract_from_context_if_present(question, context)
    if extracted:
        return {
            "answer": extracted,
            "citation_url": citation_url,
            "last_updated_note": _format_last_updated(),
        }

    # No API key: extraction already tried above; return no-info only if extraction failed
    if not GEMINI_API_KEY:
        return {
            "answer": NO_INFO_MESSAGE,
            "citation_url": citation_url,
            "last_updated_note": last_updated_note,
        }

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        user_message = build_user_message(context, question)
        response = model.generate_content(
            [SYSTEM_INSTRUCTIONS, user_message],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=256,
                temperature=0.1,
            ),
        )
        answer = (response.text or "").strip() if response.candidates else ""
        if not answer:
            answer = NO_INFO_MESSAGE
        # Fallback: if LLM still said "no info", try extraction again (e.g. different phrasing in context)
        _no_info_core = "don't have that information in my sources"
        if _no_info_core.lower() in answer.lower():
            extracted = _extract_from_context_if_present(question, context)
            if extracted:
                answer = extracted
        return {
            "answer": answer,
            "citation_url": citation_url,
            "last_updated_note": _format_last_updated(),
        }
    except Exception:
        # ROBUST: On LLM failure, try extraction once more (context is good; API may be transient)
        extracted = _extract_from_context_if_present(question, context)
        if extracted:
            return {
                "answer": extracted,
                "citation_url": citation_url,
                "last_updated_note": _format_last_updated(),
            }
        return {
            "answer": NO_INFO_MESSAGE + " (Service temporarily unavailable.)",
            "citation_url": citation_url,
            "last_updated_note": last_updated_note,
        }
