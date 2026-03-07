# Info 1–17 validation (all 5 funds)

This doc confirms that the RAG pipeline can answer user questions for **every field (Info 1–17)** from `data_review.json` across all **5 mutual funds**, so diverse user inputs return answers instead of "I don't have that information."

## Data source

- **Phase 01** `data_review.json` (and `cleaned/*.json`) hold **Info 1–17** per fund:
  - 1 Expense ratio, 2 Lock In, 3 Minimum SIP, 4 Exit Load, 5 Risk, 6 Benchmark, 7 AUM, 8 Inception Date, 9 TurnOver
  - 10 About (Fund), 11 Fund Manager, 12 How Do I Invest, 13 NAV
  - 14 Fund vs Competition, 15 Fund Comparison, 16 Fund Pros and Cons, 17 Fund Returns Calculator
- **Chunks** are built from the same labels (e.g. `Expense ratio: 0.89%`, `Fund Manager: Rohit Shimpi`).

## How we avoid “no response”

- **Phase 03** `CONTEXT_EXTRACT_PATTERNS`: for each of Info 1–17 we have (question pattern, label, context pattern). When the user’s query matches a question pattern and the retrieved context contains the corresponding label, we **extract** the value and return it (no LLM needed for these facts).
- Question patterns are **broad** so many phrasings work, e.g.:
  - Fund manager: "who is the manager", "who manages this fund", "fund manager"
  - Inception: "when was the fund started", "launch", "inception"
  - How to invest: "how do I invest", "how to invest"
  - Ranking: "ranking", "peer comparison"; "pros and cons" for positive/negative
  - Returns: "returns calculator", "absolute return", "sip return"
- Extracted values up to **400 characters** are returned (longer ones truncated with "...").

## Automated validation

- **Phase 03** tests: `tests/test_info_1_to_17_validation.py`
  - One test per **Info 1–17**: a chunk containing that label + a sample user query → `generate_response()` → assert the answer is not "I don't have that information" and contains the expected value (or key substring).
- Run from **Phase 03** directory:
  ```bash
  cd "Phase 03- llm_response"
  python -m pytest tests/test_info_1_to_17_validation.py -v
  ```
- **17/17** tests must pass. They validate extraction only (chunk provided); retrieval is tested separately in Phase 02 / 05.

## Coverage matrix (conceptual)

| Info | Field                     | Sample user query                          | Extraction pattern / note     |
|------|---------------------------|--------------------------------------------|-------------------------------|
| 1    | Expense ratio             | What is the expense ratio of SBI ELSS?     | expense ratio                 |
| 2    | Lock In                   | Lock-in period for SBI ELSS?                | lock in, lock-in              |
| 3    | Minimum SIP               | Minimum SIP / min investment for SBI ELSS? | minimum sip, min investment   |
| 4    | Exit Load                 | Exit load for SBI ELSS?                     | exit load                     |
| 5    | Risk                      | Risk / riskometer for SBI ELSS?             | risk, riskometer              |
| 6    | Benchmark                 | Benchmark of SBI ELSS?                      | benchmark (incl. typo)        |
| 7    | AUM                       | AUM of SBI ELSS?                            | aum                           |
| 8    | Inception Date            | When was SBI ELSS started?                  | inception, started, launch    |
| 9    | TurnOver                  | Turnover of SBI ELSS?                       | turnover                      |
| 10   | About (Fund)              | What is this fund about? SBI ELSS           | about fund, fund objective     |
| 11   | Fund Manager              | Who is the manager of SBI US fund?           | fund manager, who manages      |
| 12   | How Do I Invest           | How do I invest in SBI ELSS?                 | how do I invest, how to invest |
| 13   | NAV                       | NAV of SBI ELSS?                            | nav                           |
| 14   | Fund vs Competition       | Fund vs competition for SBI ELSS?           | performance, comparison       |
| 15   | Fund Comparison           | What is fund ranking for SBI Nifty Index?   | ranking, peer comparison      |
| 16   | Fund Pros and Cons        | Pros and cons of SBI ELSS?                  | positive and negative, pros   |
| 17   | Fund Returns Calculator   | Returns calculator for SBI ELSS?           | returns calculator, sip return |

Same logic applies to **all 5 funds** (SBI US FoF, SBI Nifty Index, SBI Flexicap, SBI ELSS, SBI Large Cap); the chunk text and scheme name in the query determine which fund’s data is used.

## If a scenario still fails

1. **Retrieval**: The chunk that contains the answer might not be in top-k. Try rephrasing the question to include the scheme name and the topic (e.g. "SBI ELSS expense ratio"). If needed, increase `top_k` in Phase 05.
2. **Phrasing**: If you see a new phrasing that should map to an existing Info field, add a question pattern for it in `Phase 03- llm_response/client/gemini_client.py` `CONTEXT_EXTRACT_PATTERNS`.
3. **New field**: If you add a new field to data/chunks, add a corresponding (question pattern, label, context pattern) and a test in `test_info_1_to_17_validation.py`.
