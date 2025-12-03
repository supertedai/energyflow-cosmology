#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update Qdrant vector store with embeddings.
Handles multiple input formats:
- JSON list of objects
- JSON list of strings
- Mixed list (strings + objects)
"""

import os
import json
import uuid
from pathlib import Path

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


# ----------------------------------------
# Environment
# ----------------------------------------
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not QDRANT_URL or not QDRANT_API_KEY:
    raise SystemExit("QDRANT_URL or QDRANT_API_KEY missing in GitHub secrets.")

client_q = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# ----------------------------------------
# Embedding setup
# ----------------------------------------
USE_OPENAI = OPENAI_API_KEY not in (None, "", "null")

if USE_OPENAI:
    print("[embed] Using OpenAI embeddings (text-embedding-3-small)")
    client_oa = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("[embed] Using fallback mpnet (768 → padded → 1536)")
    fallback_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")


def embed(text: str):
    """Always return 1536-d embedding."""
    global USE_OPENAI

    if USE_OPENAI:
        try:
            out = client_oa.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return out.data[0].embedding
        except Exception as e:
            print(f"[embed] OpenAI failed → fallback activated: {e}")
            USE_OPENAI = False

    # fallback → 768 → pad to 1536
    vec = fallback_model.encode(text).tolist()
    return vec + vec


# ----------------------------------------
# Load semantic index
# ----------------------------------------
ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "semantic-search-index.json"

if not HARVEST.exists():
    raise SystemExit("semantic-search-index.json missing")

raw_data = json.loads(HARVEST.read_text())

docs = []

for item in raw_data:
    if isinstance(item, dict):
        # full node
        docs.append({
            "text": item.get("text", ""),
            "slug": item.get("slug") or item.get("id") or str(uuid.uuid4()),
            "title": item.get("title", None),
            "keywords": item.get("keywords", []),
        })
    elif isinstance(item, str):
        # bare text → wrap it
        docs.append({
            "text": item,
            "slug": str(uuid.uuid4()),
            "title": None,
            "keywords": [],
        })
    else:
        # ignore corrupt items
        continue

print(f"[data] Loaded {len(docs)} normalized documents")


# ----------------------------------------
# Prepare Qdrant collection
# ----------------------------------------
COLLECTION = "efc"
VECTOR_SIZE = 1536

if client_q.collection_exists(COLLECTION):
    print(f"[qdrant] Deleting old collection: {COLLECTION}")
    client_q.delete_collection(COLLECTION)

print(f"[qdrant] Creating collection '{COLLECTION}' with dim={VECTOR_SIZE}")
client_q.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance="Cosine"),
)


# ----------------------------------------
# Upsert embeddings
# ----------------------------------------
print(f"[qdrant] Upserting {len(docs)} documents…")

batch = []

for d in docs:
    vec = embed(d["text"])
    if len(vec) != VECTOR_SIZE:
        raise ValueError(f"Wrong embedding dim: {len(vec)} != {VECTOR_SIZE}")

    batch.append(
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload=d,
        )
    )

    # batch flush
    if len(batch) >= 500:
        client_q.upsert(COLLECTION, batch)
        batch = []

# final flush
if batch:
    client_q.upsert(COLLECTION, batch)

print("[qdrant] DONE – vector store updated.")
