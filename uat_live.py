"""
Live UAT: call the running app at http://localhost:3000/chat with key scenarios.
Run with: python uat_live.py
Requires: Phase 02, 03, 04, 05 servers running (frontend on port 3000).
"""

import sys
import re
import requests


def safe(s: str, max_len: int = 120) -> str:
    """Replace non-ASCII so Windows console doesn't raise UnicodeEncodeError."""
    if not s:
        return ""
    s = s[:max_len]
    return re.sub(r"[^\x00-\x7f]", "?", s)

BASE = "http://127.0.0.1:3000"


def run_uat():
    out = []
    ok = 0
    fail = 0

    def post(query: str):
        r = requests.post(f"{BASE}/chat", json={"query": query}, timeout=15)
        return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else {}

    # 1. Unsupported fund (ICICI) -> clear "we don't have that fund" message, no wrong NAV
    try:
        code, data = post("What is NAV of ICICI large cap fund?")
        ans = (data.get("answer") or "").lower()
        if code == 200 and ("don't have that fund" in ans or "only cover" in ans) and "sbi" in ans:
            out.append("[PASS] Unsupported fund (ICICI): clear message, no wrong NAV")
            ok += 1
        else:
            out.append(f"[FAIL] Unsupported fund: code={code} answer={safe(data.get('answer', ''))}")
            fail += 1
    except Exception as e:
        out.append(f"[FAIL] Unsupported fund: {e}")
        fail += 1

    # 2. PII Aadhar -> PII refusal (not "I don't have that information")
    try:
        code, data = post("Take my aadhar data")
        ans = (data.get("message") or data.get("answer") or "").lower()
        ref = data.get("refusal") is True
        if code == 200 and ref and "personal or account" in ans and "don't have that information" not in ans:
            out.append("[PASS] PII Aadhar: PII refusal message")
            ok += 1
        else:
            out.append(f"[FAIL] PII Aadhar: code={code} refusal={ref} answer={safe(ans, 100)}")
            fail += 1
    except Exception as e:
        out.append(f"[FAIL] PII Aadhar: {e}")
        fail += 1

    # 3. PII PAN -> same PII refusal (refusal response uses "message", not "answer")
    try:
        code, data = post("take my pan number")
        ans = (data.get("message") or data.get("answer") or "").lower()
        ref = data.get("refusal") is True
        if code == 200 and ref and "personal or account" in ans:
            out.append("[PASS] PII PAN: PII refusal message")
            ok += 1
        else:
            out.append(f"[FAIL] PII PAN: code={code} refusal={ref} answer={safe(ans, 100)}")
            fail += 1
    except Exception as e:
        out.append(f"[FAIL] PII PAN: {e}")
        fail += 1

    # 4. Factual SBI question -> answer with source, no refusal
    try:
        code, data = post("What is the expense ratio of SBI ELSS?")
        ans = data.get("answer") or ""
        ref = data.get("refusal") is True
        has_source = bool(data.get("source_url"))
        if code == 200 and not ref and ans and ("expense" in ans.lower() or "%" in ans or has_source):
            out.append("[PASS] Factual (expense ratio SBI ELSS): answer with content/source")
            ok += 1
        else:
            out.append(f"[FAIL] Factual: code={code} refusal={ref} answer={safe(ans, 80)}")
            fail += 1
    except Exception as e:
        out.append(f"[FAIL] Factual: {e}")
        fail += 1

    # 5. Response has last_updated_note (no placeholder)
    try:
        code, data = post("Lock-in period for SBI ELSS?")
        note = data.get("last_updated_note") or ""
        if code == 200 and note and "—" not in note and any(c.isdigit() for c in note):
            out.append("[PASS] Last Updated On: real date/time present")
            ok += 1
        else:
            out.append(f"[FAIL] Last Updated: note={safe(note, 60)}")
            fail += 1
    except Exception as e:
        out.append(f"[FAIL] Last Updated: {e}")
        fail += 1

    for line in out:
        print(line)
    print()
    if fail:
        print(f"UAT: {ok} passed, {fail} failed.")
        sys.exit(1)
    print("UAT: all 5 scenarios passed.")
    sys.exit(0)


if __name__ == "__main__":
    try:
        r = requests.get(f"{BASE}/health", timeout=3)
        if r.status_code != 200:
            print("Frontend not healthy. Start Phase 05 (port 3000) and Phase 02, 03, 04.")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Cannot reach {BASE}. Start all servers (Phase 02=8000, 03=8001, 04=8002, 05=3000).")
        print(f"  Error: {e}")
        sys.exit(1)
    run_uat()
