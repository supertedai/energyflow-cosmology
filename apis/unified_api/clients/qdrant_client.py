# clients/qdrant_client.py
#
# Midlertidig "stub" for Qdrant-kall.
# Denne gjør INGENTING avansert – den returnerer bare tomme treff,
# slik at API-et kan starte og Neo4j kan testes først.

from typing import Any, Dict, List


def qdrant_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Midlertidig Qdrant-stub.

    Returnerer en tom liste med "hits" slik at resten av API-et
    (Neo4j, routers, health) kan testes uten at vi trenger
    HuggingFace, embeddings eller faktisk Qdrant-tilkobling ennå.
    """
    return {
        "query": query,
        "limit": limit,
        "hits": [],
        "note": "Qdrant is disabled in this stage – this is a stub response.",
    }

