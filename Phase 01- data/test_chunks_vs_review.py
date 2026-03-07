"""
Quick test: verify chunks.json is consistent with data_review.json.
Checks fund coverage, URL match, and that key review values appear in chunk text.
"""

import json
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parent
REVIEW_PATH = PHASE_DIR / "data_review.json"
CHUNKS_PATH = PHASE_DIR / "chunks" / "chunks.json"


def main():
    with open(REVIEW_PATH, "r", encoding="utf-8") as f:
        review = json.load(f)
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
    chunks = chunks_data["chunks"]

    funds = {f["Mutual Fund Name"]: f for f in review["funds"]}
    chunks_by_fund = {}
    for c in chunks:
        name = c["fund_name"]
        chunks_by_fund.setdefault(name, []).append(c)

    passed = 0
    failed = 0

    # 1) Every review fund has at least one chunk
    print("1. Fund coverage (every data_review fund has chunks):")
    for name, fund in funds.items():
        count = len(chunks_by_fund.get(name, []))
        if count >= 1:
            print(f"   OK  {name}: {count} chunks")
            passed += 1
        else:
            print(f"   FAIL {name}: 0 chunks")
            failed += 1

    # 2) Every chunk's fund_name exists in data_review
    print("\n2. Chunk fund names exist in data_review:")
    for c in chunks:
        if c["fund_name"] in funds:
            passed += 1
        else:
            print(f"   FAIL chunk {c['chunk_id']}: unknown fund_name '{c['fund_name']}'")
            failed += 1
    if not any(c["fund_name"] not in funds for c in chunks):
        print("   OK  All chunk fund names present in data_review.")

    # 3) For each fund, Source URL and Statement URL in chunks match data_review
    print("\n3. Source URL & Statement URL match data_review per fund:")
    for name, fund in funds.items():
        expected_src = fund.get("Source URL", "")
        expected_stmt = fund.get("Statement URL", "")
        for c in chunks_by_fund.get(name, []):
            if c["source_url"] != expected_src or c["statement_url"] != expected_stmt:
                print(f"   FAIL {name} chunk {c['chunk_id']}: URL mismatch")
                failed += 1
                break
        else:
            if chunks_by_fund.get(name):
                print(f"   OK  {name}: URLs match")
                passed += 1

    # 4) Spot-check: key values from data_review appear in combined chunk text per fund
    print("\n4. Spot-check: key fields from data_review appear in chunk text:")
    for name, fund in funds.items():
        full_text = " ".join(c["text"] for c in chunks_by_fund.get(name, []))
        checks = [
            ("Mutual Fund Name / fund name", name in full_text or name[:20] in full_text),
            ("Expense ratio", fund.get("Info 1 - Expense ratio", "") in full_text),
            ("Source URL", fund.get("Source URL", "") in full_text),
        ]
        all_ok = all(b for _, b in checks)
        if all_ok:
            print(f"   OK  {name}: fund name, expense ratio, source URL found in chunks")
            passed += 1
        else:
            for label, ok in checks:
                if not ok:
                    print(f"   FAIL {name}: '{label}' not found in chunk text")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Result: {passed} checks passed, {failed} failed.")
    if failed == 0:
        print("chunks.json is consistent with data_review.json.")
    else:
        print("Some checks failed; review above.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
