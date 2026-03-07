"""
Phase 01 - Data: Full pipeline (scrape -> chunk -> embed -> manifest).
Run from this directory: python run_data_phase.py
Optional: python run_data_phase.py --skip-scrape  (use existing raw/cleaned, only chunk+embed).
Writes last_scraped.txt with timestamp when pipeline completes (for UI "Last Updated On").
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PHASE_DIR = Path(__file__).resolve().parent
LAST_SCRAPED_FILE = PHASE_DIR / "last_scraped.txt"


def main():
    parser = argparse.ArgumentParser(description="Run Phase 1 Data pipeline")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping; use existing cleaned/ only")
    args = parser.parse_args()

    if not args.skip_scrape:
        print("Step 1/2: Scraping INDMoney pages (raw + cleaned + data_review.json) ...")
        r = subprocess.run([sys.executable, str(PHASE_DIR / "scrape.py")], cwd=str(PHASE_DIR))
        if r.returncode != 0:
            print("Scrape failed. Fix errors and re-run.")
            sys.exit(r.returncode)
    else:
        print("Step 1/2: Skipping scrape (using existing cleaned/).")

    print("Step 2/2: Chunking and embedding ...")
    r = subprocess.run([sys.executable, str(PHASE_DIR / "chunk_and_embed.py")], cwd=str(PHASE_DIR))
    if r.returncode != 0:
        print("Chunk/embed failed. Fix errors and re-run.")
        sys.exit(r.returncode)

    try:
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        LAST_SCRAPED_FILE.write_text(now.strftime("%d %b %Y, %I:%M %p IST"), encoding="utf-8")
    except Exception:
        try:
            LAST_SCRAPED_FILE.write_text(datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"), encoding="utf-8")
        except Exception:
            pass
    print("Phase 1 complete. Artifacts: raw/, cleaned/, chunks/, embeddings/, manifest/")


if __name__ == "__main__":
    main()
