"""
Run the Mutual Fund FAQ Assistant (orchestrator + static frontend).
From project root: python "Phase 05- frontend/run.py"
Or from Phase 05- frontend: python run.py
"""

import sys
from pathlib import Path

# Ensure server can import from Phase 02, 03, 04
FRONTEND_DIR = Path(__file__).resolve().parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

import os
import uvicorn

if __name__ == "__main__":
    # Run server/app.py; static files from public/
    port = int(os.environ.get("PORT", "3000"))
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
