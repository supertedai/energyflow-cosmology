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
    return {
        "status": "ok",
        "api": "symbiose-query-api-v1",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }


@app.get("/context")
async def context():
    """
    Live Context endpoint for MSTY.
    Returns clean JSON with current symbiose state.
    Expand this later with graph, rag, axes, metadata flows.
    """
    return {
        "context_version": "v1",
        "status": "ok",
        "symbiose": {
            "node": "cloud-run",
            "region": "europe-north1",
            "mode": "live",
            "state": "running",
            "message": "Symbiose live context feed operational."
        },
        "efc": {
            "active": True,
            "note": "Base context only – add Neo4j/RAG integration next."
        }
    }


@app.post("/query")
async def query(req: QueryRequest):
    """
    Simple echo-like endpoint for now.
    Later this becomes the unified Query Engine (EFC + Graph + RAG).
    """
    return {
        "response": f"symbiose-query-api-v1: {req.text}"
    }
