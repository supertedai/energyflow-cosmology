#!/usr/bin/env python3
"""
Sync Qdrant with Neo4j - Remove orphaned vectors
"""
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

print("🔄 Syncing Qdrant with Neo4j...")
print("=" * 80)
print()

# Connect to both
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Get all chunk IDs from Neo4j
print("📊 Getting chunk IDs from Neo4j...")
with driver.session() as session:
    result = session.run("MATCH (ch:Chunk) RETURN ch.id as id")
    neo4j_chunk_ids = set(record["id"] for record in result)

print(f"   Found {len(neo4j_chunk_ids)} chunks in Neo4j")
print()

# Get all vector IDs from Qdrant
print("📊 Getting vector IDs from Qdrant...")
qdrant_ids = []
offset = None
while True:
    batch, offset = client.scroll(
        collection_name="efc",
        limit=100,
        offset=offset,
        with_payload=False,
        with_vectors=False
    )
    qdrant_ids.extend([str(p.id) for p in batch])
    if offset is None:
        break

print(f"   Found {len(qdrant_ids)} vectors in Qdrant")
print()

# Find orphaned vectors (in Qdrant but not in Neo4j)
orphaned = [vid for vid in qdrant_ids if vid not in neo4j_chunk_ids]

print(f"🗑️  Found {len(orphaned)} orphaned vectors")
print()

if orphaned:
    print(f"Deleting orphaned vectors in batches of 100...")
    
    deleted = 0
    for i in range(0, len(orphaned), 100):
        batch = orphaned[i:i+100]
        client.delete(
            collection_name="efc",
            points_selector=batch
        )
        deleted += len(batch)
        print(f"   Deleted batch {i//100 + 1}: {len(batch)} vectors (total: {deleted}/{len(orphaned)})")
    
    print()
    print(f"✅ Deleted {deleted} orphaned vectors")
else:
    print("✅ No orphaned vectors found")

print()

# Verify sync
final_count = client.get_collection("efc").points_count
print(f"📊 Final Status:")
print(f"   Neo4j chunks:    {len(neo4j_chunk_ids)}")
print(f"   Qdrant vectors:  {final_count}")

if len(neo4j_chunk_ids) == final_count:
    print(f"   ✅ PERFECTLY SYNCED!")
else:
    diff = abs(len(neo4j_chunk_ids) - final_count)
    print(f"   ⚠️  Still {diff} mismatch")

print()
print("=" * 80)

driver.close()
