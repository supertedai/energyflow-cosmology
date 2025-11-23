#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update Qdrant vector store with embeddings for all EFC documents.
Supports:
- OpenAI embeddings (1536 dim)
- Fallback model (768 → padded to 1536)

Stable for GitHub Actions and local use.
"""

import os
import json
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid


# ---------------------------
# Environment
# ---------------------------
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("QDRANT_URL or QDRANT_API_KEY missing in environment.")

# Qdrant client
client_q = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# ---------------------------
# Embedding Setup
# ---------------------------
USE_OPENAI = OPENAI_API_KEY not in (None, "", "null")

if USE_OPENAI:
    print("[embed] Using OpenAI embeddings (text-embedding-3-small)")
    client_oa = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("[embed] OPENAI_API_KEY missing → Using fallback mpnet padded → 1536")
    fallback_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


def embed(text: str):
    """Return 1536-d embedding, always."""
    global USE_OPENAI

    if USE_OPENAI:
        try:
            resp = client_oa.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return resp.data[0].embedding
        except Exception as e:
            print(f"[embed] OpenAI failed → switching to fallback: {e}")
            USE_OPENAI = False

    # --- fallback ---
    vec = fallback_model.encode(text).tolist()  # 768 dim
    padded = vec + vec                           # → 1536 dim
    return padded


# ---------------------------
# Load harvested documents
# ---------------------------
ROOT = Path(__file__).resolve().parents[1]
HARVEST_FILE = ROOT / "semantic-search-index.json"

if not HARVEST_FILE.exists():
    raise SystemExit("semantic-search-index.json missing. Run semantic-harvest first.")

docs = json.loads(HARVEST_FILE.read_text())


# ---------------------------
# Create / ensure collection
# ---------------------------
COLLECTION = "efc_docs"
VECTOR_SIZE = 1536

print(f"[qdrant] Ensuring collection '{COLLECTION}' exists (dim={VECTOR_SIZE})")

client_q.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance="Cosine"),
)


# ---------------------------
# Upsert documents
# ---------------------------
print(f"[qdrant] Upserting {len(docs)} documents…")

points = []

for d in docs:
    text = d.get("text", "")
    identifier = d.get("id") or d.get("slug") or str(uuid.uuid4())

    vec = embed(text)

    if len(vec) != VECTOR_SIZE:
        raise ValueError(f"Embedding dim mismatch: got {len(vec)}, expected {VECTOR_SIZE}")

    points.append(
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "id": identifier,
                "slug": d.get("slug"),
                "text": text,
                "keywords": d.get("keywords", []),
                "title": d.get("title"),
            },
        )
    )

    # batch every 1000
    if len(points) >= 1000:
        client_q.upsert(collection_name=COLLECTION, points=points)
        points = []

# final flush
if points:
    client_q.upsert(collection_name=COLLECTION, points=points)

print("[qdrant] DONE – embeddings updated.")
