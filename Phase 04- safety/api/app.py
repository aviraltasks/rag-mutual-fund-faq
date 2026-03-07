"""
Phase 04 - Safety Layer: optional HTTP API for testing/integration.
POST /check with { "query": "..." } -> { "allowed", "refusal_message", "educational_link" }.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from classifier import check_safety

app = FastAPI(
    title="Mutual Fund FAQ — Safety Check API",
    description="Classify question as factual (allowed) or advice/opinion/PII (refusal).",
    version="0.1.0",
)


class CheckRequest(BaseModel):
    query: str = Field(..., description="User question")


class CheckResponse(BaseModel):
    allowed: bool
    refusal_message: str | None
    educational_link: str | None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
def check(req: CheckRequest):
    """Classify question. If allowed=True, caller proceeds to retrieval + LLM. Else return refusal."""
    return CheckResponse(**check_safety(req.query))
