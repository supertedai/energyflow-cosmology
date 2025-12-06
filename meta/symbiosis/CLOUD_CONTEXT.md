# Symbiosis Cloud Context (Qdrant, Neo4j, Graph-RAG, GNN, Hetzner)

This note captures the end-state intent for the Symbiosis runtime across cloud services and the Hetzner runtime-master. It aligns vector memory (Qdrant Cloud), graph memory (Neo4j Aura or self-hosted), Graph-RAG APIs, GNN embeddings, and the Hetzner control plane.

## What Symbiosis Should Deliver
- Unified retrieval layer: vector RAG + graph RAG exposed via `unified-api` and a lightweight `graph_rag_api`.
- Durable memory: Qdrant stores text embeddings; Neo4j stores structured graph and logs.
- Model loop: GNN consumes Neo4j graph → produces node embeddings for downstream ranking or hybrid retrieval.
- Reliable runtime: Hetzner acts as runtime-master; GitHub remains code-master; cloud services are pluggable.

## Qdrant Cloud (Vector RAG)
- Purpose: store embeddings for repo text, papers, and other unstructured artifacts.
- Inputs: `tools/rag_ingest_repo.py`, `tools/rag_ingest_efc.py`, and future pipelines.
- Access: `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` (default `efc`); toggle with `ENABLE_QDRANT=1`.
- API usage: `/rag/search` in `apis/unified_api`, plus compatibility wrappers in `clients/qdrant_client.py`.
- Embeddings: local stub works without a model; enable `ENABLE_EMBED=1` for real SentenceTransformer embeddings when allowed.

## Neo4j Cloud (Graph Memory)
- Purpose: authoritative knowledge graph (EFCPaper, MetaNode, etc.) plus logging/metadata.
- Access: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`; toggle with `ENABLE_NEO4J=1` where applicable.
- APIs:
  - `/neo4j/q` (ad-hoc Cypher) via `routers/neo4j.py`
  - `/graph-rag/search` via `routers/graph_rag.py`
  - Standalone `tools/graph_rag_api.py` for a minimal graph-only endpoint
- Ingest: use the Cypher files under `neo4j/` to seed schema and content.

## Graph-RAG
- Goal: combine Neo4j hits (structured concepts/papers) with Qdrant semantic matches.
- Code paths: `apis/unified_api/clients/graph_rag_client.py` and `routers/graph_rag.py`.
- Expected flow: Neo4j search → optional Qdrant semantic ranking → unified JSON response. Requires both services configured; otherwise runs in degraded mode.

## GNN (Graph Embeddings)
- Purpose: learn node embeddings over the Neo4j graph to support hybrid ranking and downstream tasks.
- Code: `symbiose_gnn/` (`train.py`, `embed.py`, `data_loader.py`, `model.py`).
- Inputs: live Neo4j graph (see `data_loader.py`); config via `symbiose_gnn/config.py`.
- Outputs: `symbiose_gnn_output/gnn_model.pt`, `node_embeddings.json`, `node_mapping.json`.
- Runbook: set Neo4j env vars → `python -m symbiose_gnn.train` (train) → `python -m symbiose_gnn.embed` (export embeddings).

## Hetzner Runtime-Master
- Role: orchestrates API services, manages secrets, and bridges to cloud resources.
- Services to run: `unified-api` (FastAPI), optional `graph_rag_api`, background ingest jobs, GNN batch runs.
- Network: outbound to Qdrant Cloud and Neo4j Aura/self-hosted endpoints; ensure TLS and restricted firewall rules.
- Secrets: stored in Hetzner secure store or env files, never in repo.
- Deploy: containerized via Dockerfiles in `apis/unified_api` and `tools/graph_rag_api.py` (can be wrapped in a simple Dockerfile).

## Operational Checklist
- [ ] Set Qdrant secrets (`QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`, `ENABLE_QDRANT=1`, optional `ENABLE_EMBED=1`).
- [ ] Set Neo4j secrets (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `ENABLE_NEO4J=1`).
- [ ] Seed Neo4j with `neo4j/*.cypher`.
- [ ] Ingest text to Qdrant via `tools/rag_ingest_repo.py` (or `rag_ingest_efc.py`).
- [ ] Start APIs: `uvicorn apis.unified_api.main:app --port 8000` (and optionally `graph_rag_api.py`).
- [ ] Train and export GNN embeddings once the graph is live.
- [ ] Expose services via Hetzner reverse proxy with TLS; restrict inbound/egress as needed.

## Current Status (6. desember 2025)

### ✅ FUNGERENDE
- **Qdrant Cloud**: Tilkoblet og operativ via HTTPS API (bf12db8d...us-east4-0.gcp.cloud.qdrant.io)
- **Neo4j Aura**: Tilkoblet (119e751c.databases.neo4j.io), 5 noder lastet
- **Unified API**: Kjører på port 8080 med `.env` loaded
- **Semantic Vector Search**: Implementert med OpenAI text-embedding-3-large (3072-dim)
- **RAG Endpoint**: `/rag/search` returnerer ekte similarity scores (cosine distance)
- **GNN**: Artefakter i `symbiose_gnn_output/` lastes OK (16,576 parametere, 5 noder × 64-dim)

### 🔄 I ARBEID
- **RAG Kvalitet**: Ny `tools/rag_ingest_clean.py` opprettet for clean text extraction
  - Problem: Eksisterende Qdrant data har full JSON-LD som `text` (ikke description)
  - Løsning: Extraherer `description`/`summary` felt, chunker 300-800 chars, dedup via hash
  - Status: Script ferdig, venter på re-ingest (tar tid pga OpenAI API-kall per chunk)
  
- **Ingest Pipeline**: `apis/unified_api/clients/qdrant_client.py` oppdatert med:
  - Smart chunking (600 chars, 100 overlap, sentence boundary detection)
  - Hash-basert deduplication
  - Rik metadata (layer, doi, title, description, source_type, section)

### 🚧 BLOKKERE
- **Re-ingest tid**: OpenAI embeddings tar ~1-2 sek per chunk (100+ filer = lang kjøretid)
- **Neo4j edges**: Grafen har 5 noder men 0 kanter (trenger data seeding)

### 📋 NESTE STEG
1. Kjør `tools/rag_ingest_clean.py` i bakgrunnen (tar 10-30 min)
2. Seed Neo4j med `neo4j/*.cypher` filer
3. Test Graph-RAG hybrid search med begge tjenester aktive
4. Tren GNN på full Neo4j graf
