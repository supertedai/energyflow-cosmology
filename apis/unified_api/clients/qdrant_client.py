# qdrant_client.py
#
# Komplett stub for lokal utvikling (lag-1a).
# Ingen kontakt med Qdrant – alt returnerer dummy-data.

def qdrant_ingest(text: str) -> dict:
    """Stub for ingest."""
    return {
        "status": "qdrant_disabled_stub",
        "operation": "ingest",
        "received_text_length": len(text),
        "message": "Qdrant ingest er deaktivert lokalt."
    }


def qdrant_search(query: str, limit: int = 5) -> dict:
    """Stub for RAG-søk."""
    return {
        "status": "qdrant_disabled_stub",
        "operation": "search",
        "query": query,
        "limit": limit,
        "results": [],
        "message": "Qdrant search er deaktivert lokalt."
    }


def qdrant_graph_search(query: str, limit: int = 5) -> dict:
    """Stub for graph-RAG-søk."""
    return {
        "status": "qdrant_disabled_stub",
        "operation": "graph_search",
        "query": query,
        "limit": limit,
        "results": [],
        "message": "Graph-RAG er deaktivert lokalt."
    }

