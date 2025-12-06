# FILE: /opt/symbiose/repo/apis/unified_api/routers/graph_rag.py

from fastapi import APIRouter, Query
from apis.unified_api.clients.graph_rag_client import graph_rag_query

router = APIRouter(tags=["graph-rag"])


def combined_graph_rag(query: str, limit: int = 10, use_gnn: bool = True, alpha: float = 0.7):
    """
    Wrapper-funksjon brukt av unified_query.py.
    Støtter nå GNN-hybrid scoring.
    """
    return graph_rag_query(query, limit, use_gnn=use_gnn, alpha=alpha)


@router.get("/search")
def graph_rag_endpoint(
    query: str = Query(..., description="Søkestreng"),
    limit: int = Query(10, ge=1, le=50),
    use_gnn: bool = Query(True, description="Enable GNN structural boost"),
    alpha: float = Query(0.7, ge=0.0, le=1.0, description="Hybrid weight: alpha*semantic + (1-alpha)*structural")
):
    """
    🧠 Hybrid Graph-RAG med GNN-boost
    
    Kombinerer:
    - Neo4j (strukturelt søk)
    - Qdrant (semantisk søk)
    - GNN embeddings (strukturell likhet)
    
    Route: GET /graph-rag/search?query=...&limit=...&use_gnn=true&alpha=0.7
    
    Parameters:
        - query: Search string
        - limit: Max results (1-50)
        - use_gnn: Enable GNN structural boosting (default: true)
        - alpha: Hybrid scoring weight (0.7 = 70% semantic, 30% structural)
    """
    return combined_graph_rag(query, limit, use_gnn=use_gnn, alpha=alpha)
