"""
Run all phase tests together. Exits 0 only if every phase's tests pass.
Usage: from project root: python run_all_tests.py
       Or: pytest run_all_tests.py -v  (run_all_tests is a script, not pytest collection)
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

PHASES = [
    ("Phase 02- backend", "Backend (retrieval)"),
    ("Phase 03- llm_response", "LLM Response"),
    ("Phase 04- safety", "Safety"),
    ("Phase 05- frontend", "Frontend (orchestrator)"),
]


def run_pytest(phase_dir: Path, phase_name: str) -> bool:
    """Run pytest in phase_dir. Return True if all tests pass."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(phase_dir), timeout=120)
    return result.returncode == 0


def main():
    failed = []
    for rel_dir, label in PHASES:
        phase_dir = PROJECT_ROOT / rel_dir
        if not phase_dir.exists():
            print(f"[SKIP] {label}: directory not found ({rel_dir})")
            continue
        print(f"\n{'='*60}\n{label} ({rel_dir})\n{'='*60}")
        if run_pytest(phase_dir, label):
            print(f"[PASS] {label}")
        else:
            print(f"[FAIL] {label}")
            failed.append(label)

    print("\n" + "=" * 60)
    if failed:
        print("FAILED:", ", ".join(failed))
        sys.exit(1)
    print("All phases passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
