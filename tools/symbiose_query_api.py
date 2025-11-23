#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os
import json
import hashlib
import random
from pathlib import Path

# Optional imports – fanges i try/except
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import CollectionDescription, ScoredPoint
except ImportError:
    QdrantClient = None
    CollectionDescription = None
    ScoredPoint = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import networkx as nx
except ImportError:
    nx = None


app = FastAPI()

# ------------------------------------------------------------
# MODELLER
# ------------------------------------------------------------

class QueryRequest(BaseModel):
    text: str


class RagQuery(BaseModel):
    text: str
    top_k: int = 5


class GraphSearchRequest(BaseModel):
    query: str
    limit: int = 10


class GraphPathRequest(BaseModel):
    from_id: int
    to_id: int
    max_hops: int = 6


class AxesRequest(BaseModel):
    text: str
    rag_hits: Optional[int] = None
    graph_hits: Optional[int] = None


# ------------------------------------------------------------
# KONFIG / PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
EMBED_DIM = 1536  # må matche ingest-skriptet


# ------------------------------------------------------------
# HJELPERE
# ------------------------------------------------------------

def deterministic_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    """
    Identisk mekanisme som i rag_ingest.py:
    - SHA256 av tekst
    - heltall-seed
    - random.Random(seed).random() i [0,1)
    """
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]


# ------------------------
# NEO4J STATUS + CLIENT
# ------------------------

def get_neo4j_config():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    return uri, user, password, database


def get_neo4j_status():
    uri, user, password, database = get_neo4j_config()

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


def get_neo4j_driver():
    uri, user, password, _ = get_neo4j_config()
    if not (uri and user and password):
        return None
    if GraphDatabase is None:
        return None
    try:
        return GraphDatabase.driver(uri, auth=(user, password))
    except Exception:
        return None


# ------------------------
# QDRANT / RAG STATUS + CLIENT
# ------------------------

def get_qdrant_config():
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")
    return url, api_key, collection


def get_qdrant_status():
    url, api_key, collection = get_qdrant_config()

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
        if hasattr(info, "points_count"):
            vectors_count = info.points_count
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


def get_qdrant_client():
    url, api_key, _ = get_qdrant_config()
    if not url or QdrantClient is None:
        return None
    try:
        return QdrantClient(url=url, api_key=api_key)
    except Exception:
        return None


# ------------------------
# GNN / GRAPH STATE (passiv)
# ------------------------

def load_graph_state():
    emb_path = BASE_DIR / "symbiose_gnn_output" / "node_embeddings.json"
    map_path = BASE_DIR / "symbiose_gnn_output" / "node_mapping.json"

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


# ------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------

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
    Live symbiose-state for MSTY / LLM:
    - node/system
    - EFC meta
    - Neo4j-status
    - Qdrant/RAG-status
    - GNN/graph-status
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


# ------------------------------------------------------------
# RAG / QDRANT-ENDPOINT
# ------------------------------------------------------------

@app.post("/rag/search")
async def rag_search(req: RagQuery):
    """
    Enkel RAG-søk mot Qdrant collection 'efc'.
    Bruker samme embedding-funksjon som ingest.
    """
    status = get_qdrant_status()
    if status["status"] != "ok" or not status["connected"]:
        return {
            "status": status,
            "results": []
        }

    client = get_qdrant_client()
    if client is None:
        return {
            "status": {**status, "status": "error", "reason": "Qdrant client not available."},
            "results": []
        }

    _, _, collection = get_qdrant_config()
    vector = deterministic_embedding(req.text)

    try:
        hits: List[ScoredPoint] = client.search(
            collection_name=collection,
            query_vector=vector,
            limit=req.top_k,
            with_payload=True,
            with_vectors=False
        )

        results = []
        for h in hits:
            payload = h.payload or {}
            results.append({
                "id": h.id,
                "score": h.score,
                "path": payload.get("path"),
                "chunk_index": payload.get("chunk_index"),
                "paper_title": payload.get("paper_title"),
                "slug": payload.get("slug"),
                "doi": payload.get("doi"),
                "keywords": payload.get("keywords"),
                "source": payload.get("source"),
                "text": payload.get("text"),
            })

        return {
            "status": status,
            "results": results
        }

    except Exception as e:
        return {
            "status": {
                **status,
                "status": "error",
                "reason": f"RAG search failed: {e}",
            },
            "results": []
        }


# ------------------------------------------------------------
# GRAPH / NEO4J-ENDPOINTS
# ------------------------------------------------------------

