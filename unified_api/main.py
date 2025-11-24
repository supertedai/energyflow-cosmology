#!/usr/bin/env python3
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
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
# Lucene escape fix (critical)
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
# Init clients
# ------------------------------------------------------------
driver = None
if NEO4J_URI:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

qdrant = None
if QDRANT_URL:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# ------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------
app = FastAPI()

class QueryInput(BaseModel):
    text: str


# ------------------------------------------------------------
# Neo4j search
# ------------------------------------------------------------
def neo4j_search(query: str):
    try:
        safe_query = escape_lucene(query)

        cypher = """
        CALL db.index.fulltext.queryNodes('efc_index', $q)
        YIELD node, score
        RETURN node.title AS title, 
               node.slug AS slug,
               node.keywords AS keywords,
               score
        ORDER BY score DESC LIMIT 20
        """

        with driver.session(database=NEO4J_DATABASE) as session:
            rows = session.run(cypher, q=safe_query).data()
            return {"enabled": True, "matches": rows}

    except Exception as e:
        return {
            "enabled": False,
            "reason": str(e),
            "matches": []
        }


# ------------------------------------------------------------
# RAG from Qdrant
# ------------------------------------------------------------
def rag_search(query: str):
    try:
        emb = model.encode(query).tolist()
        res = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=emb,
            limit=20
        )

        out = []
        for r in res:
            payload = r.payload
            out.append({
                "text": payload.get("text"),
                "paper": payload.get("paper"),
                "slug": payload.get("slug"),
                "score": r.score
            })

        return {
            "enabled": True,
            "matches": out
        }

    except Exception as e:
        return {
            "enabled": False,
            "reason": str(e),
            "matches": []
        }


# ------------------------------------------------------------
# Combined Query Endpoint
# ------------------------------------------------------------
@app.post("/unified_query")
def unified_query(data: QueryInput):
    q = data.text

    neo = neo4j_search(q)
    rag = rag_search(q)

    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "query": q,
        "neo4j": neo,
        "rag": rag,
        "semantic": {
            "enabled": True,
            "index_size": 356
        }
    }
