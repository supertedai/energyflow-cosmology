# FILE: /opt/symbiose/repo/apis/unified_api/routers/rag.py

from fastapi import APIRouter, Query
from apis.unified_api.clients.qdrant_client import qdrant_search

router = APIRouter(tags=["rag"])


def do_rag_search(query: str, limit: int = 5):
    """
    Wrapper-funksjon brukt av unified_query.py.
    """
    return qdrant_search(query, limit=limit)


@router.get("/search")
def search_endpoint(
    query: str = Query(..., description="Søkestreng"),
    limit: int = Query(5, ge=1, le=50)
):
    """
    Enkelt RAG-søk direkte mot Qdrant.
    Route: GET /rag/search?query=...&limit=...
    """
    return do_rag_search(query, limit)
