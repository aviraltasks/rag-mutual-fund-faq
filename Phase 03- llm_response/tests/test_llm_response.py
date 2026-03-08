"""
Phase 03 - LLM Response: tests.
Run from Phase 03- llm_response: pytest tests/ -v
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from client.gemini_client import (
    generate_response,
    _chunks_to_context,
    _citation_from_chunks,
    _ensure_complete_ending,
    NO_INFO_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
    DEFAULT_LAST_UPDATED,
)
from prompts import SYSTEM_INSTRUCTIONS, build_user_message


# --- Prompt tests ---

def test_system_instructions_mention_context_only():
    assert "only" in SYSTEM_INSTRUCTIONS.lower() and "context" in SYSTEM_INSTRUCTIONS.lower()


def test_system_instructions_forbid_advice():
    assert "advice" in SYSTEM_INSTRUCTIONS.lower() or "recommendation" in SYSTEM_INSTRUCTIONS.lower()


def test_system_instructions_mention_personal_info():
    assert "personal" in SYSTEM_INSTRUCTIONS.lower() or "PAN" in SYSTEM_INSTRUCTIONS or "Aadhaar" in SYSTEM_INSTRUCTIONS


def test_build_user_message_includes_context_and_question():
    msg = build_user_message("Lock in is 3 years.", "What is the lock in?")
    assert "Lock in is 3 years." in msg
    assert "What is the lock in?" in msg


# --- Helper tests ---

def test_chunks_to_context_empty():
    assert _chunks_to_context([]) == ""


def test_chunks_to_context_joins_text():
    chunks = [{"text": "A"}, {"text": "B"}]
    assert "A" in _chunks_to_context(chunks) and "B" in _chunks_to_context(chunks)


def test_citation_from_chunks_empty():
    assert _citation_from_chunks([]) == ""


def test_citation_from_chunks_returns_first_source_url():
    chunks = [
        {"text": "x", "source_url": "https://indmoney.com/fund1"},
        {"text": "y", "source_url": "https://indmoney.com/fund2"},
    ]
    assert _citation_from_chunks(chunks) == "https://indmoney.com/fund1"


def test_ensure_complete_ending_strips_broken_fragments():
    """Broken endings like ' thi.' or ' but.' are removed; answer always ends at a sentence boundary or with a period."""
    assert _ensure_complete_ending("No bad points found for thi.") == "No bad points found for."
    assert _ensure_complete_ending("The fund has outperformed over 3Y, 5Y, but.") == "The fund has outperformed over 3Y, 5Y."
    assert _ensure_complete_ending("Normal complete answer.") == "Normal complete answer."
    assert _ensure_complete_ending("One sentence. Another ending with thi.") == "One sentence."
    assert _ensure_complete_ending("") == ""
    assert _ensure_complete_ending("Short") == "Short."


def test_ensure_complete_ending_unforeseen_cases():
    """Other incomplete endings (and, the, for, etc.) and missing punctuation are fixed so users never see broken info."""
    assert _ensure_complete_ending("Positive points. Negative: none found for the.") == "Positive points."
    assert _ensure_complete_ending("The expense ratio is 0.89%. The lock-in is 3 years, and.") == "The expense ratio is 0.89%. The lock-in is 3 years."
    assert _ensure_complete_ending("It has outperformed over 1Y and 3Y.") == "It has outperformed over 1Y and 3Y."
    assert _ensure_complete_ending("Some answer without period") == "Some answer without period."
    assert _ensure_complete_ending("Ends with comma or space  ") == "Ends with comma or space."
    assert _ensure_complete_ending("Yes") == "Yes."


# --- generate_response tests (mocked Gemini) ---

def test_generate_response_empty_chunks():
    result = generate_response("What is the lock in?", [])
    assert result["answer"] == NO_INFO_MESSAGE
    assert result["citation_url"] == ""
    assert result["last_updated_note"] == DEFAULT_LAST_UPDATED


def test_generate_response_no_context_text_returns_no_info():
    chunks = [{"text": "", "source_url": "https://example.com"}]
    result = generate_response("Anything?", chunks)
    assert NO_INFO_MESSAGE in result["answer"]
    assert "citation_url" in result and "last_updated_note" in result


def test_generate_response_returns_citation_from_top_chunk():
    """Citation URL must come from the top chunk's source_url, not from LLM."""
    chunks = [
        {"text": "ELSS has 3 year lock in.", "source_url": "https://indmoney.com/elss"},
    ]
    result = generate_response("What is lock in?", chunks)
    assert result["citation_url"] == "https://indmoney.com/elss"
    assert result["last_updated_note"] == DEFAULT_LAST_UPDATED or "Last updated" in (result.get("last_updated_note") or "")
    assert "answer" in result


def test_generate_response_structure():
    """Without mocking: if no API key, we get the no-info path; structure still correct."""
    chunks = [{"text": "Some context.", "source_url": "https://indmoney.com/x"}]
    result = generate_response("Question?", chunks)
    assert "answer" in result and isinstance(result["answer"], str)
    assert "citation_url" in result and isinstance(result["citation_url"], str)
    assert "last_updated_note" in result and isinstance(result["last_updated_note"], str)
    assert result["citation_url"] == "https://indmoney.com/x"


def test_generate_response_extraction_returns_fact():
    """Extraction-first: when chunks contain the fact, answer contains it (no LLM required)."""
    chunks = [
        {
            "text": "Mutual Fund Name: SBI ELSS Tax Saver Fund\n\nExpense ratio: 0.89%\n\nLock In: 3 Years",
            "source_url": "https://indmoney.com/elss",
            "chunk_id": "c1",
            "fund_name": "SBI ELSS",
            "statement_url": "",
        }
    ]
    result = generate_response("What is the expense ratio of SBI ELSS Tax Saver Fund?", chunks)
    assert "0.89%" in result["answer"], f"Expected 0.89%% in answer, got: {result['answer']}"
    assert result["citation_url"] == "https://indmoney.com/elss"
    assert "last_updated_note" in result


def test_generate_response_extraction_benchmark():
    """Extraction returns benchmark when present in context."""
    chunks = [
        {
            "text": "SBI Large Cap Fund\n\nBenchmark: BSE 100 India TR INR\n\nAUM: 54.8K Cr",
            "source_url": "https://indmoney.com/largecap",
            "chunk_id": "c1",
            "fund_name": "SBI Large Cap",
            "statement_url": "",
        }
    ]
    result = generate_response("What is the benchmark of SBI Large Cap Fund?", chunks)
    assert "BSE 100" in result["answer"] or "benchmark" in result["answer"].lower()
    assert result["citation_url"] == "https://indmoney.com/largecap"


def test_generate_response_extraction_fund_manager():
    """Extraction returns fund manager when context has 'Fund Manager: Name' and user asks 'who is the manager'."""
    chunks = [
        {
            "text": "SBI US Specific Equity Active FoF Fund. About: invests in US markets.\n\nFund Manager: Rohit Shimpi\n\nHow Do I Invest: Download the app.",
            "source_url": "https://indmoney.com/us-fof",
            "chunk_id": "c1",
            "fund_name": "SBI US Specific Equity Active FoF Fund",
            "statement_url": "",
        }
    ]
    result = generate_response("Who is the manager of SBI US Specific Equity Active Fof Fund?", chunks)
    assert "Rohit Shimpi" in result["answer"]
    assert "don't have that information" not in result["answer"].lower()
