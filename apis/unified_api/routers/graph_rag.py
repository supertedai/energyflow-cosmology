from fastapi import APIRouter
from apis.unified_api.clients.graph_rag_client import graph_rag_query

router = APIRouter()

def combined_graph_rag(query: str, limit: int = 10):
    """
    Wrapper-funksjon brukt av unified_query.py.
    """
    return graph_rag_query(query, limit)

@router.get("")
def graph_rag_endpoint(query: str, limit: int = 10):
    """
    Kombinert Neo4j + Qdrant søk via API-endepunkt.
    """
    return combined_graph_rag(query, limit)
