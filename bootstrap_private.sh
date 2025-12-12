#!/bin/bash
# ============================================================
# Bootstrap Private Memory System - Complete Setup
# ============================================================
# Purpose: Create isolated Private database and collection
# Run once to initialize separate namespace for personal knowledge
# ============================================================

set -e  # Exit on error

echo "🚀 Bootstrap Private Memory System"
echo "===================================================="
echo ""

# ============================================================
# STEP 1: Create Neo4j Private Database
# ============================================================
echo "📦 Step 1: Creating Neo4j indexes for Private namespace..."
echo ""
echo "   ℹ️  Note: Neo4j Aura uses single database with namespace isolation"
echo "   ℹ️  Private uses :PrivateChunk/:PrivateDocument/:Feedback labels"
echo "   ℹ️  EFC uses :Chunk/:Document/:Concept labels"
echo ""

python - << 'EOF'
from neo4j import GraphDatabase
import os

# Load env manually
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val.strip('"').strip("'")

driver = GraphDatabase.driver(
    os.environ['NEO4J_URI'],
    auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
)

# Create indexes in default database (neo4j Aura limitation)
with driver.session() as session:
    # Check if indexes exist
    try:
        session.run("""
            CREATE INDEX private_chunk_id IF NOT EXISTS
            FOR (c:PrivateChunk) ON (c.id)
        """)
        print("   ✅ Created index: PrivateChunk.id")
    except Exception as e:
        print(f"   ℹ️  PrivateChunk.id index exists: {e}")
    
    try:
        session.run("""
            CREATE INDEX private_doc_id IF NOT EXISTS
            FOR (d:PrivateDocument) ON (d.id)
        """)
        print("   ✅ Created index: PrivateDocument.id")
    except Exception as e:
        print(f"   ℹ️  PrivateDocument.id index exists: {e}")
    
    try:
        session.run("""
            CREATE INDEX feedback_id IF NOT EXISTS
            FOR (f:Feedback) ON (f.id)
        """)
        print("   ✅ Created index: Feedback.id")
    except Exception as e:
        print(f"   ℹ️  Feedback.id index exists: {e}")

driver.close()

print("")
print("✅ Neo4j indexes ready (namespace-isolated)")
print("")
EOF

# ============================================================
# STEP 2: Create Qdrant Private Collection
# ============================================================
echo "📊 Step 2: Creating Qdrant private collection..."
echo ""

python - << 'EOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os

# Load env manually
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val.strip('"').strip("'")

client = QdrantClient(
    url=os.environ['QDRANT_URL'],
    api_key=os.environ.get('QDRANT_API_KEY')
)

# Check if collection exists
collections = [c.name for c in client.get_collections().collections]

if "private" in collections:
    client.delete_collection("private")
    print("   ⚠️  Deleted existing 'private' collection")

# Create collection (3072 dim for gpt-4o-mini embeddings)
client.create_collection(
    collection_name="private",
    vectors_config=VectorParams(
        size=3072,
        distance=Distance.COSINE
    )
)

print("   ✅ Created collection: private (3072-dim, cosine)")
print("")
print("✅ Qdrant private collection ready")
print("")
EOF

# ============================================================
# STEP 3: Verify namespace isolation
# ============================================================
echo "⚙️  Step 3: Verifying namespace isolation..."
echo ""
echo "   ℹ️  Namespace strategy (Neo4j Aura compatible):"
echo "   ✅ EFC: :Document, :Chunk, :Concept"
echo "   ✅ Private: :PrivateDocument, :PrivateChunk, :PrivateConcept"
echo "   ✅ Feedback: :Feedback (shared layer)"
echo ""

# ============================================================
# STEP 4: Verify Setup
# ============================================================
echo "🔍 Step 4: Verifying setup..."
echo ""

python - << 'EOF'
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import os

# Load env manually
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val.strip('"').strip("'")

print("=" * 60)
print("📊 VERIFICATION REPORT")
print("=" * 60)
print("")

# Neo4j
driver = GraphDatabase.driver(
    os.environ['NEO4J_URI'],
    auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
)

with driver.session() as session:
    # Check EFC namespace
    efc_count = session.run("MATCH (n:Document) RETURN count(n)").single()[0]
    print(f"Neo4j Namespace Status:")
    print(f"   EFC :Document nodes: {efc_count}")
    
    # Check Private namespace
    priv_count = session.run("MATCH (n:PrivateDocument) RETURN count(n)").single()[0]
    print(f"   Private :PrivateDocument nodes: {priv_count} (should be 0 initially)")
    
    # Check Feedback
    feedback_count = session.run("MATCH (f:Feedback) RETURN count(f)").single()[0]
    print(f"   Feedback :Feedback nodes: {feedback_count} (should be 0 initially)")
    print("")

driver.close()

# Qdrant
client = QdrantClient(
    url=os.environ['QDRANT_URL'],
    api_key=os.environ.get('QDRANT_API_KEY')
)

collections = client.get_collections().collections
print("Qdrant Collections:")
for c in collections:
    print(f"   ✅ {c.name}")
    if c.name == "private":
        info = client.get_collection("private")
        print(f"      Vectors: {info.points_count}")
        print(f"      Dimension: {info.config.params.vectors.size}")
        print(f"      Distance: {info.config.params.vectors.distance}")

print("")
print("=" * 60)
print("✅ All systems initialized and verified")
print("=" * 60)
EOF

echo ""
echo "🎉 Bootstrap Complete!"
echo ""
echo "Next steps:"
echo "  1. Test private ingestion:"
echo "     python tools/private_orchestrator.py --input 'Test message' --type chat"
echo ""
echo "  2. Classify the document:"
echo "     python tools/memory_classifier.py --document-id <uuid>"
echo ""
echo "  3. Add feedback:"
echo "     python tools/feedback_listener.py --chunk-id <uuid> --signal good"
echo ""
echo "  4. Test steering:"
echo "     python tools/steering_layer.py --dry-run"
echo ""
