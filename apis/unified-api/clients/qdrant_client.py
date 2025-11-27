import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

qdrant = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"]        # <-- RIKTIG HEADER
)

model = SentenceTransformer("all-MiniLM-L6-v2")

def qdrant_ingest(text: str):
    emb = model.encode(text).tolist()
    qdrant.upsert(
        collection_name="efc_rag",
        points=[{"id": None, "vector": emb, "payload": {"text": text}}]
    )
    return {"status": "ok", "text": text}

def qdrant_search(query: str):
    emb = model.encode(query).tolist()
    return qdrant.search(
        collection_name="efc_rag",
        query_vector=emb,
        limit=5
    )

