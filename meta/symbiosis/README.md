# Symbiosis Runtime — EFC Ecosystem

## Overview  
Symbiosis is the runtime subsystem for the Energy-Flow Cosmology (EFC) framework.  
It unifies APIs, memory graph (Neo4j), embedding store (Qdrant), agent orchestration, logging and RAG-based retrieval to support meta-cognitive workflows.  

## Goals  
- Provide a stable runtime backbone for EFC.  
- Enable layered architecture: unified-api, query-api, graph-rag-api.  
- Maintain clear separation: Hetzner as runtime master; all other services as clients.  
- Support audit, logging and reproducibility through structured metadata and versioning.  

## Key Components  
- Neo4j graph backend (knowledge & context graph)  
- Qdrant vector store (embeddings + RAG memory)  
- Unified-API / Query-API / Graph-RAG-API (interaction layer)  
- Logging & conversation tracking pipeline (e.g. via proxy)  
- Metadata layer (JSON-LD / CodeMeta / schema.org)  

## Quickstart / Deployment  
(To fill out when baseline is stable.)  

## Contribution & License  
(Describe license, contribution guidelines, code ownership etc.)  
