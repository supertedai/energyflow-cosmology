from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os
import json

# Optional drivers (fallback hvis ikke installert)
try:
    from neo4j import GraphDatabase
except:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
except:
    QdrantClient = None


app = FastAPI()


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
            CALL db.index.fulltext.queryNodes('efc_index', $query)
            YIELD node, score
            RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
            ORDER BY score DESC LIMIT 5
            """
            rows = session.run(q, query=text)
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

    try:
        client = QdrantClient(url=url, api_key=api_key)

        # Dummy embedding (erstattes senere)
        emb = [0.1] * 1536

        result = client.search(
            collection_name=collection,
            query_vector=emb,
            limit=limit
        )

        return {
            "enabled": True,
            "matches": [
                {
                    "text": h.payload.get("text"),
                    "paper": h.payload.get("paper_title"),
                    "slug": h.payload.get("slug"),
                    "score": h.score
                }
                for h in result
            ]
        }

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}


# ---------------------------------------------
# ENDPOINTS
# ---------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "unified-symbiose-v4",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@app.get("/context")
def context():
    utc = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "context_version": "v4",
        "timestamp": utc,
        "system": {
            "utc": utc,
            "container": {"cpu": "auto", "mem": "auto"},
        },
        "neo4j": "see /unified_query",
        "rag": "see /unified_query",
        "semantic_index": "loaded",
        "symbiose": {
            "node": "cloud-run",
            "region": os.getenv("REGION", "europe-west1"),
            "mode": "live",
            "state": "running",
            "api": "unified",
        },
    }


@app.post("/unified_query")
def unified_query(req: UnifiedQuery):

    # semantic index
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
        "semantic": {
            "enabled": True,
            "index_size": len(semantic)
        }
    }
