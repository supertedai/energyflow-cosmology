#!/bin/bash
# Monitor Semantic Augmentation Progress

LOG_FILE="semantic_augmentation.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "⏳ Waiting for log file..."
    sleep 5
fi

clear

echo "📊 Semantic Augmentation Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    # Extract progress
    PROCESSED=$(grep -c "Analyzing:" "$LOG_FILE" 2>/dev/null || echo 0)
    AUGMENTED=$(grep -c "✅ Type:" "$LOG_FILE" 2>/dev/null || echo 0)
    ERRORS=$(grep -c "⚠️  Analysis failed:" "$LOG_FILE" 2>/dev/null || echo 0)
    
    # Get total from initial log line
    TOTAL=$(grep "Found.*concepts with PRIMARY chunks" "$LOG_FILE" 2>/dev/null | sed 's/.*Found //' | sed 's/ concepts.*//' || echo "958")
    
    # Calculate percentage
    if [ "$TOTAL" -gt 0 ]; then
        PERCENT=$((PROCESSED * 100 / TOTAL))
    else
        PERCENT=0
    fi
    
    # Progress bar
    BAR_WIDTH=50
    FILLED=$((PERCENT * BAR_WIDTH / 100))
    EMPTY=$((BAR_WIDTH - FILLED))
    
    BAR=""
    for ((i=0; i<FILLED; i++)); do BAR="${BAR}█"; done
    for ((i=0; i<EMPTY; i++)); do BAR="${BAR}░"; done
    
    # Current concept
    CURRENT=$(tail -20 "$LOG_FILE" | grep "Analyzing:" | tail -1 | sed 's/.*Analyzing: //' || echo "Starting...")
    
    # Get recent stats
    RECENT_TYPE=$(tail -20 "$LOG_FILE" | grep "Type:" | tail -1 | sed 's/.*Type: //' || echo "N/A")
    RECENT_DOMAIN=$(tail -20 "$LOG_FILE" | grep "Domain:" | tail -1 | sed 's/.*Domain: //' || echo "N/A")
    RECENT_RELS=$(tail -20 "$LOG_FILE" | grep "Relations:" | tail -1 | sed 's/.*Relations: //' || echo "0")
    
    # Display
    tput cup 3 0
    echo "┌────────────────────────────────────────────────────────────────┐"
    echo "│ Progress:  ${PERCENT}% [${BAR}]   │"
    echo "├────────────────────────────────────────────────────────────────┤"
    echo "│ 📊 Stats:                                                     │"
    echo "│    Processed:  ${PROCESSED} / ${TOTAL}                                      │"
    echo "│    Augmented:  ${AUGMENTED}                                              │"
    echo "│    Errors:     ${ERRORS}                                                │"
    echo "├────────────────────────────────────────────────────────────────┤"
    echo "│ 🧠 Current Concept:                                           │"
    printf "│    %-58s │\n" "${CURRENT:0:58}"
    echo "│                                                                │"
    echo "│ 📋 Last Analysis:                                             │"
    echo "│    Type:      ${RECENT_TYPE}                                 │"
    echo "│    Domain:    ${RECENT_DOMAIN}                               │"
    echo "│    Relations: ${RECENT_RELS}                                 │"
    
    # Check if complete
    if grep -q "AUGMENTATION COMPLETE" "$LOG_FILE" 2>/dev/null; then
        echo "├────────────────────────────────────────────────────────────────┤"
        echo "│ 🎉 COMPLETE!                                                 │"
        
        # Get final stats
        FINAL_PROCESSED=$(grep "Processed:" "$LOG_FILE" | tail -1 | sed 's/.*: //')
        FINAL_AUGMENTED=$(grep "Augmented:" "$LOG_FILE" | tail -1 | sed 's/.*: //')
        FINAL_ERRORS=$(grep "Errors:" "$LOG_FILE" | tail -1 | sed 's/.*: //')
        
        echo "│                                                                │"
        echo "│ Final Stats:                                                   │"
        echo "│    Processed:  ${FINAL_PROCESSED}                                      │"
        echo "│    Augmented:  ${FINAL_AUGMENTED}                                      │"
        echo "│    Errors:     ${FINAL_ERRORS}                                        │"
    fi
    
    echo "└────────────────────────────────────────────────────────────────┘"
    echo ""
    echo "Press Ctrl+C to exit this monitor"
    echo "(Augmentation process will continue in background)"
    
    # Break if complete
    if grep -q "AUGMENTATION COMPLETE" "$LOG_FILE" 2>/dev/null; then
        break
    fi
    
    sleep 5
done
