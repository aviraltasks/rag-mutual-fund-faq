"""
Validate extraction for all Info 1-17 (data_review / chunks) so diverse user inputs return answers.
One test per Info type: chunk contains the label, query triggers extraction, answer contains expected value.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from client.gemini_client import generate_response, NO_INFO_MESSAGE

BASE_CHUNK = {
    "chunk_id": "v",
    "source_url": "https://indmoney.com/test",
    "statement_url": "",
    "fund_name": "SBI ELSS Tax Saver Fund",
}

# Info 1-17: (sample query, chunk text snippet with label: value, expected substring in answer)
INFO_VALIDATION = [
    (1, "What is the expense ratio of SBI ELSS?", "Expense ratio: 0.89%\n\nLock In:", "0.89%"),
    (2, "What is the lock-in period for SBI ELSS?", "Lock In: 3 Years\n\nMinimum SIP:", "3 Years"),
    (3, "What is the minimum SIP for SBI ELSS?", "Minimum SIP: ₹500\n\nExit Load:", "500"),
    (4, "What is the exit load for SBI ELSS?", "Exit Load: 0%\n\nRisk:", "0%"),
    (5, "What is the risk for SBI ELSS?", "Risk: Very High\n\nBenchmark:", "Very High"),
    (6, "What is the benchmark of SBI ELSS?", "Benchmark: BSE 500 India TR INR\n\nAUM:", "BSE 500"),
    (7, "What is the AUM of SBI ELSS?", "AUM: ₹ 31.9K Cr\n\nInception", "31.9"),
    (8, "When was SBI ELSS started?", "Inception Date: 1 January, 2013\n\nTurnOver:", "2013"),
    (9, "What is the turnover of SBI ELSS?", "TurnOver: 19.46%\n\nAbout", "19.46"),
    (10, "What is this fund about? SBI ELSS", "About (Fund): The fund allocates at least 80%", "allocates"),
    (11, "Who is the fund manager of SBI ELSS?", "Fund Manager: Milind Agrawal\n\nHow Do I Invest:", "Milind Agrawal"),
    (12, "How do I invest in SBI ELSS?", "How Do I Invest: 1. Download the INDmoney app. 2. Search", "Download"),
    (13, "What is the NAV of SBI ELSS?", "NAV: ₹465.85\n\nFund vs Competition:", "465.85"),
    (14, "Fund vs competition for SBI ELSS?", "Fund vs Competition: The fund has outperformed the benchmark", "outperformed"),
    (15, "What is the ranking of SBI ELSS?", "Fund Comparison: Ranked 2 out of 23 mutual funds", "Ranked 2"),
    (16, "Pros and cons of SBI ELSS?", "Fund Pros and Cons: Positive: Generated Consistent Returns", "Positive"),
    (17, "What is the returns calculator for SBI ELSS?", "Fund Returns Calculator: 1-time Absolute Return 0.9% SIP Absolute Return 54%", "0.9%"),
]


def test_lock_period_generic_phrase():
    """'Lock period' (without 'in') should still trigger Lock-in extraction."""
    chunk = {**BASE_CHUNK, "text": "Lock In: No Lock-in\n\nMinimum SIP: --"}
    result = generate_response("what is lock period for SBI FOF?", [chunk])
    answer = (result.get("answer") or "").strip()
    assert answer != NO_INFO_MESSAGE
    assert "Lock-in" in answer or "No Lock-in" in answer


def test_fund_manager_hinglish():
    """Hinglish 'kaun he manager SBI large cap ka?' should trigger fund manager extraction."""
    chunk = {**BASE_CHUNK, "text": "Fund Manager: Saurabh Pant\n\nHow Do I Invest:", "fund_name": "SBI Large Cap Fund"}
    result = generate_response("kaun he manager SBI large cap ka?", [chunk])
    answer = (result.get("answer") or "").strip()
    assert answer != NO_INFO_MESSAGE
    assert "Saurabh Pant" in answer


@pytest.mark.parametrize("info_num,query,chunk_text,expected_in_answer", INFO_VALIDATION)
def test_info_extraction_returns_expected(info_num, query, chunk_text, expected_in_answer):
    """For each Info 1-17, extraction from context returns an answer containing the expected value."""
    chunk = {**BASE_CHUNK, "text": chunk_text}
    result = generate_response(query, [chunk])
    answer = (result.get("answer") or "").strip()
    assert answer != NO_INFO_MESSAGE, f"Info {info_num}: got no-info for query '{query[:50]}...'"
    assert expected_in_answer in answer, f"Info {info_num}: expected '{expected_in_answer}' in answer: {answer[:120]}..."
