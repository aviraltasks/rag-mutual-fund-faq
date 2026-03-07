"""
Phase 01 - Data: Scraper for INDMoney SBI mutual fund pages.
Collects Info 1-18 per fund, cleans data, saves raw/cleaned and data_review.json.
Uses Selenium (Chrome) for JS-rendered content, then BeautifulSoup for parsing.
Run: python scrape.py (from Phase 01- data folder). Requires Chrome installed.
"""

import json
import re
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

PHASE_DIR = Path(__file__).resolve().parent
RAW_DIR = PHASE_DIR / "raw"
CLEANED_DIR = PHASE_DIR / "cleaned"
RAW_DIR.mkdir(exist_ok=True)
CLEANED_DIR.mkdir(exist_ok=True)

URLS = [
    "https://www.indmoney.com/mutual-funds/sbi-us-specific-equity-active-fof-direct-growth-1006394",
    "https://www.indmoney.com/mutual-funds/sbi-nifty-index-fund-direct-growth-5583",
    "https://www.indmoney.com/mutual-funds/sbi-flexicap-fund-direct-growth-3249",
    "https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth-2754",
    "https://www.indmoney.com/mutual-funds/sbi-large-cap-fund-direct-growth-3046",
]

# SBI Mutual Fund scheme-details URLs for factsheets, KIM/SID, statements (not scraped; for user reference)
STATEMENT_URLS = {
    "SBI US Specific Equity Active FoF Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-international-access---us-equity-fof-582",
    "SBI Nifty Index Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-nifty-index-fund-13",
    "SBI Flexicap Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-flexicap-fund-39",
    "SBI ELSS Tax Saver Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-elss-tax-saver-fund-(formerly-known-as-sbi-long-term-equity-fund)-3",
    "SBI Large Cap Fund": "https://www.sbimf.com/sbimf-scheme-details/sbi-large-cap-fund-(formerly-known-as-sbi-bluechip-fund)-43",
}

NA = "Data not available at this moment"


def clean_text(s: str) -> str:
    """Remove HTML/extra spacing; keep ₹ and %."""
    if not s or not isinstance(s, str):
        return NA
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s if s else NA


def _get_text(el) -> str:
    if el is None:
        return ""
    return (el.get_text(strip=True) if hasattr(el, "get_text") else str(el)).strip()


