#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import os
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Check if node_id exists in any point
points, _ = client.scroll(
    collection_name='efc',
    limit=20,
    with_payload=True,
    with_vectors=False
)

found_with_node_id = 0
found_without_node_id = 0

for p in points:
    payload = p.payload or {}
    if payload.get('node_id'):
        found_with_node_id += 1
        if found_with_node_id == 1:  # Show first example
            print(f"✅ Found node_id: {payload.get('node_id')[:50]}")
            print(f"   source: {payload.get('source')}")
    else:
        found_without_node_id += 1

print(f"\nTotal checked: {len(points)}")
print(f"With node_id: {found_with_node_id}")
print(f"Without node_id: {found_without_node_id}")
