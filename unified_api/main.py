#!/usr/bin/env python3
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "efc_docs"

# ------------------------------------------------------------
# Init clients
# ------------------------------------------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# ------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------
app = FastAPI()

class QueryInput(BaseModel):
    text: str

# ------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "unified-api",
        "neo4j": bool(NEO4J_URI),
        "qdrant": bool(QDRANT_URL),
    }

# ------------------------------------------------------------
# Lucene escape fix
# ------------------------------------------------------------
def escape_lucene(q: str) -> str:
    if not q:
        return ""
    special = r'+ - && || ! ( ) { } [ ] ^ " ~ * ? : \ /'
    out = q
    for c in special.split():
        out = out.replace(c, f"\\{c}")
    return out

# ------------------------------------------------------------
# Neo4j search
# ------------------------------------------------------------
def neo4j_search(query: str):
    safe = escape_lucene(query)
    cypher = """
    CALL db.index.fulltext.queryNodes('efc_index', $q)
    YIELD node, score
    RETURN node.title AS title,
           node.slug AS slug,
           node.keywords AS keywords,
           score
    ORDER BY score DESC LIMIT 20
    """
    try:
        with driver.session(database=NEO4J_DATABASE) as s:
            res = s.run(cypher, q=safe).data()
        return {"enabled": True, "matches": res}
    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}

# ------------------------------------------------------------
# RAG (Qdrant Cloud compatible)
# ------------------------------------------------------------
def rag_search(query: str):
    try:
        emb = model.encode(query).tolist()

        # Qdrant Cloud uses "vector=", not "query_vector="
        res = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            vector=emb,
            limit=20
        )

        out = []
        for r in res:
            payload = r.payload or {}
            out.append({
                "text": payload.get("text"),
                "paper": payload.get("paper"),
                "slug": payload.get("slug"),
                "score": r.score,
            })
        return {"enabled": True, "matches": out}

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}

# ------------------------------------------------------------
# Unified endpoint
# ------------------------------------------------------------
@app.post("/unified_query")
def unified_query(input: QueryInput):
    q = input.text
    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "query": q,
        "neo4j": neo4j_search(q),
        "rag": rag_search(q),
        "semantic": {"enabled": True, "index_size": 356},
    }
