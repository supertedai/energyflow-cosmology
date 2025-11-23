from fastapi import FastAPI
from pydantic import BaseModel
import datetime
import os

# Optional imports – hvis ikke installert / ikke satt opp, fanges det i try/except
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

app = FastAPI()


# ------------------------
# MODELS
# ------------------------

class QueryRequest(BaseModel):
    text: str


# ------------------------
# LAZY CLIENT HELPERS
# ------------------------

def get_neo4j_status():
    """
    Returnerer enkel status + metrikker for Neo4j, basert på env-vars.
    Faller tilbake til "pending" hvis ikke satt opp eller feiler.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not (uri and user and password):
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD env vars.",
            "uri": None,
            "database": None,
            "node_count": None,
            "relationship_count": None,
        }

    if GraphDatabase is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "neo4j driver not installed in environment.",
            "uri": uri,
            "database": database,
            "node_count": None,
            "relationship_count": None,
        }

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as session:
            node_count = session.run("MATCH (n) RETURN count(n) AS c").single().get("c", 0)
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single().get("c", 0)

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


def get_qdrant_status():
    """
    Returnerer enkel status for Qdrant, basert på env-vars.
    Faller tilbake til "pending" hvis ikke satt opp eller feiler.
    """
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")

    if not url:
        return {
            "status": "pending",
            "connected": False,
            "reason": "Missing QDRANT_URL env var.",
            "url": None,
            "collection": None,
            "vectors_count": None,
        }

    if QdrantClient is None:
        return {
            "status": "error",
            "connected": False,
            "reason": "qdrant-client not installed in environment.",
            "url": url,
            "collection": collection,
            "vectors_count": None,
        }

    try:
        client = QdrantClient(url=url, api_key=api_key) if api_key else QdrantClient(url=url)
        info = client.get_collection(collection)
        vectors_count = info.vectors_count if hasattr(info, "vectors_count") else None

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
    - efc
    - neo4j-status
    - qdrant/RAG-status
    - axes/graph placeholders
    - pipeline/meta-status
    Designet for MSTY Live Context + LLM reasoning.
    """
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"

    neo4j_status = get_neo4j_status()
    qdrant_status = get_qdrant_status()

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

        "graph": {
            "status": "pending",
            "enabled": False,
            "notes": "Graph engine for EFC + MetaNodes can hook in here (v4)."
        },

        "pipeline": {
            "repo": "github.com/supertedai/energyflow-cosmology",
            "last_commit": "pending",
            "auto_sync": True,
            "figshare_sync": "running",
            "semantic_layer": "OK"
        },

        "extensions": {
            "gnn_ready": False,
            "metadata_ready": True,
            "multiagent_mode": "disabled",
            "night_mode": False
        },

        "placeholders": {
            "axes_status": "pending",
            "graph_status": "pending",
            "gnn_status": "pending"
        }
    }


@app.post("/query")
async def query(req: QueryRequest):
    """
    Nå: enkel echo med versjonsmarkør.
    Senere: plugg inn Neo4j + Qdrant + EFC-motor her.
    """
    return {
        "response": f"symbiose-query-api-v1: {req.text}"
    }
