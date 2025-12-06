# FILE: apis/unified_api/routers/unified_query.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Korrekt import – rag_search finnes, do_rag_search finnes ikke
from apis.unified_api.routers.rag_router import rag_search

router = APIRouter(tags=["Unified Query"])

@router.post("/unified_query")
def unified_query(payload: Dict[str, Any]):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' field")

    # Call RAG search directly
    rag_result = rag_search(query=query)

    return {
        "timestamp": "N/A",
        "query": query,
        "neo4j": {"enabled": False},
        "rag": rag_result,
        "semantic": {"enabled": False},
    }