@app.post("/graph/search")
async def graph_search(req: GraphSearchRequest):
    """
    Enkel tekstbasert søk mot Neo4j:
    Søk i title, name, slug.
    """
    driver = get_neo4j_driver()
    uri, _, _, database = get_neo4j_config()

    if driver is None:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": "Neo4j driver not available or config missing.",
                "uri": uri,
                "database": database,
            },
            "results": []
        }

    try:
        with driver.session(database=database) as session:
            res = session.run(
                """
                MATCH (n)
                WHERE (exists(n.title) AND toString(n.title) CONTAINS $q)
                   OR (exists(n.name) AND toString(n.name) CONTAINS $q)
                   OR (exists(n.slug) AND toString(n.slug) CONTAINS $q)
                RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props
                LIMIT $limit
                """,
                q=req.query,
                limit=req.limit
            )
            nodes = []
            for record in res:
                nodes.append({
                    "id": record["id"],
                    "labels": record["labels"],
                    "properties": record["props"]
                })

        driver.close()
        return {
            "status": {
                "status": "ok",
                "connected": True,
                "uri": uri,
                "database": database,
            },
            "results": nodes
        }

    except Exception as e:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": str(e),
                "uri": uri,
                "database": database,
            },
            "results": []
        }


@app.get("/graph/node/{node_id}")
async def graph_node(node_id: int):
    """
    Hent én node fra Neo4j basert på intern id(n).
    """
    driver = get_neo4j_driver()
    uri, _, _, database = get_neo4j_config()

    if driver is None:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": "Neo4j driver not available or config missing.",
                "uri": uri,
                "database": database,
            },
            "node": None
        }

    try:
        with driver.session(database=database) as session:
            record = session.run(
                """
                MATCH (n)
                WHERE id(n) = $id
                RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props
                """,
                id=node_id
            ).single()

        driver.close()

        if record is None:
            return {
                "status": {
                    "status": "ok",
                    "connected": True,
                    "uri": uri,
                    "database": database,
                    "reason": "Node not found."
                },
                "node": None
            }

        return {
            "status": {
                "status": "ok",
                "connected": True,
                "uri": uri,
                "database": database,
            },
            "node": {
                "id": record["id"],
                "labels": record["labels"],
                "properties": record["props"]
            }
        }

    except Exception as e:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": str(e),
                "uri": uri,
                "database": database,
            },
            "node": None
        }


@app.post("/graph/path")
async def graph_path(req: GraphPathRequest):
    """
    Korteste sti mellom to noder (intern id).
    """
    driver = get_neo4j_driver()
    uri, _, _, database = get_neo4j_config()

    if driver is None:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": "Neo4j driver not available or config missing.",
                "uri": uri,
                "database": database,
            },
            "path": None
        }

    try:
        with driver.session(database=database) as session:
            record = session.run(
                """
                MATCH (a),(b)
                WHERE id(a) = $from_id AND id(b) = $to_id
                MATCH p = shortestPath((a)-[*..$max_hops]-(b))
                RETURN p LIMIT 1
                """,
                from_id=req.from_id,
                to_id=req.to_id,
                max_hops=req.max_hops
            ).single()

        driver.close()

        if record is None:
            return {
                "status": {
                    "status": "ok",
                    "connected": True,
                    "uri": uri,
                    "database": database,
                    "reason": "No path found."
                },
                "path": None
            }

        # Forenklet representasjon av path
        p = record["p"]
        nodes = [
            {"id": n.id, "labels": list(n.labels), "properties": dict(n)}
            for n in p.nodes
        ]
        rels = [
            {
                "id": r.id,
                "type": r.type,
                "start": r.start_node.id,
                "end": r.end_node.id,
                "properties": dict(r)
            }
            for r in p.relationships
        ]

        return {
            "status": {
                "status": "ok",
                "connected": True,
                "uri": uri,
                "database": database,
            },
            "path": {
                "nodes": nodes,
                "relationships": rels
            }
        }

    except Exception as e:
        return {
            "status": {
                "status": "error",
                "connected": False,
                "reason": str(e),
                "uri": uri,
                "database": database,
            },
            "path": None
        }


# ------------------------------------------------------------
# AXES-ENDPOINT (ENKEL HEURISTIKK)
# ------------------------------------------------------------

@app.post("/axes/evaluate")
async def axes_evaluate(req: AxesRequest):
    """
    Enkel, heuristisk akseskår.
    Denne kan senere byttes til en ordentlig IMX/akses-motor.
    """
    text_len = len(req.text or "")
    rag_hits = req.rag_hits or 0
    graph_hits = req.graph_hits or 0

    # dummy-heuristikk, bare for å få tall:
    clarity = max(0.0, min(1.0, 1.0 - (text_len / 4000.0)))
    resonance = max(0.0, min(1.0, rag_hits / 10.0))
    density = max(0.0, min(1.0, graph_hits / 10.0))
    stability = 0.5  # fast inntil du vil gjøre det dynamisk

    return {
        "status": "ok",
        "axes": {
            "axis_clarity": clarity,
            "axis_resonance": resonance,
            "axis_density": density,
            "axis_stability": stability
        }
    }


# ------------------------------------------------------------
# HOVED-QUERY-ENDPOINT
# ------------------------------------------------------------

@app.post("/query")
async def query(req: QueryRequest):
    """
    v1: enkel echo med versjonsmarkør.
    v2+: kan rute via:
      - /rag/search
      - /graph/search
      - /axes/evaluate
    """
    return {
        "response": f"symbiose-query-api-v1: {req.text}"
    }
