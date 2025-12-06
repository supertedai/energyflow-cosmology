#!/usr/bin/env python3
"""Debug: Verifiser at node_id faktisk lagres"""
from dotenv import load_dotenv
load_dotenv()

import os
import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Simple test
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Create test point with node_id
test_point = PointStruct(
    id=uuid.uuid4().hex,
    vector=[0.1] * 3072,  # Dummy vector
    payload={
        "text": "DEBUG TEST",
        "source": "debug/test.md",
        "node_id": "4:DEBUG:12345"  # Test node_id
    }
)

test_id = test_point.id
print(f"📝 Upserting test point with node_id (ID: {test_id})...")
result = client.upsert(
    collection_name='efc',
    points=[test_point],
    wait=True
)
print(f"   Upsert result: {result}")

# Verify by direct retrieve
print("🔍 Retrieving test point by ID...")
retrieved = client.retrieve(
    collection_name='efc',
    ids=[test_id],
    with_payload=True,
    with_vectors=False
)

if retrieved:
    p = retrieved[0]
    payload = p.payload or {}
    print(f"\n✅ Found test point!")
    print(f"   node_id: {payload.get('node_id')}")
    print(f"   source: {payload.get('source')}")
    print(f"   Full payload keys: {list(payload.keys())}")
    
    # Cleanup
    client.delete(collection_name='efc', points_selector=[test_id])
    print(f"\n🗑️  Cleaned up test point")
else:
    print("\n❌ Test point not found!")
