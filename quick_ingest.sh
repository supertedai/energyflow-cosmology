#!/bin/bash
#
# Quick Ingest - Smart batch ingestion with progress bar
# ======================================================
#
# Features:
# - 📊 Real-time progress bar
# - 🔄 Resume capability (skip already processed)
# - ✅ Success/failure tracking
# - 📝 Detailed logging
#
# Usage:
#   ./quick_ingest.sh                    # Dry run - show what would be processed
#   ./quick_ingest.sh --run              # Process all files
#   ./quick_ingest.sh --resume           # Resume from last run
#   ./quick_ingest.sh --dir theory/      # Process specific directory

set -e

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install tqdm if needed
python -c "import tqdm" 2>/dev/null || {
    echo "📦 Installing tqdm for progress bars..."
    pip install -q tqdm
}

# Parse arguments
DRY_RUN=true
RESUME=""
DIR="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --run)
            DRY_RUN=false
            shift
            ;;
        --resume)
            RESUME="--resume batch_ingest.log"
            DRY_RUN=false
            shift
            ;;
        --dir)
            DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--run] [--resume] [--dir <directory>]"
            exit 1
            ;;
    esac
done

# Build command
CMD="python tools/batch_ingest.py --all"

if [ "$DIR" != "." ]; then
    CMD="python tools/batch_ingest.py --dir $DIR"
fi

if [ "$DRY_RUN" = true ]; then
    CMD="$CMD --dry-run"
    echo "🔍 DRY RUN MODE - showing files that would be processed"
    echo ""
fi

if [ -n "$RESUME" ]; then
    CMD="$CMD $RESUME"
    echo "🔄 RESUME MODE - skipping already processed files"
    echo ""
fi

# Run
echo "🚀 Starting batch ingest..."
echo "================================================"
echo ""

$CMD

echo ""
echo "================================================"
echo "✅ Done!"
echo ""
echo "📝 Check batch_ingest.log for details"
echo "📊 Check batch_ingest_summary.json for statistics"
