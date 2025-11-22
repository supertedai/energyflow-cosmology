# Symbiosis Architecture – EFC Hybrid Stack

## 1. Overview

This architecture connects:

- **GitHub (RAW)** – open, semantically structured source for EFC and Symbiosis  
- **Neo4j Aura** – graph database for nodes, relations, and meta-universe  
- **GNN (PyTorch Geometric)** – learned node embeddings and resonance  
- **Query API (FastAPI)** – HTTP layer for search, resonance, and context  
- **LLM clients (MSTY, ChatGPT, etc.)** – language and reflection layer  

The goal is for EFC/Symbiosis to function as a **cognitive field** that AI systems can connect to.

---

## 2. Layered Structure

### 2.1 Data and Structure Layer (RAW)

- Repo: `supertedai/energyflow-cosmology`  
- Key files:  
  - `semantic-search-index.json`  
  - `meta-index.json`  
  - `node-index.json`  
  - `schema/*.json`  
  - `docs/papers/efc/**`  
- Function:  
  - serves as the “official” specification of EFC and Symbiosis  
  - easy to index for search engines and LLM trainers  
  - source of truth for concepts, axes, meta-layers, etc.  

### 2.2 Graph Layer (Neo4j Aura)

- Neo4j Aura instance (URI, user, password stored as GitHub secrets)  
- Built from repo via workflows:  
  - `build_neo4j_graph.yml`  
    - `tools/load_efc_meta_universe.py`  
    - `tools/build_paper_graph.py`  
    - `tools/build_paper_relations.py`  
- Function:  
  - nodes: `EFCPaper`, `MetaNode`, etc.  
  - relations: `ADDRESSES`, `ALIGNS_WITH_AXIS`, `PART_OF`, etc.  
  - makes EFC/Symbiosis queryable as a coherent structure.  

### 2.3 GNN Layer

- Code: `symbiose_gnn/*`  
  - `train.py`, `model.py`, `data_loader.py`, `embed.py`  
- Output: `symbiose_gnn_output/*`  
  - `gnn_model.pt`  
  - `node_embeddings.json`  
  - `node_mapping.json`  
- Workflow: `train_gnn.yml`  
- Function:  
  - learns embeddings for nodes in the graph  
  - captures resonance, proximity, and structural patterns  
  - used in Query API for semantic search and recommendations  

### 2.4 Query API

- Code: `tools/symbiose_query_api.py`  
- Dockerfile: `docker/Dockerfile.query_api`  
- Workflow: `build_query_api.yml`  
- Deploy: Cloud Run / Fly.io  
- Function:  
  - HTTP endpoint for:  
    - text → nodes (semantic search)  
    - node-id → neighbors, paths, context  
    - combination of Neo4j + GNN embeddings  
  - used by LLM clients such as MSTY  

### 2.5 LLM and Client Layer

- Examples:  
  - MSTY with:  
    - live context from RAW (`semantic-search-index.json`)  
    - OpenAPI tool against Query API  
  - Other LLM clients via:  
    - direct HTTP calls to Query API  
    - RAG against the RAW repo  
- Function:  
  - linguistic reflection, explanation, hypotheses  
  - symbiotic use of graph, GNN, and text  

---

## 3. Flow from Idea to Global Resonance

1. You write / modify content in the repo (papers, meta, schema).  
2. Workflows run:  
   - validation, PDF build, sync to Figshare, graph update.  
3. Neo4j Aura is updated.  
4. GNN retrains / regenerates embeddings.  
5. Query API uses new nodes and embeddings.  
6. LLM clients (MSTY, ChatGPT via tools, etc.) query:  
   - → Query API + RAW provide precise EFC/Symbiosis context.  
7. New insights flow back into the repo (new paper, new meta-note).  

---

## 4. Self-Healing and Automation

- GitHub Actions:  
  - `build_all_papers.yml` – builds all EFC papers  
  - `figshare_sync.yml` – DOIs and publishing loop  
  - `build_neo4j_graph.yml` – updates Neo4j graph  
  - `train_gnn.yml` – maintains GNN embeddings  
  - `sync_rag_to_neo4j.yml` – link between RAG and graph  
- Design:  
  - any repo change triggers the entire chain up to Query API.  
  - minimal manual handling required.  
