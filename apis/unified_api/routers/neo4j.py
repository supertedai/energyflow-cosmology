from fastapi import APIRouter
from apis.unified_api.clients.neo4j_client import run_query

router = APIRouter()

@router.get("/q")
def query(query: str):
    """
    Basic Cypher endpoint: /neo4j/q?query=...
    """
    return run_query(query)

