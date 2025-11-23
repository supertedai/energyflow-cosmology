#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct
from openai import OpenAI
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "semantic-index.json"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
client_oa = OpenAI(api_key=OPENAI_API_KEY)

COLLECTION = "efc_docs"

def ensure_collection():
    try:
        client_qdrant.get_collection(COLLECTION)
    except:
        client_qdrant.create_collection(
            COLLECTION,
            vectors=VectorParams(size=1536, distance="Cosine")
        )

def embed(text):
    resp = client_oa.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp.data[0].embedding

def main():
    ensure_collection()
    items = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    points = []
    for i, item in enumerate(items):
        vec = embed(item["title"] + " " + (item["description"] or ""))
        points.append(PointStruct(id=i, vector=vec, payload=item))

    client_qdrant.upsert(collection_name=COLLECTION, points=points)

    print(f"[qdrant] Updated {len(items)} embeddings")

if __name__ == "__main__":
    main()
