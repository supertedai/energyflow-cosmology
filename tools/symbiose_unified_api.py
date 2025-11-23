from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os
import json

# Neo4j
try:
    from neo4j import GraphDatabase
except:
    GraphDatabase = None

# Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
except:
    QdrantClient = None

app = FastAPI()


# ----------------------------------------------------------
# MODELS
# ----------------------------------------------------------

class UnifiedQuery(BaseModel):
    text: str
    max_results: int = 5


# ----------------------------------------------------------
# HELPERS: NEO4J
# ----------------------------------------------------------

def neo4j_query(text: str):
    if GraphDatabase is None:
        return {"enabled": False, "matches": []}

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "neo4j")

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=db) as session:
            q = """
            CALL db.index.fulltext.queryNodes('efc_index', $query)
            YIELD node, score
            RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
            ORDER BY score DESC LIMIT 5
            """
            rows = session.run(q, query=text)
            return {"enabled": True, "matches": [r.data() for r in rows]}
    except Exception as e:
        return {"enabled": False, "error": str(e), "matches": []}


# ----------------------------------------------------------
# HELPERS: QDRANT (RAG)
# ----------------------------------------------------------

def qdrant_search(text: str, limit=5):
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")

    if QdrantClient is None:
        return {"enabled": False, "matches": []}

    try:
        client = QdrantClient(url=url, api_key=api_key)
        # Dummy embedding for nå (senere: ekte embedding)
        emb = [0.1] * 1536

        results = client.search(
            collection_name=collection,
            query_vector=emb,
            limit=limit
        )

        return {
            "enabled": True,
            "matches": [
                {
                    "text": hit.payload.get("text"),
                    "paper": hit.payload.get("paper_title"),
                    "score": hit.score
                }
                for hit in results
            ]
        }
    except Exception as e:
        return {"enabled": False, "error": str(e), "matches": []}


# ----------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "api": "unified-symbiose-v4"}


@app.post("/unified_query")
def unified_query(req: UnifiedQuery):
    """
    Samler: Neo4j + Qdrant + Semantic Index (v4)
    """

    # Load semantic index
    try:
        with open("semantic-search-index.json", "r") as f:
            semantic_data = json.load(f)
    except:
        semantic_data = {}

    return {
        "query": req.text,
        "neo4j": neo4j_query(req.text),
        "rag": qdrant_search(req.text, req.max_results),
        "semantic": {
            "enabled": True,
            "index_size": len(semantic_data),
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
