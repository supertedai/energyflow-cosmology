#!/usr/bin/env python3
"""
Remove test documents from Qdrant (via scroll, not filter).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")


def main():
    print("🧹 Removing test documents from Qdrant...\n")
    
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("❌ QDRANT_URL/API_KEY not set")
        return
    
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Scroll all points
    offset = None
    test_ids = []
    
    while True:
        points, offset = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        if not points:
            break
        
        for p in points:
            payload = p.payload or {}
            source = payload.get("source", "")
            
            # Check if test document
            if source.startswith(("test/", "Test/", "TEST/")):
                test_ids.append(str(p.id))
                print(f"  Found test doc: {source}")
        
        if offset is None:
            break
    
    # Delete test documents
    if test_ids:
        print(f"\n🗑️  Deleting {len(test_ids)} test documents...")
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=test_ids
        )
        print(f"✅ Deleted {len(test_ids)} test documents")
    else:
        print("✅ No test documents found")


if __name__ == "__main__":
    main()
