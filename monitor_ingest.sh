#!/bin/bash
#
# Live Progress Monitor for Gold Standard Ingest
#

clear

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 GOLD STANDARD INGEST - LIVE MONITOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while true; do
    # Get counts
    total=587
    success=$(grep -c "✅ Success:" gold_ingest.log 2>/dev/null || echo "0")
    errors=$(grep -c "❌ Error:" gold_ingest.log 2>/dev/null || echo "0")
    
    # Ensure numeric values
    success=${success:-0}
    errors=${errors:-0}
    
    # Calculate progress (avoid division by zero)
    if [ $total -gt 0 ]; then
        progress=$((success * 100 / total))
    else
        progress=0
    fi
    remaining=$((total - success - errors))
    
    # Estimate time remaining (assuming 20 sec per file)
    seconds_remaining=$((remaining * 20))
    hours=$((seconds_remaining / 3600))
    minutes=$(((seconds_remaining % 3600) / 60))
    
    # Get current file
    current=$(tail -20 gold_ingest.log 2>/dev/null | grep "Processing:" | tail -1 | sed 's/.*Processing: //')
    
    # Clear previous output (move cursor up)
    tput cuu 12 2>/dev/null || true
    
    echo "┌────────────────────────────────────────────────────────────────┐"
    printf "│ Progress: %3d%% [" "$progress"
    
    # Progress bar (50 chars)
    filled=$((progress / 2))
    for i in $(seq 1 50); do
        if [ $i -le $filled ]; then
            printf "█"
        else
            printf "░"
        fi
    done
    printf "]   │\n"
    
    echo "├────────────────────────────────────────────────────────────────┤"
    printf "│ ✅ Success:   %4d / %4d                                     │\n" "$success" "$total"
    printf "│ ❌ Errors:    %4d                                           │\n" "$errors"
    printf "│ ⏳ Remaining: %4d files                                     │\n" "$remaining"
    echo "├────────────────────────────────────────────────────────────────┤"
    
    if [ $remaining -gt 0 ]; then
        printf "│ 🕐 Est. time: %2dh %02dm                                      │\n" "$hours" "$minutes"
    else
        printf "│ 🎉 COMPLETE!                                                 │\n"
    fi
    
    echo "├────────────────────────────────────────────────────────────────┤"
    
    # Current file (truncate if too long)
    if [ -n "$current" ]; then
        current_short=$(echo "$current" | cut -c1-55)
        printf "│ 📄 Current: %-55s│\n" "$current_short"
    else
        printf "│ 📄 Current: Waiting...                                       │\n"
    fi
    
    echo "└────────────────────────────────────────────────────────────────┘"
    echo ""
    
    # Exit if done
    if [ $remaining -eq 0 ] && [ $success -gt 0 ]; then
        echo ""
        echo "✅ Ingest complete! Final stats:"
        echo "   Success: $success"
        echo "   Errors:  $errors"
        echo ""
        
        # Show database stats
        echo "📊 Database status:"
        source .venv/bin/activate 2>/dev/null
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
" 2>/dev/null || echo "   (Database stats unavailable)"
        
        break
    fi
    
    # Update every 5 seconds
    sleep 5
done

echo ""
echo "Press Ctrl+C to exit this monitor"
echo "(Ingest process will continue in background)"
