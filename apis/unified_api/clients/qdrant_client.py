# apis/unified_api/clients/qdrant_client.py

import os
import uuid
import hashlib
from apis.unified_api.config import ENABLE_QDRANT
from apis.unified_api.clients.embed_client import embed_text
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

_client = None
if ENABLE_QDRANT and QDRANT_URL and QDRANT_API_KEY:
    _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks (300-800 token target ≈ 600 chars).
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > chunk_size * 0.5:  # Don't break too early
                chunk = chunk[:break_point + 1]
        
        chunks.append(chunk.strip())
        start += len(chunk) - overlap
        
    return chunks


def qdrant_ingest(text: str, source: str, metadata: dict = None):
    """
    Ingest text with proper chunking, deduplication, and metadata.
    
    Args:
        text: Clean text to ingest (not full JSON)
        source: Source identifier
        metadata: Additional fields (layer, doi, title, etc.)
    """
    if not ENABLE_QDRANT or not _client:
        return {
            "status": "disabled",
            "message": "Qdrant not enabled or configured"
        }

    try:
        chunks = chunk_text(text)
        points = []
        
        for i, chunk in enumerate(chunks):
            # Deduplication: hash source + text to create deterministic ID
            content_for_hash = f"{source}||{chunk}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()[:32]
            point_id = str(uuid.UUID(content_hash))
            
            # Generate embedding
            vector = embed_text(chunk)
            
            # Build payload with rich metadata
            payload = {
                "text": chunk,
                "source": source,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            
            # Add optional metadata
            if metadata:
                payload.update({
                    "layer": metadata.get("layer"),
                    "doi": metadata.get("doi"),
                    "title": metadata.get("title"),
                    "description": metadata.get("description"),
                    "summary": metadata.get("summary"),
                    "source_type": metadata.get("source_type"),
                    "section": metadata.get("section"),
                    "node_id": metadata.get("node_id"),  # 🔗 BRIDGE to Neo4j/GNN
                })
            
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
        
        # Upsert to Qdrant
        _client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
            wait=True
        )
        
        return {
            "status": "ok",
            "operation": "ingest",
            "source": source,
            "chunks_ingested": len(chunks),
            "total_chars": len(text)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def qdrant_search(query: str, limit: int = 5):
    """
    Use the rag_router's rag_search function for actual search.
    This is a compatibility wrapper.
    """
    from apis.unified_api.routers.rag_router import rag_search
    return rag_search(query, limit)


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

