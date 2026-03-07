"""
Phase 04 - Safety: classifier and rules tests.
Run from Phase 04- safety: pytest tests/ -v
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from classifier import check_safety, is_advice_or_opinion, is_pii_or_account
from messages import get_refusal_message, get_refusal_message_pii


# --- Factual (allowed) ---

@pytest.mark.parametrize("q", [
    "What is the expense ratio of SBI ELSS?",
    "Lock in period for ELSS?",
    "What is the minimum SIP for Nifty Index Fund?",
    "Who is the fund manager of Flexicap?",
    "NAV of Large Cap fund",
    "Benchmark for SBI US FoF",
])
def test_factual_questions_allowed(q):
    r = check_safety(q)
    assert r["allowed"] is True
    assert r["refusal_message"] is None
    assert r["educational_link"] is None


# --- Advice / opinion (refusal) ---

@pytest.mark.parametrize("q", [
    "Should I buy SBI ELSS?",
    "Can you recommend a fund?",
    "Which fund should I invest in?",
    "Is it good to invest in Flexicap?",
    "What should I do with my portfolio?",
    "Buy or sell Large Cap?",
    "Recommend me a scheme",
    "Which one is best for me?",
    "Kahan karun invest aaj paise",
    "Where to invest money?",
])
def test_advice_questions_refused(q):
    r = check_safety(q)
    assert r["allowed"] is False
    assert r["refusal_message"] is not None
    assert len(r["refusal_message"]) > 0
    assert r["educational_link"] is None  # Facts-only; no investor education


def test_refusal_message_facts_only():
    msg = get_refusal_message()
    assert "factual" in msg.lower() or "no investment advice" in msg.lower()
    assert "http" not in msg and "amfiindia" not in msg.lower()


# --- PII / account (refusal, no advice link) ---

@pytest.mark.parametrize("q", [
    "Update my PAN",
    "Take my aadhar data",
    "take my pan number",
    "I want to update my email",
    "KYC status",
    "My account number",
    "OTP not received",
])
def test_pii_questions_refused(q):
    r = check_safety(q)
    assert r["allowed"] is False
    assert r["refusal_message"] is not None
    assert r["educational_link"] is None


def test_pii_refusal_does_not_offer_advice_link():
    msg = get_refusal_message_pii()
    assert "personal" in msg.lower() or "account" in msg.lower() or "fund house" in msg.lower()


# --- Empty ---

def test_empty_question_refused():
    r = check_safety("")
    assert r["allowed"] is False
    assert r["refusal_message"] is not None


def test_whitespace_only_refused():
    r = check_safety("   ")
    assert r["allowed"] is False


# --- Rules unit tests ---

def test_is_advice_or_opinion():
    assert is_advice_or_opinion("Should I invest?") is True
    assert is_advice_or_opinion("What is expense ratio?") is False


def test_is_pii_or_account():
    assert is_pii_or_account("Update my PAN") is True
    assert is_pii_or_account("What is lock in?") is False
