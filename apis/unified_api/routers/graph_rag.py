# FILE: /opt/symbiose/repo/apis/unified_api/routers/graph_rag.py

from fastapi import APIRouter, Query
from apis.unified_api.clients.graph_rag_client import graph_rag_query

router = APIRouter(tags=["graph-rag"])


def combined_graph_rag(query: str, limit: int = 10):
    """
    Wrapper-funksjon brukt av unified_query.py.
    """
    return graph_rag_query(query, limit)


@router.get("/search")
def graph_rag_endpoint(
    query: str = Query(..., description="Søkestreng"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Kombinert Neo4j + Qdrant-søk via API-endepunkt.
    Route: GET /graph-rag/search?query=...&limit=...
    """
    return combined_graph_rag(query, limit)
