"""
Validate that all 17 embedded/hyperlink question types return an answer (not NO_INFO)
for all 5 mutual funds when the right chunk is in context.
Uses chunks from Phase 01 chunks.json to simulate retrieval.
"""

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

PROJECT_ROOT = BACKEND_ROOT.parent
CHUNKS_PATH = PROJECT_ROOT / "Phase 01- data" / "chunks" / "chunks.json"

import pytest
from client.gemini_client import generate_response, NO_INFO_MESSAGE

# All 5 funds (canonical names)
FUNDS = [
    "SBI US Specific Equity Active FoF Fund",
    "SBI Nifty Index Fund",
    "SBI Flexicap Fund",
    "SBI ELSS Tax Saver Fund",
    "SBI Large Cap Fund",
]

# 17 question types: (label substrings to try in chunk text, question template with {scheme})
# For 15/16 we accept either old or new chunk labels.
QUESTION_TYPES = [
    ("Expense ratio:", "What is the expense ratio of {scheme}?"),
    ("Lock In:", "What is the lock-in period for {scheme}?"),
    ("Minimum SIP:", "What is the minimum SIP for {scheme}?"),
    ("Exit Load:", "What is the exit load for {scheme}?"),
    ("Risk:", "What is the risk for {scheme}?"),
    ("Benchmark:", "What is the benchmark of {scheme}?"),
    ("AUM:", "What is the AUM of {scheme}?"),
    ("Inception Date:", "What is the inception date of {scheme}?"),
    ("TurnOver:", "What is the turnover of {scheme}?"),
    ("About (Fund):", "Tell me about {scheme}"),
    ("Fund Manager:", "Who is the fund manager of {scheme}?"),
    ("How Do I Invest:", "How do I invest in {scheme}?"),
    ("NAV:", "What is the NAV of {scheme}?"),
    ("Fund vs Competition:", "What is the Fund vs Competition for {scheme}?"),
    (("Fund Ranking and Peer Comparison:", "Fund Comparison:"), "What is the fund ranking for {scheme}?"),
    (("Fund Ranking (Positive and Negative):", "Fund Pros and Cons:"), "What are the pros and cons of {scheme}?"),
    ("Fund Returns Calculator:", "What is the returns calculator for {scheme}?"),
]


def load_chunks_by_fund():
    """Load chunks.json and return dict fund_name -> list of chunk dicts."""
    if not CHUNKS_PATH.exists():
        pytest.skip(f"Chunks not found at {CHUNKS_PATH}")
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    chunks = data.get("chunks", [])
    by_fund = {}
    for c in chunks:
        name = c.get("fund_name", "")
        if name not in by_fund:
            by_fund[name] = []
        by_fund[name].append(c)
    return by_fund


def find_chunk_with_label(chunks, label_substring):
    """Return first chunk whose text contains label_substring (or any of them if tuple), or None."""
    labels = (label_substring,) if isinstance(label_substring, str) else label_substring
    for c in chunks:
        text = c.get("text") or ""
        if any(lbl in text for lbl in labels):
            return c
    return None


@pytest.fixture(scope="module")
def chunks_by_fund():
    return load_chunks_by_fund()


@pytest.mark.parametrize("fund_name", FUNDS)
@pytest.mark.parametrize("label_substring,question_template", QUESTION_TYPES)
def test_embedded_question_returns_answer_for_fund(chunks_by_fund, fund_name, label_substring, question_template):
    """For each fund and each of the 17 embedded question types, extraction returns an answer when chunk has the label."""
    chunks = chunks_by_fund.get(fund_name, [])
    if not chunks:
        pytest.skip(f"No chunks for fund {fund_name!r}")
    chunk = find_chunk_with_label(chunks, label_substring)
    if chunk is None:
        pytest.skip(f"No chunk with {label_substring!r} for {fund_name!r}")
    question = question_template.format(scheme=fund_name)
    result = generate_response(question, [chunk])
    answer = (result.get("answer") or "").strip()
    assert answer != NO_INFO_MESSAGE, (
        f"Fund {fund_name!r}, question type {label_substring!r}: got NO_INFO. Question: {question[:60]}..."
    )
