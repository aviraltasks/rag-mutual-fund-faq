"""
Standalone backend for deployment (e.g. Railway): /chat and /last-updated with in-process flow.
Run: python backend_server.py  (or uvicorn backend_server:app --host 0.0.0.0 --port $PORT)
Expects: Phase 01- data, Phase 02- backend, Phase 03- llm_response, Phase 04- safety, Phase 05- frontend in cwd.
Set env GEMINI_API_KEY for LLM. PORT defaults to 8000.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in [str(ROOT), str(ROOT / "Phase 02- backend"), str(ROOT / "Phase 03- llm_response"), str(ROOT / "Phase 04- safety"), str(ROOT / "Phase 05- frontend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from classifier.classifier import check_safety
from retrieval.search import search
from client.gemini_client import generate_response
from server.app import run_chat_flow_sync, _last_updated_note


def _retrieve(q: str):
    results = search(query=q, top_k=15)
    return [{"chunk_id": r.get("chunk_id"), "text": r.get("text"), "fund_name": r.get("fund_name"), "source_url": r.get("source_url") or "", "statement_url": r.get("statement_url") or ""} for r in results]


def _llm(question: str, chunks: list) -> dict:
    out = generate_response(question, chunks)
    return {"answer": out.get("answer", ""), "citation_url": out.get("citation_url", ""), "last_updated_note": out.get("last_updated_note", "")}


app = FastAPI(title="RAG Mutual Fund FAQ Backend", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/last-updated")
def last_updated():
    return {"last_updated_note": _last_updated_note()}


@app.post("/chat")
def chat(req: ChatRequest):
    query = (req.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    out = run_chat_flow_sync(
        query,
        safety_fn=lambda q: check_safety(q),
        retrieve_fn=lambda q: _retrieve(q),
        llm_fn=lambda q, ch: _llm(q, ch),
    )
    if "error" in out:
        raise HTTPException(status_code=400, detail=out.get("error"))
    return out


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
