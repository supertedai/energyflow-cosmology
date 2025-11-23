#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symbiose Query API v4
=====================

Gir tre hoved-endpoints:

- /health       → basis status
- /context      → full symbiose-state for MSTY Live Context
- /unified_query → samlet RAG + Graph + Axes + GNN-respons

Dette er "one stop API" for hele symbiosen.
"""

import datetime
import os
import json
from typing import Optional, List, Dict

from fastapi import FastAPI
from pydantic import BaseModel

# Optional imports
try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client import models as qm
except Exception:
    QdrantClient = None

import hashlib
import random


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI()


# =====================================================
# MODELS
# =====================================================

class UnifiedQueryRequest(BaseModel):
    text: str
    rag_top_k: int = 5
    graph_limit: int = 10
    use_rag: bool = True
    use_graph: bool = True
    use_axes: bool = True


# =====================================================
# INTERNAL HELPERS
# =====================================================

def deterministic_embedding(text: str, dim: int = 1536) -> List[float]:
    """Reproduserbar hashing-embedding."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(seed)
    return [rnd.random() for _ in range(dim)]


# -----------------------------
# Neo4j Helpers
# -----------------------------

def get_neo4j_config():
    return (
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        os.getenv("NEO4J_DATABASE", "neo4j"),
    )


def get_neo4j_driver():
    uri, user, password, _ = get_neo4j_config()
    if not uri or not user or not password:
        return None
    if GraphDatabase is None:
        return None
    try:
        return GraphDatabase.driver(uri, auth=(user, password))
    except Exception:
        return None


def neo4j_status():
    uri, user, password, database = get_neo4j_config()

    if not uri:
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD",
            "uri": None,
            "database": None,
        }

    if GraphDatabase is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "neo4j-driver not installed",
            "uri": uri,
            "database": database,
        }

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as s:
            node_count = s.run("MATCH (n) RETURN count(n) AS c").single().get("c")
            rel_count = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single().get("c")

        driver.close()

        return {
            "status": "ok",
            "connected": True,
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
        }


# -----------------------------
# Qdrant Helpers
# -----------------------------

def get_qdrant_config():
    return (
        os.getenv("QDRANT_URL"),
        os.getenv("QDRANT_API_KEY"),
        os.getenv("QDRANT_COLLECTION", "efc"),
    )


def get_qdrant_client():
    url, api, _ = get_qdrant_config()
    if not url or QdrantClient is None:
        return None
    try:
        return QdrantClient(url=url, api_key=api)
    except Exception:
        return None


def qdrant_status():
    url, api_key, collection = get_qdrant_config()
    if not url:
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing QDRANT_URL",
            "url": None,
            "collection": None,
        }

    if QdrantClient is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "qdrant-client not installed",
            "url": url,
            "collection": collection,
        }

    try:
        client = QdrantClient(url=url, api_key=api_key)
        info = client.get_collection(collection)
        vc = getattr(info, "vectors_count", None)

        return {
            "status": "ok",
            "connected": True,
            "reason": None,
            "url": url,
            "collection": collection,
            "vectors_count": vc,
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "reason": str(e),
            "url": url,
            "collection": collection,
        }


