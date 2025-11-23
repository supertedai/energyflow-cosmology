#!/usr/bin/env python3
import json, os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct

# Optional OpenAI import
from openai import OpenAI
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "semantic-index.json"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

COLLECTION = "efc_docs"

# -----------------------------
# Embedder selection
# -----------------------------
USE_OPENAI = OPENAI_API_KEY not in (None, "", "null")

if USE_OPENAI:
    print("[embed] Using OpenAI embeddings (text-embedding-3-small)")
    client_oa = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("[embed] OPENAI_API_KEY missing → Using fallback (MiniLM)")
    fallback_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed(text):
    if USE_OPENAI:
        try:
            resp = client_oa.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return resp.data[0].embedding
        except Exception as e:
            print(f"[embed] OpenAI failed → fallback: {e}")

    return fallback_model.encode(text).tolist()

# -----------------------------
# Qdrant setup
# -----------------------------
client_q = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def ensure_collection():
    try:
        client_q.get_collection(COLLECTION)
        print(f"[qdrant] Collection exists: {COLLECTION}")
    except:
        print(f"[qdrant] Creating collection: {COLLECTION}")
        client_q.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=1536,
                distance="Cosine"
            )
        )

# -----------------------------
# MAIN
# -----------------------------
def main():
    ensure_collection()
    items = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    points = []
    for i, item in enumerate(items):
        text = item.get("title", "") + " " + item.get("description", "")
        vec = embed(text)
        points.append(PointStruct(id=i, vector=vec, payload=item))

    client_q.upsert(
        collection_name=COLLECTION, 
        points=points
    )

    print(f"[qdrant] Updated {len(items)} embeddings.")

if __name__ == "__main__":
    main()
