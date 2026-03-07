# Schedule configuration (reference)

The actual schedule is defined in GitHub Actions:

- **File:** `.github/workflows/data-pipeline-schedule.yml`
- **Cron:** `0 2 * * *` (daily at 02:00 UTC)
- **Manual:** `workflow_dispatch` (run from Actions tab)

No separate config file is required; this folder documents where the schedule lives.
