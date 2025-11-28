from fastapi import APIRouter
from apis.unified_api.clients.graph_rag_client import graph_rag_query

# Router base-path styres fra main.py → prefix="/graph-rag"
router = APIRouter()

@router.get("")    # viktig: uten "/"
def graph_rag(query: str, limit: int = 10):
    """
    Kombinert Neo4j + Qdrant søk
    """
    return graph_rag_query(query, limit)

