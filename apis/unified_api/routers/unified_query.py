# FILE: /Users/morpheus/energyflow-cosmology/apis/unified_api/routers/unified_query.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from apis.unified_api.routers.rag_router import rag_search_internal
from apis.unified_api.routers.neo4j import run_cypher

router = APIRouter(tags=["Unified Query"])

@router.post("/unified_query")
def unified_query(payload: Dict[str, Any]):
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query'")

    rag = rag_search_internal(query=query)

    try:
        neo = run_cypher("RETURN 1 AS ok")
    except Exception:
        neo = {"neo4j": "error"}

    return {
        "query": query,
        "rag": rag,
        "neo4j": neo,
        "semantic": {"enabled": False},
    }