def extract_overview_from_html(html: str) -> dict:
    """Parse Overview section from full page HTML."""
    overview = {}
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body") or soup
    text = body.get_text() if body else ""
    if "Expense ratio" not in text and "Overview" not in text:
        return overview

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            row_text = " ".join(_get_text(c) for c in cells)
            if "Expense ratio" in row_text:
                m = re.search(r"(\d+\.?\d*%?)", row_text)
                overview["expense_ratio"] = m.group(1) if m else NA
            elif "Lock In" in row_text or "Lock-in" in row_text:
                overview["lock_in"] = "No Lock-in" if ("No Lock" in row_text or "No Lock-in" in row_text) else (re.search(r"\d+\s*Years?", row_text, re.I).group(0).strip() if re.search(r"\d+\s*Years?", row_text, re.I) else NA)
            elif "Min Lumpsum" in row_text or "Lumpsum/SIP" in row_text:
                m = re.search(r"[/–-]\s*(₹?\s*[\d,]+|--)", row_text)
                overview["min_sip"] = m.group(1).strip() if m else ("--" if "--" in row_text else NA)
            elif "Exit Load" in row_text:
                val = row_text.replace("Exit Load", "").strip()
                if re.search(r"\d+%", val) or "redeem" in val.lower() or "Years" in val:
                    overview["exit_load"] = val or NA
            elif "Risk" in row_text and "risk" not in overview:
                risk_val = row_text.replace("Risk", "").strip()
                if any(x in risk_val for x in ["Very", "High", "Low", "Moderate"]):
                    overview["risk"] = risk_val or NA
            elif "Benchmark" in row_text:
                parts = row_text.split("Benchmark", 1)
                if len(parts) > 1:
                    overview["benchmark"] = parts[1].strip() or NA
            elif "AUM" in row_text and "₹" in row_text:
                m = re.search(r"₹\s*[\d,.K]+\s*Cr?", row_text)
                overview["aum"] = m.group(0).strip() if m else NA
            elif "Inception" in row_text:
                m = re.search(r"(\d{1,2}\s+\w+\s*,?\s*\d{4})", row_text)
                overview["inception_date"] = m.group(1).strip() if m else NA
            elif "TurnOver" in row_text or "Turnover" in row_text:
                m = re.search(r"(\d+\.?\d*%?)", row_text)
                overview["turnover"] = m.group(1) if m else NA

    if not overview:
        lines = [l.strip() for l in re.split(r"[\n\t]+", text) if l.strip()]
        for line in lines:
            if "Expense ratio" in line:
                m = re.search(r"(\d+\.?\d*%?)", line)
                overview["expense_ratio"] = m.group(1) if m else NA
            elif ("Lock In" in line or "No Lock-in" in line) and "lock_in" not in overview:
                overview["lock_in"] = "No Lock-in" if "No Lock" in line else (re.search(r"\d+\s*Years?", line, re.I).group(0) if re.search(r"\d+\s*Years?", line, re.I) else NA)
            elif ("Lumpsum/SIP" in line or ("Min " in line and "SIP" in line)) and "min_sip" not in overview:
                m = re.search(r"[/–-]\s*(₹?\s*[\d,]+|--)", line)
                overview["min_sip"] = m.group(1).strip() if m else "--"
            elif "Exit Load" in line and "exit_load" not in overview:
                overview["exit_load"] = line.replace("Exit Load", "").strip() or NA
            elif "Risk" in line and any(x in line for x in ["Very", "High", "Low", "Moderate"]):
                overview["risk"] = line.replace("Risk", "").strip() or NA
            elif "Benchmark" in line and "benchmark" not in overview:
                overview["benchmark"] = line.replace("Benchmark", "").strip() or NA
            elif "AUM" in line and "₹" in line:
                m = re.search(r"₹\s*[\d,.K]+\s*Cr?", line)
                overview["aum"] = m.group(0).strip() if m else NA
            elif "Inception Date" in line:
                m = re.search(r"(\d{1,2}\s+\w+\s*,?\s*\d{4})", line)
                overview["inception_date"] = m.group(1).strip() if m else NA
            elif "TurnOver" in line or "Turnover" in line:
                m = re.search(r"(\d+\.?\d*%?)", line)
                overview["turnover"] = m.group(1) if m else NA
    return overview


def extract_aum_from_text(text: str) -> str:
    """Fallback AUM extraction from full page text (e.g. AUM ₹31862 Cr or ₹ 31.9K Cr)."""
    m = re.search(r"AUM\s*₹\s*([\d,.K]+)\s*Cr", text, re.I)
    if m:
        return "₹" + m.group(1).strip() + " Cr"
    m = re.search(r"₹\s*([\d,.K]+)\s*Cr", text)
    if m:
        return "₹" + m.group(1).strip() + " Cr"
    return NA


def extract_fund_manager_name(soup: BeautifulSoup) -> str:
    """Extract only the fund manager name (e.g. Milind Agrawal), not the sentence."""
    body = soup.find("body") or soup
    text = body.get_text() if body else ""
    m = re.search(r"Fund Manager\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*Fund Manager of ", text)
    if m:
        return m.group(1).strip()
    el = body.find(string=re.compile(r"Fund Manager of ", re.I))
    if not el:
        return NA
    parent = el.find_parent(["div", "section", "p", "li"])
    if parent:
        for tag in parent.find_all(["h2", "h3", "h4", "h5"]):
            name = _get_text(tag)
            if name and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$", name) and "Fund" not in name:
                return name
    block = el.find_parent(["div", "section", "p", "li"])
    for _ in range(8):
        if not block:
            break
        t = _get_text(block)
        if "Fund Manager of " not in t:
            block = block.find_parent(["div", "section"])
            continue
        m = re.search(r"Fund Manager\s*([A-Z][a-z]+\s+[A-Z][a-z]+)\s*Fund Manager of ", t)
        if m:
            return m.group(1).strip()
        lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
        for line in lines:
            if "Fund Manager of " in line or "since " in line.lower() or line == "Fund Manager":
                continue
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$", line) and len(line) < 50:
                return line
        block = block.find_parent(["div", "section"])
    return NA


