# Phase-wise Project Architecture — Mutual Fund FAQ Chatbot (RAG)

## 0. Phase 0 — Product Context

**What we are building:** A small **Facts-Only Mutual Funds FAQ Assistant Chatbot**: RAG-based, answers factual questions about the 5 selected mutual funds using scraped information only. Concise, citation-backed responses; **strictly no investment advice**. Every answer includes **one source link**. No advice.

**Users:** Retail users comparing schemes; support/content teams answering repetitive mutual fund questions.

**Key constraints:**
- **Public sources only.** No screenshots of app back-end; no third-party blogs as sources.
- **No PII.** Do not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers.
- **No performance claims.** Do not compute or compare returns; link to official factsheet if asked.
- **Clarity & transparency.** Keep answers ≤3 sentences; add “Last updated from sources: ”.

**FAQ assistant (working prototype):**
- Answers factual queries only from our collected source information.
- Shows **one clear citation link** in every answer (IND money URL).
- Refuses opinionated/portfolio questions (e.g. “Should I buy/sell?”) with a polite, facts-only message and a relevant educational link.
- **Tiny UI:** Welcome line, 3 example questions, and the note: “Facts-only. No investment advice.” (Design to be shared in Frontend phase.)

---

## 1. List of Phases in Execution Order

| Order | Phase Name        | Purpose Summary |
|-------|-------------------|-----------------|
| 1     | **Data Phase**    | Collect, clean, chunk, and embed content from INDMoney pages; produce validated artifacts. |
| 2     | **Backend Phase** | Expose retrieval and query APIs; serve embeddings and chunk lookup. |
| 3     | **LLM Response Phase** | Use retrieved chunks + safety rules to generate factual answers. |
| 4     | **Safety Layer**  | Enforce facts-only responses and refuse advice/recommendation questions. |
| 5     | **Frontend Phase**| Small chatbot UI: welcome, example questions, facts-only disclaimer. |
| 6     | **Scheduler Phase** | Periodically run the data pipeline to refresh content and embeddings. |
| 7     | **Deployment Phase** | Deploy backend and frontend as separate services. |

---

## 2. Short Description of What Happens in Each Phase

### Phase 1 — Data Phase

- **Purpose:** Turn INDMoney mutual fund page content into a retrieval-ready corpus (cleaned text, chunks, embeddings) with artifacts that can be validated manually.
- **What happens:**
  - Scrape content from provided INDMoney URLs.
  - Clean and normalize text (encoding, whitespace, boilerplate).
  - Split cleaned text into chunks (e.g. by size/overlap or semantic boundaries).
  - Generate embeddings for each chunk.
  - Persist: raw/cleaned text, chunk metadata, and embedding vectors so each step can be inspected.
- **Artifacts:** Raw scraped content; cleaned text (per page or per document); chunked documents (with chunk IDs and source references); embedding vectors (and optional index); manifest or index listing all artifacts for validation.

---

### Phase 2 — Backend Phase

- **Purpose:** Provide services for querying the stored corpus: accept a user query, run similarity search, return relevant chunks (and optionally source links).
- **What happens:**
  - Load or connect to the embedding index and chunk store produced in the Data Phase.
  - Accept a query; optionally embed the query using the same embedding method.
  - Run similarity search over chunk embeddings; return top-k chunks plus source identifiers/URLs.
  - Expose this as an internal or public API used by the LLM layer.
- **Artifacts:** API specification (e.g. request/response shape); response payloads (e.g. list of chunks with text, source link, score).

---

### Phase 3 — LLM Response Phase

- **Purpose:** Use retrieved chunks as context so the LLM generates short, factual answers only.
- **What happens:**
  - Receive user question and (from Backend Phase) retrieved chunks and source links.
  - Build a prompt that includes: system instructions (facts-only, no advice), retrieved context, and user question.
  - Call the LLM; parse and return the answer plus one citation link.
- **Artifacts:** Prompt templates; LLM request/response format; final answer object (answer text, citation URL, “Last updated from sources:” note).

---

### Phase 4 — Safety Layer

- **Purpose:** Enforce “facts only” and “no advice”; politely refuse opinion/advisory questions and point to educational links.
- **What happens:**
  - Classify incoming questions (factual vs. advice/recommendation/opinion).
  - For factual: allow flow to LLM Response Phase with retrieved context.
  - For non-factual: return a standard refusal message, brief facts-only explanation, and a fixed educational link; do not call the LLM for advice.
- **Artifacts:** Safety rules / classification criteria; refusal message templates; educational link(s); decision flow (factual path vs. refusal path).

---

### Phase 5 — Frontend Phase

