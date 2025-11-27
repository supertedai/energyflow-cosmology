from fastapi import APIRouter
from clients.qdrant_client import qdrant_search

router = APIRouter(prefix="/rag")

@router.get("/search")
def search(query: str):
    return qdrant_search(query)

