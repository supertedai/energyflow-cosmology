from .neo4j_client import run_query
from .qdrant_client import qdrant_search

def graph_rag_query(q: str, limit: int = 10):
    """
    1) Søk i Neo4j etter Concept-noder
    2) Returner relevante metadata
    3) Kombiner med Qdrant-søk for semantisk rangering
    """
    cypher = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($q)
       OR toLower(c.description) CONTAINS toLower($q)
    RETURN c.name AS name,
           c.description AS description,
           labels(c) AS labels
    LIMIT $limit
    """

    neo4j_hits = run_query(cypher, params={"q": q, "limit": limit})

    # Qdrant semantisk søk
    qdrant_hits = qdrant_search(q)

    return {
        "query": q,
        "neo4j": neo4j_hits,
        "qdrant": qdrant_hits,
    }
