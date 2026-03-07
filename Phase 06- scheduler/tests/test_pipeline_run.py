"""
Phase 06 - Scheduler: test that the data pipeline can be run (--skip-scrape) and produces artifacts.
Requires Phase 01 cleaned/ data to exist. Run from project root: pytest "Phase 06- scheduler/tests/test_pipeline_run.py" -v
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PHASE01 = PROJECT_ROOT / "Phase 01- data"
RUN_SCRIPT = PHASE01 / "run_data_phase.py"


@pytest.fixture(scope="module")
def phase01_cleaned_exists():
    """Skip if Phase 01 cleaned/ has no data (needed for --skip-scrape)."""
    cleaned = PHASE01 / "cleaned"
    if not cleaned.exists():
        pytest.skip("Phase 01 cleaned/ not found")
    if not list(cleaned.glob("*.json")):
        pytest.skip("Phase 01 cleaned/ has no JSON files")
    return True


def test_run_data_phase_script_exists():
    """Phase 01 run_data_phase.py must exist (scheduler invokes it)."""
    assert RUN_SCRIPT.exists(), f"Missing {RUN_SCRIPT}"


def test_pipeline_skip_scrape_produces_artifacts(phase01_cleaned_exists):
    """Running run_data_phase.py --skip-scrape must produce chunks, embeddings, manifest, last_scraped."""
    result = subprocess.run(
        [sys.executable, str(RUN_SCRIPT), "--skip-scrape"],
        cwd=str(PHASE01),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr or result.stdout}"

    assert (PHASE01 / "chunks" / "chunks.json").exists()
    assert (PHASE01 / "manifest" / "manifest.json").exists()
    assert (PHASE01 / "last_scraped.txt").exists()
    assert (PHASE01 / "embeddings" / "chunk_metadata.json").exists()
    assert (PHASE01 / "embeddings" / "vectors.npy").exists()