def extract_nav_from_faq(soup: BeautifulSoup) -> str:
    """Extract NAV value from FAQ text (e.g. 'The NAV of the fund today is ₹465.85')."""
    body = soup.find("body") or soup
    text = body.get_text() if body else ""
    m = re.search(r"(?:The )?NAV of the fund today is\s*(₹\s*[\d.]+)", text, re.I)
    if m:
        return m.group(1).strip().rstrip(".")
    m = re.search(r"NAV of the fund today is\s*(₹\s*[\d.]+)", text, re.I)
    if m:
        return m.group(1).strip().rstrip(".")
    return NA


def extract_fund_vs_competition_reduced(text: str) -> str:
    """Keep only summary sentence and This Fund row as 1M: x%, 3M: x%, etc."""
    out = []
    summary = re.search(r"The fund has (?:out|under)performed[^.]+\.", text)
    if summary:
        out.append(summary.group(0).strip())
    lines = text.split("\n")
    for line in lines:
        if "This Fund" in line:
            percents = re.findall(r"(-?\d+\.?\d*%|--)", line)
            periods = ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
            values = percents[:6] if len(percents) >= 6 else percents
            row = "\n".join(f"{p}: {v}" for p, v in zip(periods[: len(values)], values))
            out.append(row)
            break
    if len(out) < 2 and "This Fund" in text:
        rest = text.split("This Fund", 1)[1][:400]
        percents = re.findall(r"(-?\d+\.?\d*%|--)", rest)
        periods = ["1M", "3M", "6M", "1Y", "3Y", "5Y"]
        values = percents[:6] if len(percents) >= 6 else percents
        row = "\n".join(f"{p}: {v}" for p, v in zip(periods[: len(values)], values))
        out.append(row)
    return "\n\n".join(out) if out else text[:1500]


def extract_positive_negative(text: str) -> str:
    """Extract Positive and Negative bullet points for Info 16."""
    pos_lines = []
    neg_lines = []
    in_positive = False
    in_negative = False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if "Positive" in line and ":" in line:
            in_positive = True
            in_negative = False
            continue
        if "Negative" in line and ":" in line:
            in_negative = True
            in_positive = False
            continue
        if in_positive and line and not line.startswith("Positive"):
            pos_lines.append(line)
        if in_negative and line and not line.startswith("Negative"):
            neg_lines.append(line)
    if not pos_lines and not neg_lines:
        pos_m = re.findall(r"Positive:\s*(.+?)(?=Negative:|$)", text, re.S)
        neg_m = re.findall(r"Negative:\s*(.+?)(?=Positive:|$)", text, re.S)
        if pos_m:
            pos_lines = [ln.strip() for ln in pos_m[0].split("\n") if ln.strip()]
        if neg_m:
            neg_lines = [ln.strip() for ln in neg_m[0].split("\n") if ln.strip()]
    pos_str = "\n".join(pos_lines) if pos_lines else "No positive points found"
    neg_str = "\n".join(neg_lines) if neg_lines else "No bad points found for this fund"
    return f"Positive:\n{pos_str}\n\nNegative:\n{neg_str}"


def _plausible_return_pct(s: str) -> bool:
    """True if string looks like a return percentage (e.g. 3.7, 8.8), not a year or large number."""
    try:
        v = float(s.replace("%", "").strip())
        return -50 <= v <= 200
    except Exception:
        return False


def extract_returns_calculator_only(text: str) -> str:
    """Extract 1-time and SIP Absolute Return %. Format: '1-time Absolute Return 8.8% SIP Absolute Return 3.7%'."""
    all_matches = re.findall(r"Absolute Return\s*(-?\d+\.?\d*%?)", text, re.I)
    candidates = [m if m.endswith("%") else f"{m}%" for m in all_matches if _plausible_return_pct(m.replace("%", ""))]
    onetime_pct = candidates[0] if len(candidates) >= 1 else None
    sip_pct = candidates[1] if len(candidates) >= 2 else None
    if onetime_pct is not None or sip_pct is not None:
        return f"1-time Absolute Return {onetime_pct or 'N/A'} SIP Absolute Return {sip_pct or 'N/A'}"
    pcts = re.findall(r"\b(\d+\.?\d*)%", text)
    plausible = [p for p in pcts if _plausible_return_pct(p)]
    if "Total Investment" in text and "Profit" in text and len(plausible) >= 2:
        return f"1-time Absolute Return {plausible[0]}% SIP Absolute Return {plausible[1]}%"
    return NA


