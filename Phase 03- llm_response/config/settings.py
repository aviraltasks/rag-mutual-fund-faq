"""
Phase 03 - LLM Response: config and env loading.
Loads GEMINI_API_KEY and GEMINI_MODEL from .env (project root).
"""

from pathlib import Path
import os

# Phase 03 dir and project root (where .env lives)
PHASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PHASE_DIR.parent

# Load .env from project root
def _load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            pass

_load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Response format
LAST_UPDATED_PREFIX = "Last updated from sources: "
