# Copilot Instructions for Energy-Flow Cosmology

## Project Overview
- **Energy-Flow Cosmology (EFC)** is a unified framework for scientific theory, computational models, semantic/graph layers, and reproducible open-science workflows.
- The repository is the **single source of truth** for theory, metadata, APIs, knowledge-graph, vector memory (RAG), and meta/cognitive processes.

## Architecture & Data Flow
- **All new data must enter via the deterministic ingestion pipeline** (`tools/orchestrator_v2.py`). This ensures:
  - Qdrant (vector DB) ↔ Neo4j (graph DB) sync
  - Token-based chunking (512 tokens, 50 overlap)
  - LLM concept extraction (GPT-4o-mini)
  - Rollback safety
- **Ingestion entry points:**
  - CLI: `python tools/orchestrator_v2.py --input <file> --type document`
  - API: `uvicorn tools.ingestion_api:app --port 8001`
  - Batch: `python tools/batch_ingest.py --dir <folder>`
- **Key data stores:**
  - Qdrant (vector search)
  - Neo4j (semantic/knowledge graph)
  - GNN output (planned/experimental)

## Key Conventions & Patterns
- **All ingestion, updates, and deletions must use the orchestrator pipeline.**
- **Metadata and semantic structure** are defined in `schema/global_schema.json` and `meta-graph/index.jsonld`.
- **Formal theory** is in `theory/formal/efc_master.tex` and `theory/formal/efc_master.pdf`.
- **APIs** are described in `api/` (see `README_API.md` and `README_API.jsonld`).
- **Automation scripts** are in `scripts/` and are auto-documented.
- **Meta/cognitive process** is documented in `meta/` and `START-HERE.md`.

## Developer Workflows
- **Ingest new data:** Use the orchestrator pipeline (see above).
- **Run tests:** Use `test_*.py` scripts (e.g., `python test_theory_auth.py`).
- **Debug/validate state:** Use scripts in `scripts/` and monitor logs (e.g., `monitor_ingest.sh`).
- **API development:** Work in `api/` and use `uvicorn` for local endpoints.

## Integration & External Dependencies
- **Qdrant**: Vector DB for RAG and semantic search (see `.env` for config).
- **Neo4j**: Knowledge graph backend (see `.env` for config).
- **LLM**: GPT-4o-mini for concept extraction during ingestion.
- **DOI/Figshare**: Open-science integration (see `figshare/`).

## Examples
- Ingest a document:
  ```bash
  python tools/orchestrator_v2.py --input README.md --type document
  ```
- Start ingestion API:
  ```bash
  uvicorn tools.ingestion_api:app --port 8001
  ```
- Batch ingest:
  ```bash
  python tools/batch_ingest.py --dir theory/
  ```

## References
- **Orientation:** `START-HERE.md`
- **Ingestion pipeline:** `tools/INGESTION_PIPELINE.md`
- **Meta layer:** `meta/README.md`
- **Schema:** `schema/global_schema.json`
- **API:** `api/README_API.md`

---
**Always use the orchestrator pipeline for any data changes.**