def extract_asset_allocation_text(text: str) -> str:
    """Extract Equity/Debt & Cash etc. with percentages. Output: 'Equity 96.2%, Debt & Cash 3.8%'."""
    parts = []
    for m in re.finditer(r"(Equity|Debt\s*&\s*Cash|Cash\s*Equivalent)\s*(\d+\.?\d*%)", text, re.I):
        parts.append(f"{m.group(1).strip()} {m.group(2)}")
    if parts:
        return ", ".join(parts)
    for m in re.finditer(r"(\d+\.?\d*%)\s*(?:Equity|Debt|Cash)", text, re.I):
        pct = m.group(1)
        rest = text[m.start() : m.end() + 20]
        if "Equity" in rest:
            parts.append(f"Equity {pct}")
        elif "Debt" in rest or "Cash" in rest:
            parts.append(f"Debt & Cash {pct}")
    if parts:
        return ", ".join(parts)
    if "Equity" in text and "Debt" in text:
        pcts = re.findall(r"\d+\.?\d*%", text)
        if len(pcts) >= 2:
            return f"Equity {pcts[0]}, Debt & Cash {pcts[1]}"
    if "Equity" in text:
        pct = re.search(r"Equity\s*(\d+\.?\d*%)", text, re.I)
        if pct:
            return f"Equity {pct.group(1)}"
    if "Debt" in text or "Cash" in text:
        pct = re.search(r"(?:Debt\s*&\s*Cash|Cash)\s*(\d+\.?\d*%)", text, re.I)
        if pct:
            return f"Debt & Cash {pct.group(1)}"
    pcts = re.findall(r"\d+\.?\d*%", text)
    if "Equity" in text and "Debt" in text and len(pcts) >= 2:
        return f"Equity {pcts[0]}, Debt & Cash {pcts[1]}"
    if "Equity" in text and len(pcts) >= 1:
        return f"Equity {pcts[0]}"
    if ("Debt" in text or "Cash" in text) and len(pcts) >= 1:
        return f"Debt & Cash {pcts[0]}"
    return NA


