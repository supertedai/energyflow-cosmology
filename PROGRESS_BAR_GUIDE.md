# Progress Bar Ingestion Guide 📊

Nytt batch ingestion system med visuell progress tracking!

## Features

✅ **Real-time progress bar** - Se fremgang med tqdm  
✅ **Success/failure tracking** - Live statistikk  
✅ **Resume capability** - Start på nytt uten duplikater  
✅ **Detailed logging** - Full sporing i JSON log  
✅ **Statistics summary** - Chunks, concepts, tokens  
✅ **Theory folder PRIMARY trust** - Alle theory/ filer har full autoritet

## Status

**Latest Update**: December 10, 2024  
- ✅ **Theory folder ingestion COMPLETE**: 33/33 files (100%)
- ✅ **System state**: 987 docs, 9,580 chunks, 1,959 concepts
- ✅ **Perfect sync**: Neo4j ↔ Qdrant (9,580 = 9,580)
- ✅ **Authority fix**: Theory files get PRIMARY trust (1.0) automatically

See: [THEORY_INGESTION_COMPLETE.md](./THEORY_INGESTION_COMPLETE.md) for details.

## Quick Start

### 1. Dry Run (se hva som vil bli prosessert)
```bash
./quick_ingest.sh
```

### 2. Kjør full ingest
```bash
./quick_ingest.sh --run
```

### 3. Resume etter feil/avbrudd
```bash
./quick_ingest.sh --resume
```

### 4. Prosesser spesifikk directory
```bash
./quick_ingest.sh --run --dir theory/
```

## Python Direct Usage

### Batch ingest med progress bar
```bash
source .venv/bin/activate

# Dry run
python tools/batch_ingest.py --all --dry-run

# Full run
python tools/batch_ingest.py --all

# Specific directory
python tools/batch_ingest.py --dir theory/

# Resume from previous run
python tools/batch_ingest.py --all --resume batch_ingest.log
```

## Output Files

```
batch_ingest.log          # Detaljert JSON log (per-file)
batch_ingest_summary.json # Statistikk og sammendrag
```

### Log Format (batch_ingest.log)
```json
{
  "timestamp": "2025-12-10T...",
  "file": "theory/formal/README.md",
  "status": "success",
  "document_id": "uuid...",
  "chunks": 15,
  "concepts": 8,
  "tokens": 3200
}
```

### Summary Format (batch_ingest_summary.json)
```json
{
  "timestamp": "2025-12-10T...",
  "total_files": 587,
  "processed": 350,
  "successful": 345,
  "errors": 5,
  "skipped": 237,
  "statistics": {
    "chunks": 5234,
    "concepts": 1089,
    "tokens": 1250000
  },
  "recent_errors": [...]
}
```

## Progress Bar View

```
Processing theory/formal/efc-formal-spec/README.md: 45%|████▌     | 265/587 [15:23<17:45, 3.31s/file]
✅ 260 | ❌ 5 | chunks: 4234 | concepts: 892
```

## Resume Capability

Systemet tracker automatisk hvilke filer som er prosessert:

1. **Kjør ingest**: `./quick_ingest.sh --run`
2. **Avbrudd skjer** (Ctrl+C, error, etc.)
3. **Resume**: `./quick_ingest.sh --resume`
4. **Hopper over** allerede prosesserte filer ✅

## Example Workflow

```bash
# 1. Se hva som finnes
./quick_ingest.sh

# Output:
# 📁 Found 587 files to process
# DRY RUN - Files that would be processed:
#   - README.md
#   - START-HERE.md
#   - theory/formal/README.md
#   ...

# 2. Start ingestion
./quick_ingest.sh --run

# Live progress:
# Ingesting: 100%|██████████| 587/587 [45:23<00:00, 4.63s/file]
# ✅ 580 | ❌ 7 | chunks: 8234 | concepts: 1892

# 3. Check results
cat batch_ingest_summary.json

# 4. If errors, check log
grep '"status": "error"' batch_ingest.log
```

## Advanced Usage

### Process only specific patterns
```python
from pathlib import Path
from tools.batch_ingest import batch_ingest

# Theory files only
root = Path("theory")
batch_ingest(root, log_file=Path("theory_ingest.log"))
```

### Custom file filtering
Edit `tools/batch_ingest.py`:
```python
INCLUDE_PATTERNS = [
    "*.md",      # Markdown
    "*.py",      # Python
    "*.tex",     # LaTeX
    "*.jsonld",  # JSON-LD
]

EXCLUDE_DIRS = [
    ".git",
    ".venv",
    "__pycache__",
    # Add custom exclusions
]
```

## Troubleshooting

### "No module named 'tqdm'"
```bash
pip install tqdm
```

### Progress bar not showing
Ensure terminal supports ANSI:
```bash
export TERM=xterm-256color
```

### Resume not working
Check log file exists:
```bash
ls -lh batch_ingest.log
```

### Too many files
Process in batches by directory:
```bash
./quick_ingest.sh --run --dir theory/
./quick_ingest.sh --run --dir figshare/
./quick_ingest.sh --run --dir docs/
```

## Integration with Gold Standard

Old way (no progress bar):
```bash
bash ingest_gold_standard.sh  # 587 files, no visual feedback
```

New way (with progress bar):
```bash
./quick_ingest.sh --run  # Same files, visual progress!
```

## Performance Tips

1. **Batch processing**: Process ~100 files at a time for better progress tracking
2. **Resume frequently**: Use `--resume` to avoid reprocessing on errors
3. **Monitor logs**: Watch `batch_ingest.log` in real-time:
   ```bash
   tail -f batch_ingest.log | grep status
   ```
4. **Check statistics**: View `batch_ingest_summary.json` after each run

## Status Monitoring

### During ingestion
```bash
# Terminal 1: Run ingestion
./quick_ingest.sh --run

# Terminal 2: Monitor progress
watch -n 5 "grep -c 'success' batch_ingest.log"
```

### After ingestion
```bash
# Check Neo4j
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as s:
    docs = s.run('MATCH (d:Document) RETURN count(d) as c').single()['c']
    chunks = s.run('MATCH (ch:Chunk) RETURN count(ch) as c').single()['c']
    concepts = s.run('MATCH (c:Concept) RETURN count(c) as c').single()['c']
    
print(f'Documents: {docs}')
print(f'Chunks: {chunks}')
print(f'Concepts: {concepts}')

driver.close()
"
```

## Next Steps

After successful ingestion:

1. **Verify sync**: Check Neo4j ↔ Qdrant consistency
2. **Semantic augmentation**: Add theory structure
3. **GNN export**: Prepare for training
4. **Quality check**: Validate extracted concepts

See `docs/PRODUCTION_READINESS.md` for full pipeline.
