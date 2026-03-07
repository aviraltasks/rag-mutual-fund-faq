"""
Backend configuration: paths to Data Phase artifacts and retrieval defaults.
"""

from pathlib import Path

# Project root (parent of Phase 02- backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_PHASE_DIR = PROJECT_ROOT / "Phase 01- data"

# Data Phase artifact paths (relative to DATA_PHASE_DIR)
CHUNKS_PATH = DATA_PHASE_DIR / "chunks" / "chunks.json"
VECTORS_PATH = DATA_PHASE_DIR / "embeddings" / "vectors.npy"

# Must match Phase 01 chunk_and_embed.py
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Default number of chunks to return per query
DEFAULT_TOP_K = 5
