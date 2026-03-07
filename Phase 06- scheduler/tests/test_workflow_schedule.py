"""
Phase 06 - Scheduler: validate GitHub Actions workflow file exists and has required structure.
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "data-pipeline-schedule.yml"


def test_workflow_file_exists():
    """The scheduled data-pipeline workflow file must exist."""
    assert WORKFLOW_PATH.exists(), f"Missing {WORKFLOW_PATH}"


def test_workflow_has_schedule_and_dispatch():
    """Workflow must trigger on schedule and allow manual dispatch."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "cron:" in text
    assert "workflow_dispatch:" in text


def test_workflow_has_data_pipeline_job():
    """Workflow must define a job that runs the data pipeline."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "run-data-pipeline" in text or "run_data_pipeline" in text
    assert "run_data_phase.py" in text
    assert "Phase 01" in text


def test_workflow_has_required_steps():
    """Workflow must include checkout, Python, and pipeline run."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "actions/checkout" in text
    assert "setup-python" in text
    assert "run_data_phase.py" in text
