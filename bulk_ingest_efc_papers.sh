#!/bin/bash
# Bulk ingest all EFC papers from docs/papers/efc/

source .venv/bin/activate

echo "🚀 Starting bulk ingest of all EFC papers..."
echo "================================================"

# Array of all EFC paper directories
papers=(
    "docs/papers/efc/EFC-How-Does-Balance-Shape-Universal-Structures/README.md"
    "docs/papers/efc/AUTH-Layer-Origin-Provenance-and-Structural-Signature-of-Energy-Flow-Cosmology/AUTH-Layer-Origin-Provenance-and-Structural-Signature-of-Energy-Flow-Cosmology.md"
    "docs/papers/efc/EFC-Observational-Evidence-for-Energy-Flow/README.md"
    "docs/papers/efc/EFC-A-Deep-Dive-into-the-Halo-Concept/README.md"
    "docs/papers/efc/EFC-v2.2-Cross-Field-Integration-Summary/README.md"
    "docs/papers/efc/EFC-Mathematical-Framework-for-Energy-Flow-in-Space-Time/README.md"
    "docs/papers/efc/EFC-The-Energy-Flow-Interface/README.md"
    "docs/papers/efc/EFC-Unresolved-Questions-and-Challenges-Entropy/README.md"
    "docs/papers/efc/EFC-How-Energy-Flow-Sustain-Spacetime/README.md"
    "docs/papers/efc/EFC-Observational-Evidence-Entropy-Cosmic-Evolution/README.md"
    "docs/papers/efc/EFC-Field-Equations-for-Entropy-Driven-Spacetime/README.md"
    "docs/papers/efc/EFC-Light-Speed-as-a-Regulator-of-Energy-Flow-in-the-Universe/README.md"
    "docs/papers/efc/EFC-Integrated-Hypothesis-Time-Entropy/README.md"
    "docs/papers/efc/EFC-Introduction-to-Energy-Flow-in-Space-Time/README.md"
    "docs/papers/efc/EFC-Why-is-Light-Speed-a-Cosmic-Limit/README.md"
    "docs/papers/efc/EFC-Introduction-to-Entropy-in-Cosmic-Evolution/README.md"
    "docs/papers/efc/EFC-Is-Consciousness-Linked-to-Entropy/README.md"
    "docs/papers/efc/EFC-Hypothesis-Interrelation-Energy-Entropy/README.md"
    "docs/papers/efc/EFC-Hypothesis-Universe-as-Energy-Driven-System/README.md"
    "docs/papers/efc/EFC-What-Happens-at-the-Universes-Extremes/README.md"
    "docs/papers/efc/EFC-Grid-Higgs-Paradigm-Shift/README.md"
    "docs/papers/efc/EFC-Grid-Model-Entropic-Dynamics/README.md"
    "docs/papers/efc/EFC-AI-Augmented-Scientific-Workflow-Framework/README.md"
    "docs/papers/efc/EFC-Energy-Flow-as-the-Fundamental-Dynamic-of-the-Universe/README.md"
    "docs/papers/efc/EFC-Flow-Entropy-and-Spacetime-Distortion-in-Cosmological-Clusters/README.md"
    "docs/papers/efc/EFC-Can-Entropy-Drive-Cosmic-Evolution/README.md"
    "docs/papers/efc/EFC-What-is-the-Connection-Between-Energy-Flow-and-the-Now/README.md"
    "docs/papers/efc/CEM-Consciousness-Ego-Mirror/README.md"
    "docs/papers/efc/EFC-Technical-Documentation-Energy-Flow-in-Space-Time/README.md"
    "docs/papers/efc/EFC-Applications-and-Implications/README.md"
    "docs/papers/efc/EFC-CMB-Thermodynamic-Gradient/README.md"
    "docs/papers/efc/EFC-v2.1-Modular-Synthesis/README.md"
)

total=${#papers[@]}
count=0

for paper in "${papers[@]}"; do
    count=$((count + 1))
    echo ""
    echo "[$count/$total] Processing: $paper"
    echo "-------------------------------------------"
    
    if [ -f "$paper" ]; then
        python tools/orchestrator_v2.py --input "$paper" --type document
        if [ $? -eq 0 ]; then
            echo "✅ Success: $paper"
        else
            echo "❌ Failed: $paper"
        fi
    else
        echo "⚠️  File not found: $paper"
    fi
done

echo ""
echo "================================================"
echo "✅ Bulk ingest complete! Processed $total papers"
echo ""

# Final status
python -c "
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), 'N-HPl8pKFVwsMgCzydGI26dsgJAMOP1ss6r1NhiHNjs')
)

with driver.session() as session:
    concepts = session.run('MATCH (c:Concept) RETURN count(c) as total').single()['total']
    docs = session.run('MATCH (d:Document) RETURN count(d) as total').single()['total']
    chunks = session.run('MATCH (ch:Chunk) RETURN count(ch) as total').single()['total']
    
    # Count Concept-to-Concept relations
    relations = session.run('''
        MATCH (c1:Concept)-[r]->(c2:Concept)
        RETURN count(r) as total
    ''').single()['total']

client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
vectors = client.get_collection('efc').points_count

print('📊 Final Database Status:')
print(f'   Concepts: {concepts}')
print(f'   Documents: {docs}')
print(f'   Chunks: {chunks}')
print(f'   Concept Relations: {relations}')
print(f'   Vectors (Qdrant): {vectors}')

if relations > 20:
    print(f'\n✅ Ready for GNN training! ({relations} concept relations)')
else:
    print(f'\n⚠️  Need more concept relations for robust GNN training (have {relations}, recommend 50+)')

driver.close()
"
