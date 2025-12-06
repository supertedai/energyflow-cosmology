# apis/unified_api/routers/neo4j.py

from fastapi import APIRouter
from apis.unified_api.clients.neo4j_client import run_query

router = APIRouter()


def run_cypher(query: str, params: dict | None = None):
    """
    Wrapper used by old modules. 
    Unified version delegates to run_query().
    """
    return run_query(query, params or {})


@router.get("/status")
def neo_status():
    """Return simple connectivity check."""
    try:
        result = run_query("RETURN 1 AS n")
        return {"neo4j": "connected", "result": result[0]["n"]}
    except Exception as e:
        return {"neo4j": "error", "detail": str(e)}


@router.get("/q")
def query_endpoint_get(query: str):
    """Manual test endpoint: /neo4j/q?query=RETURN 1"""
    return run_cypher(query)


@router.post("/q")
def query_endpoint_post(payload: dict):
    """POST endpoint for Neo4j queries with optional params."""
    query = payload.get("query")
    params = payload.get("params", {})
    if not query:
        return {"error": "Missing 'query' field in request body"}
    return run_cypher(query, params)