- **Purpose:** Provide a small chatbot UI for users to ask questions and see factual answers with citations.
- **What happens:**
  - Show a welcome line, three example questions, and the note: “Facts-only. No investment advice.”
  - Send user input to backend (Backend + LLM Response + Safety); display answer and the single citation link.
  - Handle loading and error states; display refusal messages when the Safety Layer declines the question.
- **Artifacts:** UI layout/wireframe; static assets; built frontend bundle; configuration for backend URL.

---

### Phase 6 — Scheduler Phase

- **Purpose:** Keep data up to date by re-running the Data Phase pipeline on a schedule.
- **What happens:**
  - Trigger the full data pipeline (scrape → clean → chunk → embed) at defined intervals.
  - Replace or update the existing cleaned text, chunks, and embeddings used by the Backend Phase.
  - Optionally notify or log success/failure; no change to API contract.
- **Artifacts:** Schedule configuration (e.g. cron expression or interval); pipeline run logs; updated Data Phase artifacts (cleaned text, chunks, embeddings).

---

### Phase 7 — Deployment Phase

- **Purpose:** Run the system as a working prototype with separate backend and frontend services.
- **What happens:**
  - Deploy the backend service (Backend + LLM Response + Safety) so it is reachable at a stable URL.
  - Deploy the frontend so it points to that backend URL and is served over HTTP/HTTPS.
  - Deploy or configure the Scheduler so it runs in the target environment and writes to the same storage the backend uses.
- **Artifacts:** Deployment topology (which service runs where); environment configuration (e.g. backend URL, API keys); runbooks for start/stop/health checks.

---

## 3. Suggested Folder Structure (Phase → Folder Mapping)

```
project_root/
│
├── 01_data/
│   ├── raw/                    # Raw scraped content (per page or per URL)
│   ├── cleaned/                # Cleaned text (validatable)
│   ├── chunks/                 # Chunked documents + metadata (validatable)
│   ├── embeddings/             # Embedding vectors and/or index (validatable)
│   └── manifest/              # Index or manifest of all artifacts for validation
│
├── 02_backend/
│   ├── retrieval/              # Similarity search and chunk lookup
│   ├── api/                    # API entrypoints and request/response handling
│   └── config/                 # Backend configuration
│
├── 03_llm_response/
│   ├── prompts/                # Prompt templates
│   ├── client/                 # LLM invocation and response parsing
│   └── config/                 # LLM and citation config
│
├── 04_safety/
│   ├── classifier/             # Factual vs. advice classification logic
│   ├── messages/               # Refusal templates and educational links
│   └── config/                 # Safety rules and link config
│
├── 05_frontend/
│   ├── src/                    # UI source (e.g. components, pages)
│   ├── public/                 # Static assets
│   └── config/                 # Frontend config (e.g. backend URL)
│
├── 06_scheduler/
│   ├── jobs/                   # Pipeline trigger and job definitions
│   └── config/                 # Schedule and pipeline config
│
├── 07_deployment/
│   ├── backend/                # Backend deployment descriptors/config
│   ├── frontend/               # Frontend deployment descriptors/config
│   └── scheduler/              # Scheduler deployment descriptors/config
│
└── ARCHITECTURE.md             # This document
```

---

## 4. Data Phase Artifacts (Explicit for Manual Validation)

| Artifact        | Location (example)   | Description |
|-----------------|----------------------|-------------|
| Cleaned text    | `01_data/cleaned/`   | One or more files with normalized text per source page; human-inspectable. |
| Chunked documents | `01_data/chunks/`  | Chunks with IDs, source reference, and optional metadata (e.g. JSON or structured text). |
| Embeddings      | `01_data/embeddings/`| Vectors (and optional index file) keyed by chunk ID; format allows spot-checks. |
| Manifest        | `01_data/manifest/`  | List of sources, chunk counts, and paths so validators can trace pipeline output. |

---

## 5. Phase Independence and Testing

- **Data Phase:** Test by inspecting `01_data/cleaned/`, `01_data/chunks/`, `01_data/embeddings/`, and `01_data/manifest/` without running backend or LLM.
- **Backend Phase:** Test by calling retrieval API with sample queries; backend reads from `01_data/` (or a copy) and returns chunks.
- **LLM Response Phase:** Test by passing fixed retrieved chunks and a question; verify answer format and citation.
- **Safety Layer:** Test with fixed lists of factual vs. advice questions; verify refusal path and links.
- **Frontend:** Test against mock or real backend; no change to backend contract.
- **Scheduler:** Test by running one pipeline run and verifying updated artifacts in `01_data/`.
- **Deployment:** Test by bringing up backend and frontend only; scheduler can be added last.

This keeps phases **mutually exclusive** (each folder and phase has a clear scope) and **collectively exhaustive** (from data to deployed system and refresh).
