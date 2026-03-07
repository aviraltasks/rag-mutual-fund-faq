# Phase 02 — Backend (Retrieval API)

RAG retrieval service: loads chunks and embeddings from Phase 01, exposes a **retrieve** endpoint for the FAQ chatbot.

## What it does

- Loads `Phase 01- data/chunks/chunks.json` and `embeddings/vectors.npy`
- Embeds the user query with the same model as Phase 01 (`all-MiniLM-L6-v2`)
- Returns top-k chunks by cosine similarity (each with `source_url` for citation)

## API

- **GET /health** — Liveness
- **POST /retrieve** — Body: `{"query": "user question", "top_k": 5}`. Response: `{"chunks": [...], "total": n}`. Each chunk has `chunk_id`, `text`, `fund_name`, `source_url`, `statement_url`, `score`.

## Run

```bash
cd "Phase 02- backend"
pip install -r requirements.txt
python run.py
# or: uvicorn api.app:app --host 0.0.0.0 --port 8000
```

Then e.g. `curl -X POST http://localhost:8000/retrieve -H "Content-Type: application/json" -d "{\"query\": \"ELSS lock in period\"}"`

## Tests

```bash
cd "Phase 02- backend"
pytest tests/ -v
```

Requires Phase 01 artifacts (chunks + embeddings) to be present.
