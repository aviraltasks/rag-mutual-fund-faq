"""
Phase 03 - LLM Response: main entrypoint.
generate_response(question, chunks) is the main API for Phase 3.
Chunks come from Phase 02 backend /retrieve.
"""

from client import generate_response

__all__ = ["generate_response"]
