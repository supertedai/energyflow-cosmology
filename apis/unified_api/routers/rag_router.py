# FILE: /Users/morpheus/energyflow-cosmology/apis/unified_api/routers/rag_router.py

from fastapi import APIRouter, Query
import os

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText

router = APIRouter(prefix="/rag", tags=["RAG"])

ENABLE_QDRANT = os.getenv("ENABLE_QDRANT", "1") == "1"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

client = None
if ENABLE_QDRANT:
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

def rag_search_internal(query: str, limit: int = 5):
    if not ENABLE_QDRANT:
        return {"status": "disabled"}

    try:
        hits = client.search_points(
            collection_name=QDRANT_COLLECTION,
            query_filter=Filter(
                must=[FieldCondition(key="text", match=MatchText(text=query))]
            ),
            limit=limit
        )

        return {
            "status": "ok",
            "query": query,
            "count": len(hits),
            "results": [
                {
                    "id": h.id,
                    "score": h.score,
                    "text": (h.payload or {}).get("text"),
                    "source": (h.payload or {}).get("source"),
                }
                for h in hits
            ],
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/search")
def rag_search(query: str = Query(...), limit: int = 5):
    return rag_search_internal(query=query, limit=limit)

