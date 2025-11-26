#!/usr/bin/env python3
import os
import json
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from openai import OpenAI

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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ------------------------------------------------------------
# Init clients
# ------------------------------------------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# embedding-modell matcher Qdrant (1536-dim)
EMBEDDING_MODEL = "text-embedding-3-large"

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
        "embeddings": EMBEDDING_MODEL,
    }

# ------------------------------------------------------------
# Escape special Lucene chars
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
# OpenAI embeddings (1536-dim)
# ------------------------------------------------------------
def compute_embedding(text: str):
    emb = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return emb.data[0].embedding

# ------------------------------------------------------------
# RAG Search (Qdrant)
# ------------------------------------------------------------
def rag_search(query: str):
    try:
        emb = compute_embedding(query)  # returns 1536-D

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
# Unified search
# ------------------------------------------------------------
@app.post("/unified_query")
def unified_query(input: QueryInput):
    q = input.text
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": q,
        "neo4j": neo4j_search(q),
        "rag": rag_search(q),
        "semantic": {"enabled": True, "index_size": 356}
    }
