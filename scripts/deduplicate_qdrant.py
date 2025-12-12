#!/usr/bin/env python3
"""
Deduplicate Qdrant collection by content hash.

Removes duplicate chunks with identical source+text but different IDs.
Keeps the first occurrence, deletes duplicates.
"""

import hashlib
import os
from collections import defaultdict
from typing import Dict, List

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Load environment
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "efc"


def hash_content(source: str, text: str) -> str:
    """Create deterministic hash from source + text."""
    content = f"{source}||{text}"
    return hashlib.sha256(content.encode()).hexdigest()


def deduplicate_collection():
    """Find and remove duplicate chunks."""
    
    print("🔗 Connecting to Qdrant Cloud...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    print(f"📊 Scanning collection '{COLLECTION_NAME}'...")
    
    # Scroll through all points
    points = []
    offset = None
    
    while True:
        batch, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        points.extend(batch)
        
        if offset is None:
            break
    
    print(f"✅ Found {len(points)} total points")
    
    # Group by content hash
    hash_to_points: Dict[str, List] = defaultdict(list)
    
    for point in points:
        payload = point.payload or {}
        source = payload.get("source", "")
        text = payload.get("text", "")
        
        content_hash = hash_content(source, text)
        hash_to_points[content_hash].append(point)
    
    # Find duplicates
    duplicates_to_delete = []
    unique_count = 0
    
    for content_hash, point_list in hash_to_points.items():
        if len(point_list) > 1:
            # Keep the one WITH node_id (newest), delete rest
            # Find point with node_id
            keep_point = None
            for p in point_list:
                if p.payload and p.payload.get("node_id"):
                    keep_point = p
                    break
            
            # If no node_id found, keep first as fallback
            if keep_point is None:
                keep_point = point_list[0]
            
            keep_id = keep_point.id
            delete_ids = [p.id for p in point_list if p.id != keep_id]
            duplicates_to_delete.extend(delete_ids)
            
            print(f"🔍 Hash {content_hash[:8]}... has {len(point_list)} duplicates")
            print(f"   Keeping: {keep_id} (has node_id: {bool(keep_point.payload.get('node_id'))})")
            print(f"   Deleting: {delete_ids}")
        else:
            unique_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Unique chunks: {unique_count}")
    print(f"   Duplicate chunks to delete: {len(duplicates_to_delete)}")
    
    if duplicates_to_delete:
        print(f"\n🗑️  Deleting {len(duplicates_to_delete)} duplicates...")
        
        # Delete in batches of 100
        for i in range(0, len(duplicates_to_delete), 100):
            batch = duplicates_to_delete[i:i+100]
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=batch
            )
            print(f"   Deleted batch {i//100 + 1}: {len(batch)} points")
        
        print("✅ Deduplication complete!")
        
        # Verify
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"\n📊 Final collection size: {collection_info.points_count} points")
    else:
        print("✅ No duplicates found - collection is clean!")


if __name__ == "__main__":
    deduplicate_collection()
