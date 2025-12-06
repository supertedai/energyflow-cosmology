# apis/unified_api/routers/unified_query.py

from fastapi import APIRouter, HTTPException
from apis.unified_api.routers.rag_router import rag_search
from apis.unified_api.clients.neo4j_client import run_query, driver
from datetime import datetime

router = APIRouter()


@router.post("/unified_query")
def unified_query(payload: dict):

    query = payload.get("query", "").strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' field")

    # -------------------------------------------------------
    # 1. Neo4j
    # -------------------------------------------------------
    neo4j_enabled = driver is not None
    neo4j_result = None
    
    if neo4j_enabled:
        try:
            neo4j_result = run_query(query)
        except Exception as e:
            neo4j_enabled = False
            neo4j_result = {"error": str(e)}

    # -------------------------------------------------------
    # 2. RAG (Qdrant)
    # -------------------------------------------------------
    rag_result = rag_search(query)

    # -------------------------------------------------------
    # 3. Combined response
    # -------------------------------------------------------
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "neo4j": {
            "enabled": neo4j_enabled,
            "result": neo4j_result,
        },
        "rag": rag_result,
        "semantic": {
            "enabled": False
        }
    }

