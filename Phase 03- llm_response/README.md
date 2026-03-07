# Phase 03 — LLM Response

Uses **Gemini 2.5 Flash** to generate short, factual answers from retrieved chunks. The chatbot does **not** answer from its own knowledge; it uses **only** the context (chunks) provided. Personal information questions are out of scope.

## Behaviour

- **Context-only:** Answer is generated only from the retrieved chunk text. If the answer is not in the context, the response is "I don't have that information in my sources."
- **No personal info:** Questions about PAN, Aadhaar, account numbers, OTPs, email, phone are refused with an out-of-scope message.
- **No advice:** System prompt forbids investment advice or recommendations.
- **One citation:** Citation URL is always the **top chunk’s `source_url`** (IND money link), attached by the service, not by the LLM.
- **Last updated:** Every response includes a "Last updated from sources: see citation link." note.

## Setup

1. Put your Gemini API key in the **project root** `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
2. From this directory: `pip install -r requirements.txt`

## Usage

**Programmatic:** Call `generate_response(question, chunks)` from `client`. `chunks` = list of dicts from Phase 02 `/retrieve` (each with `text`, `source_url`, etc.).

**HTTP API (optional):**
```bash
uvicorn api.app:app --port 8001
# POST /answer  body: { "query": "...", "chunks": [ { "text": "...", "source_url": "..." }, ... ] }
```

## Response shape

```json
{
  "answer": "Short factual answer (≤3 sentences).",
  "citation_url": "https://www.indmoney.com/...",
  "last_updated_note": "Last updated from sources: see citation link."
}
```

## Tests

```bash
cd "Phase 03- llm_response"
pytest tests/ -v
```

No API key required for tests (empty chunks or no-key path). With a valid key, real Gemini may be called in some tests.
