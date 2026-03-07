# Phase 06 — Scheduler

This phase keeps the **Data Phase** artifacts up to date by re-running the pipeline (scrape → clean → chunk → embed) on a schedule.

## Implementation: GitHub Actions

The scheduler is implemented as a **GitHub Actions workflow** that:

1. **Runs on a schedule** — Daily at **02:00 UTC** (e.g. 07:30 IST).
2. **Can be run manually** — In the GitHub repo: **Actions** → **Data pipeline (schedule)** → **Run workflow**.
3. **Runs the full pipeline** — `Phase 01- data/run_data_phase.py` (scrape INDMoney pages, then chunk and embed).
4. **Uploads artifacts** — Chunks, embeddings, manifest, cleaned data, and `last_scraped.txt` are uploaded as workflow artifacts so you can download them or use them in a later step (e.g. commit to a branch or deploy).

## Workflow file

- **Location:** `.github/workflows/data-pipeline-schedule.yml`
- **Triggers:** `schedule` (cron `0 2 * * *`) and `workflow_dispatch`
- **Job:** `run-data-pipeline` — checkout, set up Python, install Chrome (for Selenium), install Phase 01 dependencies, run `run_data_phase.py`, upload artifacts.

## Requirements

- Repository must be on **GitHub** (Actions run on GitHub-hosted runners).
- **Chrome** is installed in the runner via `browser-actions/setup-chrome@v1` for the scrape step.
- **Phase 01** `requirements.txt` is installed in the job (Selenium, sentence-transformers, etc.).

## Running the pipeline locally (same as Phase 01)

To run the same pipeline on your machine (e.g. for testing):

```bash
cd "Phase 01- data"
pip install -r requirements.txt
python run_data_phase.py
```

Optional: `python run_data_phase.py --skip-scrape` to only chunk and embed using existing `cleaned/` data.

## Artifacts produced

After each run, the workflow uploads:

| Artifact        | Path (under Phase 01- data) |
|-----------------|-----------------------------|
| Chunks          | `chunks/`                   |
| Embeddings      | `embeddings/`               |
| Manifest        | `manifest/`                 |
| Cleaned text    | `cleaned/`                  |
| Last updated    | `last_scraped.txt`          |
| Review file     | `data_review.json`          |

Download from the **Actions** run → **Artifacts** → **data-phase-artifacts**.

## Config

- **Schedule:** Edit the `cron` expression in `.github/workflows/data-pipeline-schedule.yml` if you want a different interval (e.g. weekly: `0 2 * * 0`).
- **Python version:** Set in the workflow under `actions/setup-python` (default `3.11`).

## Testing

See `tests/` in this folder (and repo root) for scheduler-related tests: workflow structure validation and pipeline run with `--skip-scrape`.
