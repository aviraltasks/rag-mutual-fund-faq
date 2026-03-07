# Phase 01 – Data Phase

This folder implements **Phase 1 (Data Phase)** from [ARCHITECTURE.md](../ARCHITECTURE.md): scrape → clean → chunk → embed → manifest.

## Artifacts (for manual validation)

| Artifact | Location | Description |
|----------|----------|-------------|
| Raw scraped content | `raw/` | One JSON per fund: `raw_<slug>.json` |
| Cleaned text | `cleaned/` | One JSON per fund: `cleaned_<slug>.json` (normalized, no HTML) |
| Chunked documents | `chunks/` | `chunks.json` – chunks with `chunk_id`, `text`, `fund_name`, `source_url`, `statement_url` |
| Embeddings | `embeddings/` | `vectors.npy` (float32 array), `chunk_metadata.json` (one entry per chunk, same order as rows in `vectors.npy`) |
| Manifest | `manifest/` | `manifest.json` – list of sources, chunk counts, paths, and config |
| Review file | `data_review.json` | Single file for human review (Info 1–17, Source URL, Statement URL per fund) |

## How to run

1. **Full pipeline** (scrape + chunk + embed):
   ```bash
   cd "Phase 01- data"
   pip install -r requirements.txt
   python run_data_phase.py
   ```

2. **Skip scrape** (use existing `cleaned/`, only chunk + embed):
   ```bash
   python run_data_phase.py --skip-scrape
   ```

3. **Scrape only** (update raw + cleaned + data_review.json):
   ```bash
   python scrape.py
   ```

4. **Chunk + embed only** (after scrape):
   ```bash
   python chunk_and_embed.py
   ```
   Re-run this after changing `LABELS` in `chunk_and_embed.py` (e.g. Info 15/16 renamed to Fund Comparison / Fund Pros and Cons) so that `chunks.json` and `vectors.npy` use the new labels.

## Config (chunk_and_embed.py)

- Chunk size: 450 characters, overlap: 80
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)

## Dependencies

- `scrape.py`: selenium, beautifulsoup4, webdriver-manager (Chrome required)
- `chunk_and_embed.py`: sentence-transformers, numpy
