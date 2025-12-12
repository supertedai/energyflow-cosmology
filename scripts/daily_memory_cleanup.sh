#!/bin/bash
# daily_memory_cleanup.sh - Automated memory aging and cleanup
# Run daily at 3 AM via cron: 0 3 * * * /path/to/daily_memory_cleanup.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/memory_cleanup_$(date +%Y%m%d).log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

# Log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting daily memory cleanup"
log "=========================================="

# Activate virtual environment
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    log "✅ Virtual environment activated"
else
    log "❌ Virtual environment not found"
    exit 1
fi

# Run cleanup script
cd "$PROJECT_ROOT"

python3 << 'PYTHON_SCRIPT' 2>&1 | tee -a "$LOG_FILE"
#!/usr/bin/env python3
"""Daily memory cleanup automation."""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.semantic_mesh_memory import SemanticMeshMemory
from dotenv import load_dotenv

load_dotenv()

print("\n🧹 DAILY MEMORY CLEANUP")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Initialize SMM
smm = SemanticMeshMemory()

# 1. Prune old conversations (180 days)
print("\n1️⃣ Pruning conversations older than 180 days...")
session_counts = smm.prune_old_conversations(days_threshold=180)
if session_counts:
    print(f"   Removed {sum(session_counts.values())} chunks from {len(session_counts)} sessions")
else:
    print("   No old conversations to prune")

# 2. Decay unused facts (30 days)
print("\n2️⃣ Decaying facts unused for 30+ days...")
decay_counts = smm.decay_unused_facts(usage_threshold=30)
print(f"   Decayed: {decay_counts['decayed']}")
print(f"   Pruned:  {decay_counts['pruned']}")
print(f"   Kept:    {decay_counts['kept']}")

# 3. Apply temporal decay to all chunks
print("\n3️⃣ Applying temporal decay...")
smm.apply_temporal_decay()

print("\n" + "=" * 60)
print("✅ Daily cleanup complete!")
print()

PYTHON_SCRIPT

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Cleanup completed successfully"
else
    log "❌ Cleanup failed with exit code $EXIT_CODE"
fi

log "=========================================="
log ""

exit $EXIT_CODE
