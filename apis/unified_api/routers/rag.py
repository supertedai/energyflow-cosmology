from fastapi import APIRouter
from apis.unified_api.clients.qdrant_client import qdrant_search

router = APIRouter()

def do_rag_search(query: str, limit: int = 5):
    """
    Wrapper funksjon brukt av unified_query.py.
    """
    return qdrant_search(query, limit=limit)

@router.get("/search")
def search_endpoint(query: str, limit: int = 5):
    """
    Enkelt RAG-søk direkte mot Qdrant.
    """
    return do_rag_search(query, limit)
