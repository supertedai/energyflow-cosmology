#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os
import json

# Optional drivers
try:
    from neo4j import GraphDatabase
except:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import SearchRequest, NamedVector
except:
    QdrantClient = None

app = FastAPI(title="Symbiose Unified API", version="v6")


# ---------------------------------------------
# MODELS
# ---------------------------------------------
class UnifiedQuery(BaseModel):
    text: str
    max_results: int = 5


# ---------------------------------------------
# HELPERS → NEO4J
# ---------------------------------------------
def neo4j_query(text: str):
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "neo4j")

    if GraphDatabase is None:
        return {"enabled": False, "reason": "neo4j-driver missing", "matches": []}

    if not (uri and user and password):
        return {"enabled": False, "reason": "Missing env vars", "matches": []}

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=db) as session:
            q = """
            CALL db.index.fulltext.queryNodes('efc_index', $q)
            YIELD node, score
            RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
            ORDER BY score DESC LIMIT 5
            """
            rows = session.run(q, {"q": text})
            data = [r.data() for r in rows]

        driver.close()
        return {"enabled": True, "matches": data}

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}


# ---------------------------------------------
# HELPERS → QDRANT (RAG)
# ---------------------------------------------
def qdrant_search(text: str, limit=5):
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")

    if QdrantClient is None:
        return {"enabled": False, "reason": "qdrant-client missing", "matches": []}

    if not (url and api_key):
        return {"enabled": False, "reason": "Missing Qdrant config", "matches": []}

    try:
        client = QdrantClient(url=url, api_key=api_key)

        # dummy embedding (erstattes når lokal embedder er aktiv)
        embedding = [0.1] * 3072

        search_result = client.search(
            collection_name=collection,
            query_vector=embedding,
            limit=limit
        )

        matches = []
        for hit in search_result:
            matches.append({
                "text": hit.payload.get("text"),
                "paper": hit.payload.get("paper_title"),
                "slug": hit.payload.get("slug"),
                "score": hit.score
            })

        return {"enabled": True, "matches": matches}

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}


# ---------------------------------------------
# ENDPOINTS
# ---------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "unified-symbiose-v6",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@app.get("/context")
def context():
    return {
        "context_version": "v6",
        "neo4j": bool(os.getenv("NEO4J_URI")),
        "qdrant": bool(os.getenv("QDRANT_URL")),
        "semantic_index": True,
    }


@app.post("/unified_query")
def unified_query(req: UnifiedQuery):

    try:
        with open("semantic-search-index.json") as f:
            semantic = json.load(f)
    except:
        semantic = {}

    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "query": req.text,
        "neo4j": neo4j_query(req.text),
        "rag": qdrant_search(req.text, req.max_results),
        "semantic": {"enabled": True, "index_size": len(semantic)},
    }
