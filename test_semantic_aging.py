#!/usr/bin/env python3
"""
Test semantic mesh aging functionality.

Tests:
1. Prune old conversations (>180 days)
2. Decay unused facts (>30 days without access)
3. Apply temporal decay to all chunks
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.semantic_mesh_memory import SemanticMeshMemory
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

# Initialize
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

print("🧪 Testing Semantic Mesh Aging")
print("=" * 60)

# Get initial state
try:
    collection_info = qdrant_client.get_collection("semantic_mesh")
    initial_count = collection_info.points_count
    print(f"\n📊 Initial state: {initial_count} chunks in semantic_mesh")
except Exception as e:
    print(f"⚠️  Collection doesn't exist yet: {e}")
    initial_count = 0

# Initialize SMM
smm = SemanticMeshMemory()

# Test 1: Create test data with varying ages
print("\n1️⃣ Creating test data with varying timestamps...")

# Recent conversation (should be kept)
recent_chunk = smm.store_chunk(
    text="Recent conversation about EFC theory",
    domains=["cosmology"],
    tags=["EFC", "recent"],
    session_id="recent_session",
    conversation_turn=1
)
print(f"   ✅ Created recent chunk: {recent_chunk.id[:8]}")

# Old conversation (should be pruned at 180 days)
old_timestamp = (datetime.now() - timedelta(days=200)).isoformat()
qdrant_client.set_payload(
    collection_name="semantic_mesh",
    payload={"timestamp": old_timestamp, "last_accessed": old_timestamp},
    points=[recent_chunk.id]  # Temporarily modify this one
)

# Create actual old chunk
old_chunk = smm.store_chunk(
    text="Old conversation from 200 days ago",
    domains=["legacy"],
    tags=["old"],
    session_id="old_session",
    conversation_turn=1
)
qdrant_client.set_payload(
    collection_name="semantic_mesh",
    payload={"timestamp": old_timestamp, "last_accessed": old_timestamp},
    points=[old_chunk.id]
)
print(f"   ✅ Created old chunk: {old_chunk.id[:8]} (timestamp: {old_timestamp[:10]})")

# Unused chunk (should be decayed at 30 days)
unused_timestamp = (datetime.now() - timedelta(days=40)).isoformat()
unused_chunk = smm.store_chunk(
    text="Unused fact from 40 days ago",
    domains=["unused"],
    tags=["stale"],
    session_id="unused_session",
    conversation_turn=1
)
qdrant_client.set_payload(
    collection_name="semantic_mesh",
    payload={"timestamp": unused_timestamp, "last_accessed": unused_timestamp},
    points=[unused_chunk.id]
)
print(f"   ✅ Created unused chunk: {unused_chunk.id[:8]} (timestamp: {unused_timestamp[:10]})")

# Get count after setup
collection_info = qdrant_client.get_collection("semantic_mesh")
after_setup = collection_info.points_count
print(f"\n📊 After setup: {after_setup} chunks")

# Test 2: Prune old conversations
print("\n2️⃣ Testing prune_old_conversations(days_threshold=180)...")
session_counts = smm.prune_old_conversations(days_threshold=180)
print(f"   Pruned sessions: {dict(session_counts)}")

collection_info = qdrant_client.get_collection("semantic_mesh")
after_prune = collection_info.points_count
print(f"   Before: {after_setup}, After: {after_prune}, Removed: {after_setup - after_prune}")

# Test 3: Decay unused facts
print("\n3️⃣ Testing decay_unused_facts(usage_threshold=30)...")
decay_counts = smm.decay_unused_facts(usage_threshold=30)
print(f"   Decayed: {decay_counts['decayed']}")
print(f"   Pruned:  {decay_counts['pruned']}")
print(f"   Kept:    {decay_counts['kept']}")

collection_info = qdrant_client.get_collection("semantic_mesh")
after_decay = collection_info.points_count
print(f"   Before: {after_prune}, After: {after_decay}, Removed: {after_prune - after_decay}")

# Test 4: Apply temporal decay
print("\n4️⃣ Testing apply_temporal_decay()...")
smm.apply_temporal_decay()

collection_info = qdrant_client.get_collection("semantic_mesh")
final_count = collection_info.points_count
print(f"   Before: {after_decay}, After: {final_count}")

# Summary
print("\n" + "=" * 60)
print("📊 AGING TEST SUMMARY:")
print(f"   Initial:      {initial_count} chunks")
print(f"   After setup:  {after_setup} chunks")
print(f"   After prune:  {after_prune} chunks (-{after_setup - after_prune})")
print(f"   After decay:  {after_decay} chunks (-{after_prune - after_decay})")
print(f"   Final:        {final_count} chunks")
print()

# Validation
if after_prune < after_setup:
    print("✅ Old conversation pruning works")
else:
    print("⚠️  No old conversations were pruned")

if decay_counts["decayed"] > 0 or decay_counts["pruned"] > 0:
    print("✅ Unused fact decay works")
else:
    print("⚠️  No unused facts were decayed")

print()
print("✅ Semantic mesh aging tests complete!")
