#!/usr/bin/env python3
import json, os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct

# OpenAI optional
from openai import OpenAI

# Fallback embedders
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "semantic-index.json"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_q = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

COLLECTION = "efc_docs"

# -----------------------------
# 1. SELECT EMBEDDER (primary + fallback)
# -----------------------------
USE_OPENAI = OPENAI_API_KEY not in (None, "", "null")

if USE_OPENAI:
    print("[embed] Using OpenAI embeddings (text-embedding-3-small)")
    client_oa = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("[embed] OPENAI_API_KEY missing → Using fallback (all-MiniLM-L6-v2)")
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

    # Fallback always works
    return fallback_model.encode(text).tolist()

# -----------------------------
# 2. Ensure collection exists
# -----------------------------
def ensure_collection():
    try:
        client_q.get_collection(COLLECTION)
    except:
        print("[qdrant] Creating collection:", COLLECTION)
        client_q.create_collection(
            COLLECTION,
            vectors=VectorParams(size=1536, distance="Cosine")
        )

# -----------------------------
# 3. MAIN
# -----------------------------
def main():
    ensure_collection()
    items = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    points = []
    for i, item in enumerate(items):
        text = item.get("title", "") + " " + item.get("description", "")
        vec = embed(text)
        points.append(PointStruct(id=i, vector=vec, payload=item))

    client_q.upsert(collection_name=COLLECTION, points=points)

    print(f"[qdrant] Updated {len(items)} embeddings (fallback={not USE_OPENAI})")

if __name__ == "__main__":
    main()
