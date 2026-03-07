"""
Phase 01 - Data: Chunk cleaned fund documents and generate embeddings.
Reads cleaned/*.json, produces chunks with IDs and source refs, then embeddings.
Run after scrape (or use existing cleaned/ and data_review.json).
Output: chunks/chunks.json, embeddings/vectors.npy + chunk_metadata.json, manifest/manifest.json.
"""

import json
from pathlib import Path

import numpy as np

PHASE_DIR = Path(__file__).resolve().parent
CLEANED_DIR = PHASE_DIR / "cleaned"
CHUNKS_DIR = PHASE_DIR / "chunks"
EMBEDDINGS_DIR = PHASE_DIR / "embeddings"
MANIFEST_DIR = PHASE_DIR / "manifest"

CHUNK_SIZE = 450
CHUNK_OVERLAP = 80
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Human-readable labels for cleaned keys (for document text)
LABELS = {
    "fund_name": "Mutual Fund Name",
    "info_1_expense_ratio": "Expense ratio",
    "info_2_lock_in": "Lock In",
    "info_3_min_sip": "Minimum SIP",
    "info_4_exit_load": "Exit Load",
    "info_5_risk": "Risk",
    "info_6_benchmark": "Benchmark",
    "info_7_aum": "AUM",
    "info_8_inception_date": "Inception Date",
    "info_9_turnover": "TurnOver",
    "info_10_about": "About (Fund)",
    "info_11_fund_manager": "Fund Manager",
    "info_12_how_to_invest": "How Do I Invest",
    "info_13_nav": "NAV",
    "info_14_fund_vs_competition": "Fund vs Competition",
    "info_15_ranking": "Fund Comparison",
    "info_16_ranking_pos_neg": "Fund Pros and Cons",
    "info_17_returns_calculator": "Fund Returns Calculator",
}


def cleaned_to_document(cleaned: dict) -> str:
    """Turn one cleaned fund record into a single searchable text document."""
    parts = []
    for key, label in LABELS.items():
        val = cleaned.get(key)
        if val and str(val).strip():
            parts.append(f"{label}: {val}")
    source = cleaned.get("source_url", "")
    if source:
        parts.append(f"Source URL: {source}")
    stmt = cleaned.get("statement_url", "")
    if stmt:
        parts.append(f"Statement URL: {stmt}")
    return "\n\n".join(parts)


def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks (character-based)."""
    if not text or not text.strip():
        return []
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def load_all_cleaned() -> list[dict]:
    """Load all cleaned JSON files from cleaned/."""
    out = []
    for path in sorted(CLEANED_DIR.glob("cleaned_*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception as e:
            print(f"Skip {path}: {e}")
    return out


def build_chunks() -> list[dict]:
    """Build chunk list with chunk_id, text, fund_name, source_url, statement_url."""
    all_cleaned = load_all_cleaned()
    chunks_out = []
    chunk_index = 0
    for cleaned in all_cleaned:
        fund_name = cleaned.get("fund_name", "Unknown")
        source_url = cleaned.get("source_url", "")
        statement_url = cleaned.get("statement_url", "")
        doc = cleaned_to_document(cleaned)
        text_chunks = split_into_chunks(doc)
        for i, text in enumerate(text_chunks):
            chunk_id = f"chunk_{chunk_index:04d}"
            chunk_index += 1
            chunks_out.append({
                "chunk_id": chunk_id,
                "text": text,
                "fund_name": fund_name,
                "source_url": source_url,
                "statement_url": statement_url,
            })
    return chunks_out


def embed_chunks(chunks: list[dict]) -> tuple[np.ndarray, list[dict]]:
    """Generate embeddings for each chunk. Returns (vectors, metadata list)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError("Install sentence-transformers: pip install sentence-transformers")

    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["text"] for c in chunks]
    vectors = model.encode(texts, show_progress_bar=True)
    metadata = [{"chunk_id": c["chunk_id"], "fund_name": c["fund_name"], "source_url": c["source_url"], "statement_url": c["statement_url"]} for c in chunks]
    return np.asarray(vectors, dtype=np.float32), metadata


def build_manifest(chunks: list[dict], chunk_path: Path, embeddings_path: Path, meta_path: Path) -> dict:
    """Build manifest for validation: sources, chunk counts, paths (relative to Phase dir)."""
    by_fund = {}
    for c in chunks:
        name = c["fund_name"]
        by_fund[name] = by_fund.get(name, 0) + 1
    return {
        "sources": [{"fund_name": k, "chunk_count": v} for k, v in sorted(by_fund.items())],
        "total_chunks": len(chunks),
        "paths": {
            "chunks": str(chunk_path.relative_to(PHASE_DIR)),
            "embeddings_vectors": str(embeddings_path.relative_to(PHASE_DIR)),
            "embeddings_metadata": str(meta_path.relative_to(PHASE_DIR)),
        },
        "config": {"chunk_size": CHUNK_SIZE, "chunk_overlap": CHUNK_OVERLAP, "embedding_model": EMBEDDING_MODEL},
    }


def main():
    CHUNKS_DIR.mkdir(exist_ok=True)
    EMBEDDINGS_DIR.mkdir(exist_ok=True)
    MANIFEST_DIR.mkdir(exist_ok=True)

    print("Building chunks from cleaned/ ...")
    chunks = build_chunks()
    if not chunks:
        print("No cleaned documents found. Run scrape.py first.")
        return

    chunk_path = CHUNKS_DIR / "chunks.json"
    with open(chunk_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(chunks)} chunks to {chunk_path}")

    print("Generating embeddings ...")
    vectors, metadata = embed_chunks(chunks)
    vec_path = EMBEDDINGS_DIR / "vectors.npy"
    np.save(vec_path, vectors)
    meta_path = EMBEDDINGS_DIR / "chunk_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata}, f, indent=2, ensure_ascii=False)
    print(f"Saved vectors {vectors.shape} to {vec_path}, metadata to {meta_path}")

    manifest = build_manifest(chunks, chunk_path, vec_path, meta_path)
    manifest_path = MANIFEST_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Saved manifest to {manifest_path}")
    print("Phase 1 (Data) pipeline done.")


if __name__ == "__main__":
    main()
