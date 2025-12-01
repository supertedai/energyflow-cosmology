# apis/unified_api/clients/qdrant_client.py

from apis.unified_api.config import ENABLE_QDRANT
from apis.unified_api.clients.embed_client import embed_text


def qdrant_ingest(text: str, source: str):
    vec = embed_text(text)

    if not ENABLE_QDRANT:
        return {
            "status": "qdrant_disabled_stub",
            "operation": "ingest",
            "source": source,
            "received_text_length": len(text),
            "embedding_dim": len(vec),
            "message": "Qdrant ingest er deaktivert lokalt."
        }

    return {
        "status": "qdrant_enabled_but_not_implemented",
        "operation": "ingest",
        "source": source
    }


def qdrant_search(query: str, limit: int = 5):
    if not ENABLE_QDRANT:
        return {
            "status": "qdrant_disabled_stub",
            "operation": "search",
            "query": query,
            "limit": limit,
            "results": [],
            "message": "Qdrant search er deaktivert lokalt."
        }

    return {
        "status": "qdrant_enabled_but_not_implemented",
        "operation": "search"
    }


def qdrant_graph_search(query: str, limit: int = 5):
    if not ENABLE_QDRANT:
        return {
            "status": "qdrant_disabled_stub",
            "operation": "graph_search",
            "query": query,
            "limit": limit,
            "results": [],
            "message": "Graph-RAG er deaktivert lokalt."
        }

    return {
        "status": "qdrant_enabled_but_not_implemented",
        "operation": "graph_search"
    }

