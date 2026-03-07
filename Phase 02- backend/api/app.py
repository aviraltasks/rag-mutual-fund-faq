"""
Backend API: retrieval endpoint for the FAQ chatbot.
Run from project root or backend dir: uvicorn api.app:app --reload (with cwd = Phase 02- backend)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import DEFAULT_TOP_K
from retrieval import search

app = FastAPI(
    title="Mutual Fund FAQ — Retrieval API",
    description="Facts-only RAG backend. Returns relevant chunks for a query.",
    version="0.1.0",
)


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question")
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=20, description="Max chunks to return")


class ChunkResult(BaseModel):
    chunk_id: str
    text: str
    fund_name: str
    source_url: str
    statement_url: str
    score: float


class RetrieveResponse(BaseModel):
    chunks: list[ChunkResult]
    total: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    """Return top-k chunks most similar to the query. For use by LLM/Safety layer."""
    try:
        results = search(query=req.query, top_k=req.top_k)
        return RetrieveResponse(
            chunks=[ChunkResult(**r) for r in results],
            total=len(results),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail="Data not loaded. Run Phase 01 pipeline first.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
