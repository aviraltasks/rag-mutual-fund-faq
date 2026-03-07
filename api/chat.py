# Vercel serverless: POST /api/chat — run full flow in-process (safety, retrieve, LLM).
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Phase 02- backend"))
sys.path.insert(0, str(ROOT / "Phase 03- llm_response"))
sys.path.insert(0, str(ROOT / "Phase 04- safety"))
sys.path.insert(0, str(ROOT / "Phase 05- frontend"))

# In-process callables (avoid HTTP between services)
from classifier.classifier import check_safety
from retrieval.search import search
from client.gemini_client import generate_response
from server.app import run_chat_flow_sync


def _retrieve(q: str):
    results = search(query=q, top_k=15)
    return [{"chunk_id": r.get("chunk_id"), "text": r.get("text"), "fund_name": r.get("fund_name"), "source_url": r.get("source_url") or "", "statement_url": r.get("statement_url") or ""} for r in results]


def _llm(question: str, chunks: list) -> dict:
    out = generate_response(question, chunks)
    return {"answer": out.get("answer", ""), "citation_url": out.get("citation_url", ""), "last_updated_note": out.get("last_updated_note", "")}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(body) if body.strip() else {}
            query = (data.get("query") or "").strip()
            if not query:
                self._send(400, {"detail": "Query is required"})
                return
            out = run_chat_flow_sync(
                query,
                safety_fn=lambda q: check_safety(q),
                retrieve_fn=lambda q: _retrieve(q),
                llm_fn=lambda q, ch: _llm(q, ch),
            )
            if "error" in out:
                self._send(400, out)
                return
            self._send(200, out)
        except Exception as e:
            self._send(503, {"detail": str(e)})

    def _send(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
