import os
from qdrant_client import QdrantClient

# Env
url = os.environ.get("QDRANT_URL")
api_key = os.environ.get("QDRANT_API_KEY")
collection = os.environ.get("QDRANT_COLLECTION")

client = QdrantClient(url=url, api_key=api_key)

# Midlertidig stub – ingen HF-modeller her
def qdrant_search(text: str, limit: int = 10):
    return {
        "query": text,
        "limit": limit,
        "note": "Embedding disabled in Codespaces – Qdrant reachable, embeddings skipped.",
        "hits": []
    }