def clean_about_text(text: str) -> str:
    """Add missing spaces, remove 'Know more' and all text after, remove nav/duplicate content, preserve factual content."""
    if not text or not text.strip():
        return NA
    for sep in [r"\bKnow\s+more\s+about\b", r"\bKnow\s+more\s*,", r"\bKnow\s+more\b.*$", r"Learn\s+more\s+about", r"AUM\s+Change\s+All\s+changes"]:
        idx = re.search(sep, text, re.I)
        if idx:
            text = text[: idx.start()].strip()
            break
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"About\s+SBI\s+[\w\s]+Fund\s*", " ", text, flags=re.I)
    text = re.sub(r"(?<=[a-z])([A-Z][a-z])", r" \1", text)
    text = re.sub(r"(?<=\.)([A-Z])", r" \1", text)
    text = re.sub(r"Parameters\s+Jan.*$", "", text, flags=re.S)
    text = re.sub(r"\s+Know\s+more\s*,?\s*since\s+\d+.*$", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    if text.startswith(". "):
        text = text[2:].strip()
    return text if text else NA


def extract_how_to_invest_steps(text: str) -> str:
    """Extract only the investment steps. Format: 1. Download... 2. Search... 3. Choose... 4. Enter... 5. Complete..."""
    if not text or "INDmoney" not in text:
        return NA
    steps = []
    download = re.search(r"Download\s+the\s+INDmoney\s+app\.?", text, re.I)
    search = re.search(r"Search\s+for\s+[^.]+\.", text, re.I)
    select = re.search(r"Select\s+whether\s+you\s+want\s+to\s+invest\s+in\s+SIP\s+or\s+lump\s+sum\.?", text, re.I) or re.search(r"Choose\s+SIP\s+or\s+lump\s+sum\.?", text, re.I)
    enter = re.search(r"Enter\s+the\s+amount\s+you\s+wish\s+to\s+invest\.?", text, re.I)
    payment = re.search(r"Set\s+up\s+payments\s+via\s+bank\s+mandate\s+or\s+UPI\.?", text, re.I) or re.search(r"Complete\s+payment\s+using\s+bank\s+mandate\s+or\s+UPI\.?", text, re.I)
    if download:
        steps.append("1. Download the INDmoney app.")
    if search:
        steps.append("2. Search for the fund.")
    if select:
        steps.append("3. Choose SIP or lump sum.")
    if enter:
        steps.append("4. Enter the investment amount.")
    if payment:
        steps.append("5. Complete payment using bank mandate or UPI.")
    return " ".join(steps) if steps else NA


def _clean_pos_neg_output(s: str) -> str:
    """Remove 'See all' and trailing junk from Positive/Negative block output."""
    if not s:
        return s
    original = s
    s = s.split("Returns Calculator")[0].split("Calculate SIP")[0].strip()
    s = re.sub(r"See all[^N]*", "", s)
    s = re.sub(r"\d+--\s*", "", s)
    neg = "Negative: No bad points found for this fund."
    if "5Y returns in the bottom" in original or "5Y returns in the bottom" in s:
        neg = "Negative: 5Y returns in the bottom 25% of the category."
    elif "3Y returns in the bottom" in original or "3Y returns in the bottom" in s:
        neg = "Negative: 3Y returns in the bottom 25% of the category."
    pos_parts = [p.strip() for p in s.split("Positive:") if p.strip() and not p.strip().isdigit()]
    pos_lines = []
    for p in pos_parts:
        if "Negative:" in p:
            p = p.split("Negative:")[0].strip()
        if p and len(p) > 4 and "See all" not in p:
            pos_lines.append(f"Positive: {p}")
    return "\n".join(pos_lines[:5]) + "\n" + neg if pos_lines else neg


def extract_positive_negative_from_full_text(text: str) -> str:
    """Extract Positive and Negative points from full page (labels or bullet phrases)."""
    pos_lines = []
    neg_lines = []
    for m in re.finditer(r"Positive:\s*([^\n]+)", text, re.I):
        s = m.group(1).strip()
        if "See all" in s or re.match(r"^[\d\s\-–]+$", s) or len(s) < 5:
            continue
        if any(x in s for x in ["Consistent", "benchmark", "volatility", "downside", "Outperformed", "AUM", "Beats FD", "Larger"]):
            pos_lines.append(f"Positive: {s.split('See all')[0].strip()}")
    for m in re.finditer(r"Negative:\s*([^\n]+)", text, re.I):
        s = m.group(1).strip()
        if "See all" in s or re.match(r"^[\d\s\-–]+$", s):
            continue
        if "No bad points" in s or "bottom" in s or "Underperforms" in s or "Has not" in s:
            neg_lines.append(f"Negative: {s.split('See all')[0].strip()}")
    if pos_lines or neg_lines:
        pos_str = "\n".join(pos_lines) if pos_lines else "No positive points found"
        neg_str = "\n".join(neg_lines) if neg_lines else "No bad points found for this fund."
        return f"{pos_str}\n{neg_str}"
    positives = []
    for phrase in ["Generated Consistent Returns", "Consistently beats benchmark", "Lower probablity of downside risk", "Lower volatility within category", "Outperformed benchmarks during bull run", "Larger AUM within category", "Beats FD returns"]:
        if phrase in text:
            positives.append(f"Positive: {phrase}")
    if "No bad points found for this fund" in text:
        neg_str = "Negative: No bad points found for this fund."
    elif "5Y returns in the bottom" in text or "3Y returns in the bottom" in text:
        neg_m = re.search(r"([^.]+(?:bottom\s*\d+%[^.]*\.))", text)
        neg_str = f"Negative: {neg_m.group(1).strip()}" if neg_m else "Negative: No bad points found for this fund."
    else:
        neg_str = "Negative: No bad points found for this fund."
    if positives:
        return "\n".join(positives) + "\n" + neg_str
    return NA


def extract_section_text(soup: BeautifulSoup, *anchor_texts: str, max_chars: int = 15000) -> str:
    """Find an element containing any of the anchor texts and return its parent section text."""
    body = soup.find("body") or soup
    for anchor in anchor_texts:
        el = body.find(string=re.compile(re.escape(anchor), re.I))
        if el:
            parent = el.find_parent(["section", "div", "article"])
            for _ in range(8):
                if parent is None:
                    break
                t = _get_text(parent)
                if len(t) > 50 and anchor[:20].lower() in t.lower():
                    return t[:max_chars]
                parent = parent.find_parent(["section", "div", "article"])
    return ""


def get_driver():
    """Create headless Chrome driver (webdriver-manager installs matching chromedriver)."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


def scrape_url(driver: webdriver.Chrome, url: str) -> dict:
    """Extract Info 1-17 from one INDMoney fund page. Uses Selenium for rendered HTML."""
    raw = {
        "source_url": url,
        "fund_name": "",
        "info_1_expense_ratio": NA,
        "info_2_lock_in": NA,
        "info_3_min_sip": NA,
        "info_4_exit_load": NA,
        "info_5_risk": NA,
        "info_6_benchmark": NA,
        "info_7_aum": NA,
        "info_8_inception_date": NA,
        "info_9_turnover": NA,
        "info_10_about": NA,
        "info_11_fund_manager": NA,
        "info_12_how_to_invest": NA,
        "info_13_nav": NA,
        "info_14_fund_vs_competition": NA,
        "info_15_ranking": NA,
        "info_16_ranking_pos_neg": NA,
        "info_17_returns_calculator": NA,
        "statement_url": "",
    }

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Expense ratio') or contains(text(), 'Overview') or contains(text(), 'AUM')]"))
        )
        time.sleep(2)
        for scroll_text in ["Ranking and Peer Comparison", "Returns Calculator"]:
            try:
                el = driver.find_element(By.XPATH, f"//*[contains(text(), '{scroll_text}')]")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                time.sleep(1.2)
            except Exception:
                pass
        time.sleep(1)
        html = driver.page_source
    except Exception:
        raw["fund_name"] = url.rstrip("/").split("/")[-1].replace("-", " ")
        return raw

    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text()

    # Fund name from h1 or title
    h1 = soup.find("h1")
    if h1:
        raw["fund_name"] = clean_text(_get_text(h1))
    if not raw["fund_name"]:
        title = soup.find("title")
        raw["fund_name"] = clean_text(_get_text(title).split("|")[0].strip()) if title else url.rstrip("/").split("/")[-1].replace("-", " ").title()

    # Overview (1-9)
    overview = extract_overview_from_html(html)
    raw["info_1_expense_ratio"] = overview.get("expense_ratio", NA)
    raw["info_2_lock_in"] = overview.get("lock_in", NA)
    raw["info_3_min_sip"] = overview.get("min_sip", NA)
    raw["info_4_exit_load"] = overview.get("exit_load", NA)
    raw["info_5_risk"] = overview.get("risk", NA)
    raw["info_6_benchmark"] = overview.get("benchmark", NA)
    raw["info_7_aum"] = overview.get("aum", NA)
    if raw["info_7_aum"] == NA:
        raw["info_7_aum"] = extract_aum_from_text(full_text)
    raw["info_8_inception_date"] = overview.get("inception_date", NA)
    raw["info_9_turnover"] = overview.get("turnover", NA)

    # 10 - About (Investment objective, Key Parameters, etc.) – cleaned
    about = extract_section_text(soup, "Investment objective", "Key Parameters", "About ", "equity fund", max_chars=8000)
    if about:
        raw["info_10_about"] = clean_about_text(clean_text(about))

    # 11 - Fund Manager (name only, e.g. Milind Agrawal)
    raw["info_11_fund_manager"] = extract_fund_manager_name(soup)
    if raw["info_11_fund_manager"] == NA:
        fm_el = soup.find(string=re.compile(r"Fund Manager of ", re.I))
        if fm_el and fm_el.find_previous_sibling():
            prev = fm_el.find_previous_sibling()
            if prev and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$", _get_text(prev)):
                raw["info_11_fund_manager"] = _get_text(prev)

    # 12 - How do I invest (FAQ) – steps only
    how_el = soup.find(string=re.compile(r"How do I invest", re.I))
    if how_el:
        block = how_el.find_parent(["div", "section", "li"])
        for _ in range(5):
            if block and "INDmoney" in _get_text(block):
                raw["info_12_how_to_invest"] = extract_how_to_invest_steps(_get_text(block)[:3000])
                break
            block = block.find_parent(["div", "section"]) if block else None

    # 13 - NAV (from FAQ fallback: "The NAV of the fund today is ₹465.85")
    raw["info_13_nav"] = extract_nav_from_faq(soup)

    # 14 - Fund vs Competition (summary + This Fund row only: 1M: x%, 3M: x%, ...)
    perf_el = soup.find(string=re.compile(r"Fund returns vs Benchmark", re.I))
    if perf_el:
        block = perf_el.find_parent(["div", "section", "table"])
        for _ in range(6):
            if block:
                t = _get_text(block)
                if "This Fund" in t and ("1M" in t or "1Y" in t):
                    raw["info_14_fund_vs_competition"] = extract_fund_vs_competition_reduced(t)
                    break
            block = block.find_parent(["div", "section"]) if block else None

    # 15 - Ranking ("Ranked X out of Y ... as per INDmoney")
    rank_el = soup.find(string=re.compile(r"Ranked \d+ out of \d+", re.I))
    if rank_el:
        raw["info_15_ranking"] = clean_text(rank_el)
        table = rank_el.find_parent("table") or (rank_el.find_parent("div") and rank_el.find_parent("div").find("table"))
        if table:
            first_row = table.find("tr")
            if first_row:
                raw["info_15_ranking"] = raw["info_15_ranking"] + "\n" + clean_text(_get_text(first_row))

    # 16 - Fund Ranking (Positive and Negative) – from full page then block
    raw["info_16_ranking_pos_neg"] = extract_positive_negative_from_full_text(full_text)
    if raw["info_16_ranking_pos_neg"] == NA:
        pos_neg_el = soup.find(string=re.compile(r"Lower volatility|Positive:|Negative:|5Y returns", re.I))
        if pos_neg_el:
            block = pos_neg_el.find_parent(["div", "section"])
            for _ in range(6):
                if block:
                    t = _get_text(block)
                    if ("Positive" in t or "Negative" in t or "volatility" in t) and len(t) < 2500:
                        raw["info_16_ranking_pos_neg"] = extract_positive_negative(t)
                        break
                block = block.find_parent(["div", "section"]) if block else None
    if raw["info_16_ranking_pos_neg"] == NA:
        raw["info_16_ranking_pos_neg"] = "Data not available"
    else:
        raw["info_16_ranking_pos_neg"] = _clean_pos_neg_output(raw["info_16_ranking_pos_neg"])

    # 17 - Returns Calculator (1-time and SIP Absolute Return %) – from HTML then from driver
    calc_el = soup.find(string=re.compile(r"Returns Calculator", re.I))
    if calc_el:
        block = calc_el.find_parent(["div", "section"])
        for _ in range(6):
            if block:
                t = _get_text(block)
                if "Absolute Return" in t or "Total Investment" in t:
                    raw["info_17_returns_calculator"] = extract_returns_calculator_only(t)
                    break
            block = block.find_parent(["div", "section"]) if block else None
    if raw["info_17_returns_calculator"] == NA:
        raw["info_17_returns_calculator"] = extract_returns_calculator_only(full_text)
    if raw["info_17_returns_calculator"] == NA:
        try:
            calc_heading = driver.find_element(By.XPATH, "//*[contains(text(), 'Returns Calculator')]")
            container = calc_heading.find_element(By.XPATH, "./ancestor::*[contains(., 'Total Investment') or contains(., 'Absolute Return')][1]")
            calc_text = container.text
            raw["info_17_returns_calculator"] = extract_returns_calculator_only(calc_text)
        except Exception:
            pass
    if raw["info_17_returns_calculator"] == NA:
        try:
            onetime_btn = driver.find_element(By.XPATH, "//*[contains(text(), '1-time')]")
            onetime_btn.click()
            time.sleep(1.5)
            calc_el = driver.find_element(By.XPATH, "//*[contains(text(), 'Returns Calculator')]")
            parent = calc_el.find_element(By.XPATH, "./ancestor::*[position()<=8]")
            t1 = parent.text
            pcts = re.findall(r"Absolute Return\s*(-?\d+\.?\d*%?)", t1, re.I)
            pcts = [p if p.endswith("%") else f"{p}%" for p in pcts if _plausible_return_pct(p.replace("%", ""))]
            if not pcts:
                pcts = [p for p in re.findall(r"\b(\d+\.?\d*)%", t1) if _plausible_return_pct(p)]
            onetime_pct = pcts[0] if pcts else None
            sip_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'SIP') and not(contains(text(), 'lump'))]")
            sip_btn.click()
            time.sleep(1.5)
            t2 = parent.text
            pcts2 = re.findall(r"Absolute Return\s*(-?\d+\.?\d*%?)", t2, re.I)
            pcts2 = [p if p.endswith("%") else f"{p}%" for p in pcts2 if _plausible_return_pct(p.replace("%", ""))]
            if not pcts2:
                pcts2 = [p for p in re.findall(r"\b(\d+\.?\d*)%", t2) if _plausible_return_pct(p)]
            sip_pct = pcts2[0] if pcts2 else None
            if onetime_pct or sip_pct:
                raw["info_17_returns_calculator"] = f"1-time Absolute Return {onetime_pct or 'N/A'} SIP Absolute Return {sip_pct or 'N/A'}"
        except Exception:
            pass

    # Statement URL (SBI scheme-details for factsheets, KIM/SID, statements)
    raw["statement_url"] = STATEMENT_URLS.get(raw["fund_name"], "")

    # Try __NEXT_DATA__ for richer data if HTML had little
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            data = json.loads(script.string)
            props = data.get("props", {}).get("pageProps", {})
            # Map common Next.js fund keys if present
            if not raw["fund_name"] and props.get("fundName"):
                raw["fund_name"] = clean_text(props["fundName"])
            if raw["info_1_expense_ratio"] == NA and props.get("expenseRatio") is not None:
                raw["info_1_expense_ratio"] = str(props["expenseRatio"]) + "%"
            if raw["info_7_aum"] == NA and props.get("aum"):
                raw["info_7_aum"] = "₹" + str(props["aum"]).replace(",", "") + " Cr" if isinstance(props["aum"], (int, float)) else str(props["aum"])
        except Exception:
            pass

    return raw


def build_cleaned(raw: dict) -> dict:
    """Produce cleaned record (same keys, cleaned values)."""
    cleaned = {}
    for k, v in raw.items():
        cleaned[k] = clean_text(str(v)) if v else NA
    return cleaned


def build_review_entry(cleaned: dict) -> dict:
    """One fund entry for data_review.json with readable labels (Info 1-17, Source URL, Statement URL)."""
    return {
        "Mutual Fund Name": cleaned.get("fund_name", NA),
        "Info 1 - Expense ratio": cleaned.get("info_1_expense_ratio", NA),
        "Info 2 - Lock In": cleaned.get("info_2_lock_in", NA),
        "Info 3 - Minimum SIP": cleaned.get("info_3_min_sip", NA),
        "Info 4 - Exit Load": cleaned.get("info_4_exit_load", NA),
        "Info 5 - Risk": cleaned.get("info_5_risk", NA),
        "Info 6 - Benchmark": cleaned.get("info_6_benchmark", NA),
        "Info 7 - AUM": cleaned.get("info_7_aum", NA),
        "Info 8 - Inception Date": cleaned.get("info_8_inception_date", NA),
        "Info 9 - TurnOver": cleaned.get("info_9_turnover", NA),
        "Info 10 - About (Fund)": cleaned.get("info_10_about", NA),
        "Info 11 - Fund Manager": cleaned.get("info_11_fund_manager", NA),
        "Info 12 - How Do I Invest": cleaned.get("info_12_how_to_invest", NA),
        "Info 13 - NAV": cleaned.get("info_13_nav", NA),
        "Info 14 - Fund vs Competition": cleaned.get("info_14_fund_vs_competition", NA),
        "Info 15 - Fund Comparison": cleaned.get("info_15_ranking", NA),
        "Info 16 - Fund Pros and Cons": cleaned.get("info_16_ranking_pos_neg", NA),
        "Info 17 - Fund Returns Calculator": cleaned.get("info_17_returns_calculator", NA),
        "Source URL": cleaned.get("source_url", ""),
        "Statement URL": cleaned.get("statement_url", ""),
    }


def main():
    driver = None
    try:
        driver = get_driver()
        all_cleaned = []
        for url in URLS:
            slug = url.rstrip("/").split("/")[-1]
            print(f"Scraping: {slug}")
            try:
                raw = scrape_url(driver, url)
                raw_path = RAW_DIR / f"raw_{slug}.json"
                with open(raw_path, "w", encoding="utf-8") as f:
                    json.dump(raw, f, indent=2, ensure_ascii=False)
                cleaned = build_cleaned(raw)
                cleaned_path = CLEANED_DIR / f"cleaned_{slug}.json"
                with open(cleaned_path, "w", encoding="utf-8") as f:
                    json.dump(cleaned, f, indent=2, ensure_ascii=False)
                all_cleaned.append(cleaned)
            except Exception as e:
                print(f"Error for {url}: {e}")
                all_cleaned.append(build_cleaned({"fund_name": slug, "source_url": url}))

        review_data = {"funds": [build_review_entry(c) for c in all_cleaned]}
        review_path = PHASE_DIR / "data_review.json"
        with open(review_path, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {review_path}")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
