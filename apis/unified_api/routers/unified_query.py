from fastapi import APIRouter
from datetime import datetime
from apis.unified_api.routers.neo4j import run_cypher
from apis.unified_api.routers.rag import do_rag_search
from apis.unified_api.routers.graph_rag import combined_graph_rag

router = APIRouter()

@router.post("/unified_query")
async def unified_query(payload: dict):
    """
    Kombinerer alle søk:
    - Neo4j direkte-søk
    - RAG/Qdrant
    - Graph-RAG
    """
    query = payload.get("text") or payload.get("query")

    if not query:
        return {"error": "Missing field 'text' or 'query'"}

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "neo4j": {},
        "rag": {},
        "semantic": {}
    }

    # --- Neo4j ---
    try:
        neo4j_res = run_cypher(f"MATCH (n) WHERE n.name CONTAINS '{query}' RETURN n LIMIT 10")
        result["neo4j"] = {"enabled": True, "matches": neo4j_res}
    except Exception as e:
        result["neo4j"] = {"enabled": False, "error": str(e)}

    # --- RAG/Qdrant ---
    try:
        rag_res = do_rag_search(query)
        result["rag"] = {
            "enabled": True,
            "matches": rag_res.get("hits", []),
            "note": rag_res.get("note", None)
        }
    except Exception as e:
        result["rag"] = {"enabled": False, "error": str(e)}

    # --- Graph-RAG ---
    try:
        graph_rag_res = combined_graph_rag(query)
        result["semantic"] = {
            "enabled": True,
            "index_size": graph_rag_res.get("index_size", 0),
            "matches": graph_rag_res.get("matches", [])
        }
    except Exception as e:
        result["semantic"] = {"enabled": False, "error": str(e)}

    return result
