# Why Responses May Not Be Generated — RAG + LLM Architecture Checklist

This document lists **all possible reasons** (based on our architecture) why the chatbot might not produce a factual answer from the data repository. Use it for submission documentation and debugging.

---

## End-to-end flow (reminder)

```
User query → [Phase 05] → [Phase 04 Safety] → [Phase 02 Retrieve] → [Phase 03 LLM] → Answer + citation
                              ↓                      ↓                     ↓
                         allowed?              chunks with text      answer from context/LLM
```

If the user sees **“I don’t have that information in my sources”**, a refusal message, or an error, the cause is in one of the layers below.

---

## 1. Phase 04 — Safety layer (no LLM / no retrieval)

**What happens:** The question is classified. If it’s **not** allowed, the orchestrator returns a refusal message and **never** calls retrieval or the LLM.

| Reason | What to check |
|--------|----------------|
| **Question classified as advice/opinion** | E.g. “Should I buy SBI ELSS?”, “Recommend a fund” → `allowed: false`. Safety is working as designed. |
| **Question classified as PII/account** | E.g. PAN, KYC, account number → `allowed: false`. |
| **Empty or whitespace query** | Safety treats empty query as not allowed. |
| **Safety service down** | Phase 04 not running (port 8002) or wrong `SAFETY_URL` → 503 “Safety service unavailable.” |

**Fix:** For factual demos, ask only factual questions (expense ratio, lock-in, benchmark, etc.). Ensure Phase 04 is running and `SAFETY_URL` in Phase 05 points to it.

---

## 2. Phase 02 — Retrieval (no or wrong chunks)

**What happens:** The query is embedded and compared to chunk embeddings. Top-k chunks are returned. If retrieval fails or returns irrelevant/empty chunks, the LLM has no (or wrong) context.

| Reason | What to check |
|--------|----------------|
| **Data Phase never run or incomplete** | No `Phase 01- data/chunks/chunks.json` or `Phase 01- data/embeddings/vectors.npy` → retrieval fails or raises at startup. |
| **Chunk and vector count mismatch** | `load_store()` requires `len(chunks) == len(vectors)`. Re-run Phase 01 (chunk + embed) so both artifacts are in sync. |
| **Wrong embedding model** | Phase 01 and Phase 02 must use the **same** model (e.g. `all-MiniLM-L6-v2`). Mismatch → wrong similarity → wrong chunks. |
| **Query doesn’t match chunk wording** | Semantic search returns by similarity. Very different phrasing or typo-heavy query can rank the right chunk low. |
| **Top-k too small** | If the relevant chunk is rank 6 and `top_k=5`, it’s never sent to the LLM. Increase `top_k` (e.g. 5 → 8) in Phase 02 config or request. |
| **Retrieval service down** | Phase 02 not running (port 8000) or wrong `RETRIEVE_URL` → 503 “Retrieval unavailable.” |

**Fix:** Run Phase 01 fully; ensure Phase 02 uses same embedding model and can read chunks + vectors; keep Phase 02 up; optionally increase `top_k` for harder queries.

---

## 3. Phase 03 — LLM response (context present but answer still “no info”)

**What happens:** Phase 03 receives the query and chunks. It builds context from chunk `text` and calls the LLM (or uses context extraction). The answer can still be “I don’t have that information” for several reasons.

| Reason | What to check |
|--------|----------------|
| **No `GEMINI_API_KEY`** | `.env` in project root missing or empty → Phase 03 returns “I don’t have that information” **without** calling the LLM. |
| **Wrong or invalid API key** | Key revoked, quota exceeded, or wrong key → LLM call fails; Phase 03 returns no-info or error message. |
| **Model name wrong** | `GEMINI_MODEL` in `.env` (e.g. `gemini-2.5-flash`) must be a valid model name. |
| **Chunks have no `text`** | Context is built from `chunk["text"]`. If retrieval returns chunks without `text`, context is empty → no-info. |
| **Relevant chunk not in top-k** | Even with extraction fallback, we only look in **retrieved** context. If the right chunk wasn’t in top-k, we can’t answer. |
| **Question doesn’t match extraction patterns** | Context extraction only handles known fields (expense ratio, benchmark, lock-in, etc.). Unusual phrasing or new field type may not match. |
| **Context format doesn’t match regex** | Extraction uses patterns like `Benchmark:\s*([^\n]+)`. If chunk text uses a different format (e.g. “Benchmark -”), extraction can miss it. |
| **LLM ignores context** | Model may sometimes answer from general knowledge or say “no info” despite context. We mitigate with “extract first” + extraction fallback. |
| **LLM service down** | Phase 03 not running (port 8001) or wrong `LLM_URL` → 503 “Answer service unavailable.” |

**Fix:** Set `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) in `.env`; ensure Phase 03 is running; ensure retrieval returns chunks that contain the fact and use the expected labels (e.g. “Expense ratio:”, “Benchmark:”).

---

## 4. Phase 05 — Orchestrator / frontend

**What happens:** Phase 05 calls Safety → Retrieve → LLM and returns the answer to the UI. Failures here are usually connectivity or configuration.

| Reason | What to check |
|--------|----------------|
| **Wrong backend URLs** | `SAFETY_URL`, `RETRIEVE_URL`, `LLM_URL` must point to running services (defaults: 8002, 8000, 8001). |
| **Network / firewall** | All three backend services must be reachable from the machine running Phase 05. |
| **Timeout** | Long LLM or retrieval time can cause 503 or no response. |
| **Frontend not calling /chat** | UI must POST to `/chat` with `{ "query": "..." }`. Check browser Network tab. |
| **CORS / same-origin** | If frontend is served from another origin, ensure CORS allows the request (or serve frontend and API from same origin). |

**Fix:** Start all four services (02, 03, 04, 05); use correct env vars; verify `/chat` in Network tab and response body.

---

## 5. Data repository (Phase 01) — content and format

**What happens:** Answers are only as good as the data we chunk and embed. If the fact isn’t in the corpus or is in an unexpected format, we can’t answer.

| Reason | What to check |
|--------|----------------|
| **Fact not in scraped data** | Source pages might not contain the field (e.g. expense ratio). Check `data_review.json` and cleaned/chunked text. |
| **Wrong scheme** | User asks about “SBI ELSS” but the chunk that has “Expense ratio: 0.89%” is for another fund. Retrieval must return the chunk for the **asked** scheme. |
| **Label/format change** | Chunk text uses “Expense ratio:” but we later change to “expense_ratio:” in cleaning → extraction regex may not match. |
| **Chunk boundary** | The fact is split across chunks (e.g. “Expense” in one chunk, “ratio: 0.89%” in another). Extraction looks per chunk; may need larger overlap or different chunking. |

**Fix:** Validate `data_review.json` and `chunks.json` for the schemes and fields you demo; keep Phase 01 labels and Phase 03 extraction patterns in sync.

---

## Quick checklist before submission / demo

1. **Phase 01:** Run at least once; `chunks/chunks.json` and `embeddings/vectors.npy` exist and match in length.
2. **Phase 02:** Same embedding model as Phase 01; service running; can load chunks and vectors.
3. **Phase 03:** `GEMINI_API_KEY` (and `GEMINI_MODEL` if needed) in project root `.env`; service running.
4. **Phase 04:** Service running (factual questions allowed).
5. **Phase 05:** All three URLs correct; service running; frontend hits `/chat`.
6. **Query:** Factual, mentions a scheme name, and asks for a field we have in chunks (expense ratio, benchmark, lock-in, etc.).

If all of the above are true and the relevant chunk is in the top-k results, the pipeline should return a factual answer (from context extraction or the LLM) with a citation.
