# Robustness Plan — Ensure the Project Functions Every Time

**Goal:** Response generation is **success or failure**. This plan makes the engine robust so that whenever the data repository contains the answer, the user gets it—without depending on a single point of failure (e.g. LLM availability).

---

## 1. Design principle: extraction over LLM for known facts

- **RAG + LLM** are both part of the project; the **source of truth** is the data repository (Phase 01 chunks).
- For questions that map to a **known field** (expense ratio, benchmark, lock-in, minimum SIP, etc.), we **always try to extract the answer from retrieved context first**. The LLM is used for phrasing or for questions that don’t match a simple field.
- So: **extraction is the primary path** for factual one-field questions; **LLM is an enhancement**, not the only path.

**Implemented:**
- Phase 03 runs **extraction first** on every request when context is present. If extraction returns a value, we return it and do not call the LLM.
- Extraction patterns are aligned with Phase 01 chunk labels (e.g. `Expense ratio:`, `Benchmark:`, `Lock In:`).

---

## 2. No single point of failure

| Scenario | Behaviour |
|----------|-----------|
| **No `GEMINI_API_KEY`** | We still have context from retrieval. We run extraction first; only if extraction fails do we return “I don’t have that information”. So missing key does not block answers when the fact is in the chunks. |
| **LLM throws (timeout, quota, network)** | After catching the exception, we try extraction from the same context once more. If we find the fact, we return it; otherwise we return “Service temporarily unavailable.” |
| **Retrieval returns empty chunks** | Phase 05 does not call the LLM. It returns a clear message: “No matching data for this query. Please include the scheme name (e.g. SBI ELSS Tax Saver Fund) and try again.” |
| **Relevant chunk not in top-k** | We increased **top_k from 5 to 8** in the retrieve request so more chunks are sent to Phase 03, improving the chance the right chunk is in the context. |

---

## 3. Data–code contract

- **Phase 01** produces chunk text with labels from `LABELS` in `chunk_and_embed.py` (e.g. `"Expense ratio: 0.89%"`, `"Benchmark: BSE 500 India TR INR"`).
- **Phase 03** `CONTEXT_EXTRACT_PATTERNS` use the **same labels** (and regex) so extraction always matches what’s in the chunks.
- When adding a new field in Phase 01, add a corresponding pattern in Phase 03 so extraction stays robust.

---

## 4. Clear failure messages

- **Empty retrieval:** “No matching data for this query. Please include the scheme name (e.g. SBI ELSS Tax Saver Fund) and try again.”
- **LLM down and extraction failed:** “I don’t have that information in my sources. (Service temporarily unavailable.)”
- **Safety refusal:** Existing refusal message + educational link (no change).

Users always get a deterministic, understandable outcome instead of a generic “no info” when the cause is empty data or service unavailability.

---

## 5. Pre-demo / pre-submission checklist

1. **Phase 01 run at least once**  
   - `Phase 01- data/chunks/chunks.json` and `Phase 01- data/embeddings/vectors.npy` exist and have the same length.

2. **Phase 02 running and healthy**  
   - Service starts and can load chunks and vectors (same embedding model as Phase 01).

3. **Phase 03**  
   - Extraction-first is always used when context exists; LLM is optional for known-field questions.
   - For full behaviour (including non-extractable questions), set `GEMINI_API_KEY` in project root `.env`.

4. **Phase 04 and 05 running**  
   - Safety and orchestrator up; `SAFETY_URL`, `RETRIEVE_URL`, `LLM_URL` correct.

5. **Query style**  
   - Factual question + scheme name (e.g. “What is the expense ratio of SBI ELSS Tax Saver Fund?”) so retrieval and extraction can succeed.

---

## 6. What “robust” means for this project

- **Functionality = success or failure:** The site is a success if users get correct factual answers from the repository when they ask in a supported way.
- **Robust engine:**  
  - Uses **retrieved chunks** as the source of truth.  
  - **Extracts** answers when the question matches a known field and the context contains it.  
  - Uses the **LLM** to improve phrasing or answer non-field questions when the API is available.  
  - **Never** relies only on the LLM for known-field facts when we have context; extraction can answer even when the API key is missing or the LLM fails.

This keeps the project aligned with the mandate (facts from our data, no advice) and makes response generation as reliable as the data and retrieval allow.
