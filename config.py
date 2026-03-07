"""
Unified config for backend_server when running from repo root (e.g. Railway).
Provides Phase 02 paths + Phase 03 Gemini settings so "from config import ..." works for all phases.
GEMINI_* are read from environment (set in Railway Variables).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PHASE_DIR = ROOT / "Phase 01- data"

# Phase 02 - retrieval
CHUNKS_PATH = DATA_PHASE_DIR / "chunks" / "chunks.json"
VECTORS_PATH = DATA_PHASE_DIR / "embeddings" / "vectors.npy"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5
BACKEND_DIR = ROOT / "Phase 02- backend"

# Phase 03 - LLM (from env so Railway Variables work)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
LAST_UPDATED_PREFIX = "Last updated from sources: "
