"""
Tests for query expansion: canonical expansion and fallback behavior.
Run from Phase 05- frontend: pytest tests/test_query_expansion.py -v
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.query_expansion import expand_query_for_retrieval


def test_expand_sb_lar_cap_manager():
    """'sb lar cap manager' (normalized) -> fund manager of SBI Large Cap Fund."""
    out = expand_query_for_retrieval("sb lar cap manager")
    assert "fund manager" in out.lower()
    assert "SBI Large Cap Fund" in out


def test_expand_sbi_largecap_expense():
    """'sbi largecap expense' -> expense ratio of SBI Large Cap Fund."""
    out = expand_query_for_retrieval("sbi largecap expense")
    assert "expense" in out.lower()
    assert "SBI Large Cap Fund" in out


def test_expand_nav_flexi():
    """'nav flexi' -> NAV of SBI Flexicap Fund."""
    out = expand_query_for_retrieval("nav flexi")
    assert "nav" in out.lower()
    assert "SBI Flexicap Fund" in out


def test_expand_elss_lockin():
    """'elss lockin' -> lock-in period of SBI ELSS Tax Saver Fund."""
    out = expand_query_for_retrieval("elss lockin")
    assert "lock" in out.lower()
    assert "SBI ELSS Tax Saver Fund" in out


def test_expand_benchmark_largecap():
    """'benchmark of largecap' -> benchmark of SBI Large Cap Fund."""
    out = expand_query_for_retrieval("benchmark of largecap")
    assert "benchmark" in out.lower()
    assert "SBI Large Cap Fund" in out


def test_expand_expense_of_elss():
    """'expense of elss' -> expense ratio of SBI ELSS Tax Saver Fund."""
    out = expand_query_for_retrieval("expense of elss")
    assert "expense" in out.lower()
    assert "SBI ELSS Tax Saver Fund" in out


def test_expand_nifty_index_fund_expense():
    """Nifty index + expense -> expense ratio of SBI Nifty Index Fund."""
    out = expand_query_for_retrieval("nifty index fund expense")
    assert "expense" in out.lower()
    assert "SBI Nifty Index Fund" in out


def test_expand_us_fof_nav():
    """US FoF + nav -> NAV of SBI US Specific Equity Active FoF Fund."""
    out = expand_query_for_retrieval("us specific equity fof nav")
    assert "nav" in out.lower()
    assert "SBI US" in out and "FoF" in out


def test_fallback_no_scheme():
    """No scheme hint -> return input unchanged."""
    out = expand_query_for_retrieval("what is the weather today")
    assert out == "what is the weather today"


def test_fallback_no_intent():
    """Scheme but no intent keyword -> expand to about-section question for that scheme."""
    out = expand_query_for_retrieval("tell me about sbi large cap fund")
    assert out == "What is the fund objective and about section for SBI Large Cap Fund?"


def test_fallback_empty():
    """Empty or whitespace -> return as-is."""
    assert expand_query_for_retrieval("") == ""
    assert expand_query_for_retrieval("   ") == "   "


def test_expanded_is_natural_sentence():
    """Expanded query should be a full question (ends with ? or similar)."""
    out = expand_query_for_retrieval("sb lar cap manager")
    assert out.strip().endswith("?")
    assert out.startswith("Who ") or "fund manager" in out
