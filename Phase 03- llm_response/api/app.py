"""
Phase 03 - LLM Response: optional HTTP API for testing/integration.
POST /answer with { "query": "...", "chunks": [...] } -> { "answer", "citation_url", "last_updated_note" }.
Run from Phase 03 dir: uvicorn api.app:app --port 8001
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from client import generate_response

app = FastAPI(
    title="Mutual Fund FAQ — LLM Answer API",
    description="Facts-only answers from retrieved context. No advice.",
    version="0.1.0",
)


class ChunkItem(BaseModel):
    chunk_id: str = ""
    text: str
    fund_name: str = ""
    source_url: str = ""
    statement_url: str = ""


class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=1)
    chunks: list[ChunkItem] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    answer: str
    citation_url: str
    last_updated_note: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest):
    """Generate a factual answer from the provided chunks. Citation = top chunk's source_url."""
    chunks = [c.model_dump() for c in req.chunks]
    result = generate_response(question=req.query, chunks=chunks)
    return AnswerResponse(**result)
