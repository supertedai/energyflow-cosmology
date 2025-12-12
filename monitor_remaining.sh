#!/bin/bash
# Monitor Remaining Ingest Progress

LOG_FILE="remaining_ingest.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

# ANSI colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear

echo "📊 Remaining Ingest Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    # Count stats
    ALREADY_DONE=$(head -20 "$LOG_FILE" | grep "Already processed:" | sed 's/.*: //' | sed 's/ files//')
    NEW_SUCCESS=$(grep -c "✅ Success:" "$LOG_FILE" 2>/dev/null || echo 0)
    SKIPPED=$(grep -c "⏭️  Skipped" "$LOG_FILE" 2>/dev/null || echo 0)
    ERRORS=$(grep -c "❌ Error:" "$LOG_FILE" 2>/dev/null || echo 0)
    
    TOTAL=587
    PROCESSED=$((SKIPPED + NEW_SUCCESS))
    REMAINING=$((TOTAL - PROCESSED))
    
    # Calculate percentage
    if [ $TOTAL -gt 0 ]; then
        PERCENT=$((PROCESSED * 100 / TOTAL))
    else
        PERCENT=0
    fi
    
    # Progress bar
    BAR_WIDTH=50
    FILLED=$((PERCENT * BAR_WIDTH / 100))
    EMPTY=$((BAR_WIDTH - FILLED))
    
    # Build bar
    BAR=""
    for ((i=0; i<FILLED; i++)); do BAR="${BAR}█"; done
    for ((i=0; i<EMPTY; i++)); do BAR="${BAR}░"; done
    
    # Get current file
    CURRENT=$(tail -5 "$LOG_FILE" | grep "Checking:" | tail -1 | sed 's/.*Checking: //' || echo "Starting...")
    
    # Clear and display
    tput cup 3 0
    echo "┌────────────────────────────────────────────────────────────────┐"
    echo "│ Progress:  ${PERCENT}% [${BAR}]   │"
    echo "├────────────────────────────────────────────────────────────────┤"
    echo "│ 📦 Already done: ${ALREADY_DONE:-0} files                                    │"
    echo "│ ✅ New success:  ${NEW_SUCCESS} files                                     │"
    echo "│ ⏭️  Skipped:      ${SKIPPED} files                                    │"
    echo "│ ❌ Errors:       ${ERRORS} files                                     │"
    echo "│ ⏳ Remaining:    ${REMAINING} files                                    │"
    
    # Check if complete
    if [ "$REMAINING" -eq 0 ] || grep -q "Ingest complete!" "$LOG_FILE" 2>/dev/null; then
        echo "├────────────────────────────────────────────────────────────────┤"
        echo "│ 🎉 COMPLETE!                                                 │"
    fi
    
    echo "├────────────────────────────────────────────────────────────────┤"
    printf "│ 📄 Current: %-52s │\n" "${CURRENT:0:52}"
    echo "└────────────────────────────────────────────────────────────────┘"
    echo ""
    echo "Press Ctrl+C to exit this monitor"
    echo "(Ingest process will continue in background)"
    
    # Check if complete
    if [ "$REMAINING" -eq 0 ] || grep -q "Ingest complete!" "$LOG_FILE" 2>/dev/null; then
        break
    fi
    
    sleep 5
done