# =====================================================
# ENDPOINTS
# =====================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api": "symbiose-query-api-v1",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@app.get("/context")
async def context():
    """Live context for MSTY."""
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"

    return {
        "context_version": "v3",
        "timestamp": utc_now,

        "symbiose": {
            "node": "cloud-run",
            "region": "europe-north1",
            "mode": "live",
            "state": "running",
            "role": "global_context_provider",
        },

        "system": {
            "utc": utc_now,
            "heartbeat": True,
            "api_version": "v1"
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

        "neo4j": neo4j_status(),
        "rag": qdrant_status(),

        "axes": {
            "status": "pending"
        },

        "graph": {
            "status": "pending",
            "enabled": False,
        },

        "pipeline": {
            "repo": "github.com/supertedai/energyflow-cosmology",
            "auto_sync": True,
            "semantic_layer": "OK"
        },

        "extensions": {
            "gnn_ready": False
        }
    }


@app.post("/unified_query")
async def unified_query(req: UnifiedQueryRequest):
    """
    Kombinert RAG + Graph + Axes + GNN-state.
    Returnerer alt som trengs for AI-resonnement.
    """

    text = req.text
    rag_part = None
    graph_part = None
    axes_part = None

    # -----------------------------
    # RAG
    # -----------------------------
    rag_hits = 0
    if req.use_rag:
        rag_s = qdrant_status()

        client = get_qdrant_client()
        _, _, collection = get_qdrant_config()

        if client:
            vec = deterministic_embedding(text)
            try:
                hits = client.search(
                    collection_name=collection,
                    query_vector=vec,
                    limit=req.rag_top_k,
                    with_payload=True,
                )
                results = []
                for h in hits:
                    results.append({
                        "id": h.id,
                        "score": h.score,
                        "payload": h.payload,
                    })
                rag_hits = len(results)

                rag_part = {
                    "status": rag_s,
                    "results": results
                }
            except Exception as e:
                rag_part = {
                    "status": {"status": "error", "reason": f"{e}"},
                    "results": []
                }
        else:
            rag_part = {
                "status": rag_s,
                "results": []
            }

    # -----------------------------
    # GRAPH
    # -----------------------------
    graph_hits = 0
    if req.use_graph:
        driver = get_neo4j_driver()
        uri, user, password, database = get_neo4j_config()

        if driver:
            try:
                with driver.session(database=database) as s:
                    res = s.run(
                        """
                        MATCH (n)
                        WHERE (exists(n.title) AND toString(n.title) CONTAINS $q)
                           OR (exists(n.name) AND toString(n.name) CONTAINS $q)
                           OR (exists(n.slug) AND toString(n.slug) CONTAINS $q)
                        RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props
                        LIMIT $limit
                        """,
                        q=text,
                        limit=req.graph_limit
                    )
                    out = []
                    for r in res:
                        out.append({
                            "id": r["id"],
                            "labels": r["labels"],
                            "properties": r["props"],
                        })
                    graph_hits = len(out)

                    graph_part = {
                        "status": {"status": "ok", "connected": True, "uri": uri},
                        "results": out
                    }
            except Exception as e:
                graph_part = {
                    "status": {"status": "error", "reason": str(e), "uri": uri},
                    "results": []
                }
        else:
            graph_part = {
                "status": {"status": "pending", "reason": "no driver"},
                "results": []
            }

    # -----------------------------
    # AXES
    # -----------------------------
    if req.use_axes:
        clarity = max(0.0, min(1.0, 1 - len(text) / 4000))
        resonance = min(1.0, rag_hits / 10)
        density = min(1.0, graph_hits / 10)
        stability = 0.5

        axes_part = {
            "status": "ok",
            "axes": {
                "axis_clarity": clarity,
                "axis_resonance": resonance,
                "axis_density": density,
                "axis_stability": stability
            }
        }

    # -----------------------------
    # FINAL SUMMARY
    # -----------------------------
    summary = [
        "Unified Query v4 – Sammendrag:",
        f"- RAG: {rag_hits} treff",
        f"- Graph: {graph_hits} treff",
    ]
    if axes_part:
        ax = axes_part["axes"]
        summary.append(
            f"- Akseskår: klarhet={ax['axis_clarity']:.2f}, "
            f"resonans={ax['axis_resonance']:.2f}, "
            f"tetthet={ax['axis_density']:.2f}, "
            f"stabilitet={ax['axis_stability']:.2f}"
        )

    final_text = "\n".join(summary)

    return {
        "input": {
            "text": text,
            "rag_top_k": req.rag_top_k,
            "graph_limit": req.graph_limit
        },
        "components": {
            "rag": rag_part,
            "graph": graph_part,
            "axes": axes_part
        },
        "final": {
            "answer": final_text
        }
    }
