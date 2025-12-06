# FILE: /Users/morpheus/energyflow-cosmology/apis/unified_api/routers/neo4j.py

from fastapi import APIRouter
from apis.unified_api.clients.neo4j_client import run_query

router = APIRouter(prefix="/neo4j", tags=["Neo4j"])

def run_cypher(query: str, params: dict | None = None):
    """
    Wrapper used by unified_query.py.
    """
    return run_query(query, params or {})

@router.get("/status")
def neo4j_status():
    """
    Check connectivity by running RETURN 1.
    """
    try:
        result = run_query("RETURN 1 as ok")
        return {"neo4j": "connected", "result": result[0]["ok"]}
    except Exception as e:
        return {"neo4j": "error", "error": str(e)}

@router.get("/connect")
def neo4j_connect():
    """
    Simple connection confirmation endpoint.
    """
    return {"neo4j": "connected"}

@router.get("/q")
def query_endpoint(query: str):
    """Basic test endpoint: /neo4j/q?query=RETURN 1"""
    return run_cypher(query)

