from fastapi import APIRouter
from apis.unified_api.clients.qdrant_client import qdrant_search

# Ingen prefix her – prefix settes i main.py
router = APIRouter()

@router.get("/search")
def search(query: str):
    """
    Enkelt RAG-søk direkte mot Qdrant.
    """
    return qdrant_search(query)

