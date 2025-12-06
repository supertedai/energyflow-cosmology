# FILE: apis/unified_api/routers/rag_router.py

from fastapi import APIRouter, Query
import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchText,
)

router = APIRouter(tags=["RAG"])

# ------------------------------
# ENV
# ------------------------------
ENABLE_QDRANT = os.getenv("ENABLE_QDRANT", "0") == "1"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

client = None
if ENABLE_QDRANT:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

# ------------------------------
# INTERNAL SEARCH FUNCTION
# ------------------------------
def rag_search_internal(query: str, limit: int = 5):
    if not ENABLE_QDRANT:
        return {
            "status": "disabled",
            "message": "ENABLE_QDRANT=0 — Qdrant disabled.",
        }

    try:
        # Qdrant-client 1.16.1 uses SCROLL for filter-based search
        points, next_page = client.scroll(
            collection_name=QDRANT_COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="text",
                        match=MatchText(text=query)
                    )
                ]
            ),
            limit=limit
        )

        results = []
        for h in points:
            payload = h.payload or {}
            results.append({
                "id": h.id,
                "score": 1.0,        # scroll has no score, set dummy value
                "text": payload.get("text"),
                "source": payload.get("source"),
            })

        return {
            "status": "ok",
            "query": query,
            "count": len(results),
            "results": results,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# ------------------------------
# FASTAPI ENDPOINT
# ------------------------------
@router.get("/search")
def rag_search(query: str = Query(...), limit: int = 5):
    return rag_search_internal(query=query, limit=limit)

