from fastapi import APIRouter
from clients.graph_rag_client import graph_rag_query

router = APIRouter(prefix="/graph-rag", tags=["graph_rag"])

@router.get("/query")
def query(q: str, limit: int = 10):
    """
    Kombinerer Neo4j (struktur) og Qdrant (semantikk)
    """
    return graph_rag_query(q, limit)
