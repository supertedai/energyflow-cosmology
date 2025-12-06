# apis/unified_api/routers/rag_router.py

from fastapi import APIRouter, Query
import os

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchText
from apis.unified_api.clients.embed_client import embed_text

router = APIRouter(tags=["RAG"])

ENABLE_QDRANT = os.getenv("ENABLE_QDRANT", "1") == "1"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

_client = None

def get_qdrant_client():
    """Lazy initialize Qdrant client after env vars are loaded."""
    global _client
    if _client is None and ENABLE_QDRANT and QDRANT_URL and QDRANT_API_KEY:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return _client


def rag_search(query: str, limit: int = 5, use_vector: bool = True):
    """
    RAG search with real semantic similarity.
    
    Args:
        query: Search query
        limit: Max results
        use_vector: Use vector search (True) or text filter (False)
    """
    client = get_qdrant_client()
    if not ENABLE_QDRANT or not client:
        return {
            "status": "disabled",
            "message": "Qdrant is not enabled or configured"
        }

    try:
        if use_vector:
            # SEMANTIC VECTOR SEARCH - the right way
            query_vector = embed_text(query)
            
            search_result = client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for hit in search_result:
                payload = hit.payload or {}
                
                # Extract clean text (prefer description/summary over raw JSON)
                text = payload.get("description") or payload.get("summary") or payload.get("text", "")
                
                # Truncate if too long (max 500 chars for display)
                if len(text) > 500:
                    text = text[:497] + "..."
                
                results.append({
                    "id": str(hit.id),
                    "score": float(hit.score),  # REAL similarity score!
                    "text": text,
                    "source": payload.get("source", ""),
                    "layer": payload.get("layer"),
                    "doi": payload.get("doi"),
                    "title": payload.get("name") or payload.get("title"),
                    "node_id": payload.get("node_id"),  # 🔗 GNN bridge
                    "payload": payload,  # Full payload for graph-rag
                })
        else:
            # Fallback: text matching (old behavior)
            records, _ = client.scroll(
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
            for record in records:
                payload = record.payload or {}
                text = payload.get("text", "")
                if len(text) > 500:
                    text = text[:497] + "..."
                    
                results.append({
                    "id": str(record.id),
                    "score": 1.0,
                    "text": text,
                    "source": payload.get("source", ""),
                })

        return {
            "status": "ok",
            "query": query,
            "count": len(results),
            "method": "vector_search" if use_vector else "text_filter",
            "results": results,
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/search")
def rag_endpoint(query: str = Query(...), limit: int = 5):
    return rag_search(query, limit)

