# Phase 04 — Safety Layer

Classifies each user question as **factual** (allowed) or **advice/opinion/PII** (refused). For refused questions, returns a polite facts-only refusal message; the LLM is **not** called. No investor-education links.

## Behaviour

- **Factual:** e.g. "What is the lock in for ELSS?" → `allowed: true` → caller proceeds to retrieval + LLM.
- **Advice / opinion:** e.g. "Should I buy SBI ELSS?", "Recommend a fund" → `allowed: false`, refusal message; `educational_link: null`.
- **PII / account:** e.g. "Update my PAN", "KYC status" → `allowed: false`, out-of-scope message.
- **Empty:** Refused with a short prompt to ask a factual question.

## Usage

**Programmatic:** `check_safety(question)` from `classifier` → `{ "allowed", "refusal_message", "educational_link" }`.

**HTTP API (optional):**
```bash
uvicorn api.app:app --port 8002
# POST /check  body: { "query": "..." }
```

## Response shape

- **Allowed:** `{ "allowed": true, "refusal_message": null, "educational_link": null }`
- **Refused:** `{ "allowed": false, "refusal_message": "...", "educational_link": null }`

## Tests

```bash
cd "Phase 04- safety"
pip install -r requirements.txt
pytest tests/ -v
```

## Config

- Refusal messages in `messages/refusal.py` (facts-only; no links).
