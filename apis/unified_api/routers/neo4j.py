from fastapi import APIRouter
from apis.unified_api.clients.neo4j_client import run_query

router = APIRouter()

def run_cypher(query: str, params: dict | None = None):
    """
    Wrapper used by unified_query.py.
    """
    return run_query(query, params or {})

@router.get("/q")
def query_endpoint(query: str):
    """Basic test endpoint: /neo4j/q?query=RETURN 1"""
    return run_cypher(query)
