# Testing — All Phases Together

## Run all phase tests

From **project root**:

```bash
python run_all_tests.py
```

This runs pytest for Phase 02, 03, 04, and 05 in sequence. Exit code **0** only if every phase passes.

**Prerequisite:** Phase 01 must have been run at least once (so `Phase 01- data/chunks/chunks.json` and `Phase 01- data/embeddings/vectors.npy` exist). Otherwise Phase 02 tests will fail.

---

## What is tested

### Phase 02 — Backend (retrieval)
- Health, API validation, retrieve returns chunks with expected shape.
- Data Phase artifacts exist; load store; cosine similarity; search returns top-k with scores.
- **Integration:** Query "expense ratio SBI ELSS" returns at least one chunk containing "Expense ratio"; "ELSS lock in" returns relevant chunk.

### Phase 03 — LLM Response
- System prompt and helpers; chunks-to-context; citation from top chunk.
- **Empty chunks / no context** → no-info message.
- **Extraction-first:** Chunks with "Expense ratio: 0.89%" + query about expense ratio → answer contains "0.89%". Chunks with "Benchmark: BSE 100..." + query about benchmark → answer contains benchmark. (No LLM required.)

### Phase 04 — Safety
- Health, /check API. Factual questions → allowed; advice/opinion → refusal with message and educational link; PII → refusal; empty/whitespace → refused.

### Phase 05 — Frontend (orchestrator)
- Health, index HTML, static assets. /chat requires query; validation.
- **Refusal path:** Safety returns allowed=False → /chat returns refusal + educational_link.
- **Full flow (mocked):** Safety allows → Retrieve returns chunks → LLM returns answer → /chat returns 200 with answer, citation_url, last_updated_note; answer contains expected fact.
- **Empty chunks (mocked):** Retrieve returns no chunks → /chat returns clear "No matching data" message without calling LLM.

---

## Run a single phase

From that phase’s directory:

```bash
cd "Phase 02- backend"
python -m pytest tests/ -v
```

Same for `Phase 03- llm_response`, `Phase 04- safety`, `Phase 05- frontend`.

---

## Test count summary

| Phase | Test count (approx) |
|-------|----------------------|
| Phase 02 | 13 |
| Phase 03 | 18 |
| Phase 04 | 33 |
| Phase 05 | 8 |
| **Total** | **72** |

Success means all phases pass when you run `python run_all_tests.py`.

---

## Live UAT (against running servers)

To verify behaviour end-to-end against the real app:

1. **Start all services:** Phase 02 (port 8000), 03 (8001), 04 (8002), 05 (3000).
2. From **project root** run:

   ```bash
   python uat_live.py
   ```

   This calls `http://localhost:3000/chat` for five scenarios:
   - Unsupported fund (e.g. ICICI) → clear “we don’t have that fund” message
   - PII Aadhar → PII refusal (not “I don’t have that information”)
   - PII PAN → PII refusal
   - Factual (expense ratio SBI ELSS) → answer with content/source
   - Last Updated On → real date/time in response

3. If unsupported-fund or PII Aadhar fail, **restart Phase 04 and Phase 05** so they load the latest code, then run `python uat_live.py` again.

---

## Why some issues were not caught (and what we added)

1. **Last Updated On date/time missing**  
   - **Cause:** Backend could return `"Last Updated On: —"` when `last_scraped.txt` was missing and `ZoneInfo("Asia/Kolkata")` failed. Tests only checked that `last_updated_note` was present, not that it contained a real date.  
   - **Change:** Backend now always returns a real date/time (fallback to `datetime.now()` with a simple format). Tests now assert that `last_updated_note` contains at least one digit (i.e. a date/time, not a placeholder).

2. **UI of response (Source + Last Updated) broken**  
   - **Cause:** No visual or layout tests; only API and mocked-flow tests. Layout (Source/note beside text, number breaking mid-value) and link styling were not asserted.  
   - **Change:** CSS updated so Source and Last Updated sit on their own rows below the answer (flex-wrap + full width), Source link is underlined, and the bubble has a slightly larger min-width to reduce mid-number line breaks. Consider adding DOM/structure tests (e.g. message has a link with `href`) or visual regression tests in the future.
