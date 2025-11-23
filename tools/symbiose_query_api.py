#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os
import json
from pathlib import Path

# Optional imports – fanges i try/except
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import CollectionDescription
except ImportError:
    QdrantClient = None
    CollectionDescription = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import networkx as nx
except ImportError:
    nx = None


app = FastAPI()


# ------------------------
# MODELS
# ------------------------

class QueryRequest(BaseModel):
    text: str


# ------------------------
# NEO4J STATUS
# ------------------------

def get_neo4j_status():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not (uri and user and password):
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD.",
            "uri": None,
            "database": None,
            "node_count": None,
            "relationship_count": None,
        }

    if GraphDatabase is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "neo4j driver not installed.",
            "uri": uri,
            "database": database,
            "node_count": None,
            "relationship_count": None,
        }

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as session:
            node_count = session.run(
                "MATCH (n) RETURN count(n) AS c"
            ).single().get("c", 0)

            rel_count = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            ).single().get("c", 0)

        driver.close()
        return {
            "status": "ok",
            "connected": True,
            "reason": None,
            "uri": uri,
            "database": database,
            "node_count": node_count,
            "relationship_count": rel_count,
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "reason": str(e),
            "uri": uri,
            "database": database,
            "node_count": None,
            "relationship_count": None,
        }


# ------------------------
# QDRANT / RAG STATUS
# ------------------------

def get_qdrant_status():
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")

    if not url:
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing QDRANT_URL.",
            "url": None,
            "collection": None,
            "vectors_count": None,
        }

    if QdrantClient is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "qdrant-client not installed.",
            "url": url,
            "collection": collection,
            "vectors_count": None,
        }

    try:
        client = QdrantClient(url=url, api_key=api_key)
        info = client.get_collection(collection)  # type: CollectionDescription

        vectors_count = None
        # Ny Qdrant (1.8+)
        if hasattr(info, "points_count"):
            vectors_count = info.points_count
        # Eldre felt
        if vectors_count is None and hasattr(info, "vectors_count"):
            vectors_count = info.vectors_count

        return {
            "status": "ok",
            "connected": True,
            "reason": None,
            "url": url,
            "collection": collection,
            "vectors_count": vectors_count,
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "reason": str(e),
            "url": url,
            "collection": collection,
            "vectors_count": None,
        }


# ------------------------
# GNN / GRAPH STATUS
# ------------------------

def load_graph_state():
    """
    Leser inn symbiose_gnn_output/node_embeddings.json og node_mapping.json
    hvis de finnes i containeren. Dette gir deg et "passivt" graf/embedding-lag
    som du kan aktivere senere i /query.
    """
    base = Path(__file__).resolve().parent
    emb_path = base / "symbiose_gnn_output" / "node_embeddings.json"
    map_path = base / "symbiose_gnn_output" / "node_mapping.json"

    if not emb_path.exists() or not map_path.exists():
        return {
            "status": "pending",
            "enabled": False,
            "reason": "GNN output files not found.",
            "nodes": None,
            "embedding_dim": None,
        }

    try:
        with emb_path.open() as f:
            embeddings = json.load(f)
        with map_path.open() as f:
            mapping = json.load(f)

        node_ids = list(mapping.keys())
        nodes_count = len(node_ids)

        emb_dim = None
        if nodes_count > 0:
            sample_key = node_ids[0]
            vec = embeddings.get(sample_key) or next(iter(embeddings.values()))
            emb_dim = len(vec) if isinstance(vec, list) else None

        return {
            "status": "ok",
            "enabled": True,
            "reason": None,
            "nodes": nodes_count,
            "embedding_dim": emb_dim,
        }

    except Exception as e:
        return {
            "status": "error",
            "enabled": False,
            "reason": f"Failed to load GNN state: {e}",
            "nodes": None,
            "embedding_dim": None,
        }


GRAPH_STATE = load_graph_state()


# ------------------------
# ENDPOINTS
# ------------------------

@app.get("/health")
async def health():
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "status": "ok",
        "api": "symbiose-query-api-v1",
        "timestamp": utc_now
    }


@app.get("/context")
async def context():
    """
    v3 – full symbiose-state:
    - node/system
    - EFC meta
    - Neo4j-status
    - Qdrant/RAG-status
    - GNN/graph-status
    Designet for MSTY Live Context + LLM reasoning.
    """
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"

    neo4j_status = get_neo4j_status()
    qdrant_status = get_qdrant_status()

    graph_block = {
        "status": GRAPH_STATE.get("status"),
        "enabled": GRAPH_STATE.get("enabled"),
        "reason": GRAPH_STATE.get("reason"),
        "nodes": GRAPH_STATE.get("nodes"),
        "embedding_dim": GRAPH_STATE.get("embedding_dim"),
        "notes": "Graph engine for EFC + MetaNodes can hook in here (v4)."
    }

    return {
        "context_version": "v3",
        "timestamp": utc_now,

        "symbiose": {
            "node": "cloud-run",
            "region": "europe-north1",
            "mode": "live",
            "state": "running",
            "role": "global_context_provider",
            "purpose": "Provide unified symbiose state for MSTY + LLMs.",
            "revision": "dynamic"
        },

        "system": {
            "utc": utc_now,
            "heartbeat": True,
            "api_version": "v1",
            "container": {
                "cpu_limit": "auto",
                "memory_limit": "auto"
            }
        },

        "efc": {
            "active": True,
            "mode": "base",
            "version": "draft",
            "notes": [
                "CMB reinterpretation through entropy flow.",
                "s₀/s₁ gradient architecture.",
                "Grid-Higgs / halo coupling structure."
            ]
        },

        "neo4j": neo4j_status,
        "rag": qdrant_status,

        "axes": {
            "status": "pending",
            "imx_active": False,
            "cognitive_axes": {
                "axis_clarity": None,
                "axis_resonance": None,
                "axis_density": None,
                "axis_stability": None
            }
        },

        "graph": graph_block,

        "pipeline": {
            "repo": "github.com/supertedai/energyflow-cosmology",
            "last_commit": "pending",
            "auto_sync": True,
            "figshare_sync": "running",
            "semantic_layer": "OK"
        },

        "extensions": {
            "gnn_ready": GRAPH_STATE.get("enabled") is True,
            "metadata_ready": True,
            "multiagent_mode": "disabled",
            "night_mode": False
        },

        "placeholders": {
            "axes_status": "pending",
            "graph_status": GRAPH_STATE.get("status"),
            "gnn_status": GRAPH_STATE.get("status"),
        }
    }


@app.post("/query")
async def query(req: QueryRequest):
    """
    v1: enkel echo med versjonsmarkør.
    v2/v3: her kan vi koble inn:
      - Neo4j-spørring
      - Qdrant RAG (efc-collection)
      - GNN/graph-resonans
    """
    return {
        "response": f"symbiose-query-api-v1: {req.text}"
    }
