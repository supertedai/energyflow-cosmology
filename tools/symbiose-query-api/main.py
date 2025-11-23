from fastapi import FastAPI
from pydantic import BaseModel
import datetime

app = FastAPI()


# ------------------------
# MODELS
# ------------------------

class QueryRequest(BaseModel):
    text: str


# ------------------------
# ENDPOINTS
# ------------------------

@app.get("/health")
async def health():
    """Health check for Cloud Run / monitoring / MSTY."""
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "status": "ok",
        "api": "symbiose-query-api-v1",
        "timestamp": utc_now,
    }


@app.get("/context")
async def context():
    """
    Live Context endpoint for MSTY.
    v2: Stabil symbiose-state som kan utvides med Neo4j/RAG/aksene senere.
    """
    utc_now = datetime.datetime.utcnow().isoformat() + "Z"

    return {
        "context_version": "v2",
        "timestamp": utc_now,
        "symbiose": {
            "node": "cloud-run",
            "region": "europe-north1",
            "mode": "live",
            "state": "running",
            "role": "global_context_provider",
            "purpose": "Provide MSTY with live symbiose state snapshots."
        },
        "system": {
            "utc": utc_now,
            "heartbeat": True,
            "api_version": "v1",
            "cloud_run_revision": "dynamic"
        },
        "efc": {
            "active": True,
            "mode": "base",
            "note": "Neo4j, RAG and metadata integration will be added in the next version."
        },
        "placeholders": {
            "neo4j_status": "pending",
            "rag_status": "pending",
            "axes_status": "pending",
            "graph_status": "pending"
        }
    }


@app.post("/query")
async def query(req: QueryRequest):
    """
    Enkel query-endpoint.
    Nå: echo med versjonsmarkør.
    Senere: kobles til Neo4j, RAG, EFC-motor osv.
    """
    return {
        "response": f"symbiose-query-api-v1: {req.text}"
    }
