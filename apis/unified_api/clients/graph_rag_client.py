from .neo4j_client import run_query
from .qdrant_client import qdrant_search
from .gnn_client import (
    get_node_embedding,
    compute_structural_similarity,
    find_k_nearest_neighbors,
    hybrid_score
)

def graph_rag_query(q: str, limit: int = 10, use_gnn: bool = True, alpha: float = 0.7):
    """
    Hybrid Graph-RAG med GNN-boost:
    
    1) Søk i Neo4j etter Concept-noder (strukturelt)
    2) Søk i Qdrant for semantisk matching
    3) Kombiner med GNN-embeddings for strukturell likhet
    4) Hybrid scoring: alpha * semantic + (1-alpha) * structural
    
    Args:
        q: Query string
        limit: Max results
        use_gnn: Enable GNN structural boosting (default: True)
        alpha: Hybrid weight (0.7 = 70% semantic, 30% structural)
    """

    # 1. Neo4j strukturelt søk
    cypher = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($q)
       OR toLower(c.description) CONTAINS toLower($q)
    RETURN id(c) AS node_id,
           c.name AS name,
           c.description AS description,
           labels(c) AS labels
    LIMIT $limit
    """

    neo4j_hits = run_query(
        cypher,
        params={"q": q, "limit": limit}
    )

    # 2. Qdrant semantisk søk
    qdrant_response = qdrant_search(q, limit=limit)
    qdrant_hits = qdrant_response.get("results", [])

    # 3. GNN-boost: Strukturell likhet
    if use_gnn:
        # Extract node IDs from Neo4j hits (if any)
        neo4j_node_ids = [str(hit.get("node_id")) for hit in neo4j_hits if hit.get("node_id")] if neo4j_hits else []
        
        # Enrich Qdrant hits with GNN structural signals
        for hit in qdrant_hits:
            semantic_score = hit.get("score", 0.0)
            
            # Try to extract node_id from payload if available
            payload = hit.get("payload", {})
            node_id = payload.get("node_id")
            
            if node_id and neo4j_node_ids:
                # Compute structural similarity to Neo4j hits
                structural_score = compute_structural_similarity(
                    node_id=str(node_id),
                    reference_ids=neo4j_node_ids
                )
                
                # Compute hybrid score
                hit["structural_score"] = structural_score
                hit["hybrid_score"] = hybrid_score(semantic_score, structural_score, alpha)
                hit["gnn_neighbors"] = find_k_nearest_neighbors(str(node_id), k=3)
            else:
                # No node_id or no Neo4j reference → pure semantic
                hit["structural_score"] = None
                hit["hybrid_score"] = semantic_score
                hit["gnn_status"] = "no_node_id_mapping"
        
        # Re-rank by hybrid score
        qdrant_hits.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)

    return {
        "query": q,
        "neo4j": neo4j_hits,
        "qdrant": {
            "results": qdrant_hits,
            "gnn_enabled": use_gnn,
            "hybrid_alpha": alpha if use_gnn else None
        },
    }

