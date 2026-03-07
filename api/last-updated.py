# Vercel serverless: GET /api/last-updated
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "Phase 05- frontend") not in sys.path:
    sys.path.insert(0, str(ROOT / "Phase 05- frontend"))
from server.app import _last_updated_note


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        out = {"last_updated_note": _last_updated_note()}
        self.wfile.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
