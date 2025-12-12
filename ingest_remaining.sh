#!/bin/bash
# Resume Gold Standard Ingest (Skip Duplicates)
# Generated: 2025-12-10
# This script ingests ONLY files that haven't been successfully processed yet

set -e  # Exit on error

echo "🔄 Resuming Gold Standard Ingest (skipping duplicates)..."
echo "=================================================="

# Get list of successfully processed files
PROCESSED=$(grep "✅ Success:" gold_ingest.log 2>/dev/null | sed 's/✅ Success: //' || echo "")
PROCESSED_ARRAY=()
while IFS= read -r line; do
    [[ -n "$line" ]] && PROCESSED_ARRAY+=("$line")
done <<< "$PROCESSED"

echo "📊 Status:"
echo "   Already processed: ${#PROCESSED_ARRAY[@]} files"

# Function to check if file was processed
is_processed() {
    local file="$1"
    for processed in "${PROCESSED_ARRAY[@]}"; do
        if [[ "$processed" == "$file" ]]; then
            return 0
        fi
    done
    return 1
}

SUCCESS=0
ERRORS=0
SKIPPED=0
TOTAL=587

# Source files from generated script
source .venv/bin/activate

# Read all files from ingest_gold_standard.sh
FILES=()
while IFS= read -r line; do
    if [[ "$line" =~ \"([^\"]+)\"\ --type ]]; then
        FILES+=("${BASH_REMATCH[1]}")
    fi
done < ingest_gold_standard.sh

echo "   Total files: ${#FILES[@]}"
echo "   To process: $((${#FILES[@]} - ${#PROCESSED_ARRAY[@]}))"
echo ""

# Process each file
for i in "${!FILES[@]}"; do
    FILE="${FILES[$i]}"
    NUM=$((i + 1))
    
    echo "[$NUM/$TOTAL] Checking: $FILE"
    
    # Check if already processed
    if is_processed "$FILE"; then
        echo "⏭️  Skipped (already done): $FILE"
        ((SKIPPED++))
        continue
    fi
    
    echo "-------------------------------------------"
    
    # Process file
    if python tools/orchestrator_v2.py --input "$FILE" --type document 2>&1; then
        echo "✅ Success: $FILE"
        ((SUCCESS++))
    else
        echo "❌ Error: $FILE"
        ((ERRORS++))
    fi
    
    echo ""
done

echo ""
echo "=================================================="
echo "✅ Ingest complete! Final stats:"
echo "   Previously done: ${#PROCESSED_ARRAY[@]}"
echo "   Newly added:     $SUCCESS"
echo "   Skipped:         $SKIPPED"
echo "   Errors:          $ERRORS"
echo ""
echo "📊 Database status:"
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

client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
vectors = client.get_collection('efc').points_count

print(f'   Concepts:  {concepts}')
print(f'   Documents: {docs}')
print(f'   Chunks:    {chunks}')
print(f'   Vectors:   {vectors}')

driver.close()
"
