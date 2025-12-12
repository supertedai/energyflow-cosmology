# Unified Ingestion Pipeline - Orchestrator v2

**🔒 MANDATORY ENTRY POINT FOR ALL DATA**

All new information entering the EnergyFlow Cosmology system MUST go through this pipeline to ensure:
- ✅ 100% deterministic token-based chunking
- ✅ LLM-powered concept extraction
- ✅ Perfect Qdrant ↔ Neo4j sync
- ✅ Rollback safety on failures
- ✅ GNN integration (coming soon)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ALL DATA ENTRY POINTS                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
         ┌────────────────────┼────────────────────┐
         ↓                    ↓                    ↓
    API Endpoint       File Upload         Batch Script
  (ingestion_api)   (ingestion_hook)    (batch_ingest)
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ↓
                   ┌──────────────────────┐
                   │  ORCHESTRATOR V2     │
                   │  (deterministic)     │
                   └──────────────────────┘
                              ↓
         ┏━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┓
         ↓                    ↓                    ↓
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ Qdrant  │         │  Neo4j  │         │   GNN   │
    │ (vector)│←────sync────→(graph)│←────sync────→(struct)│
    └─────────┘         └─────────┘         └─────────┘
```

---

## Components

### 1. **orchestrator_v2.py** (Core Pipeline)
The deterministic ingestion pipeline with ALL production fixes:
- Token-based chunking (tiktoken cl100k_base)
- LLM concept extraction (GPT-4o-mini)
- Safe Neo4j transactions
- Qdrant rollback with PointIdsList
- Embedding dimension validation
- Progress indicators

**Usage:**
```bash
python tools/orchestrator_v2.py --input README.md --type document
```

### 2. **ingestion_hook.py** (Programmatic Interface)
Python API for programmatic ingestion. Use this in your code:

```python
from tools.ingestion_hook import ingest_text, ingest_file

# Ingest text
result = ingest_text(
    text="Energy-flow cosmology explains...",
    source="manual_entry",
    input_type="document"
)

# Ingest file
result = ingest_file("docs/new_paper.md")

# Result contains:
# - document_id (UUID)
# - chunk_ids (list of UUIDs)
# - concepts (list of extracted concepts)
# - neo4j_node_id
# - total_tokens
```

### 3. **ingestion_api.py** (REST API)
FastAPI endpoint for HTTP-based ingestion:

```bash
# Start API
uvicorn tools.ingestion_api:app --host 0.0.0.0 --port 8001

# Ingest via curl
curl -X POST http://localhost:8001/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "text": "New content here",
       "source": "api_client",
       "type": "document"
     }'

# Batch ingest
curl -X POST http://localhost:8001/ingest/batch \
     -H "Content-Type: application/json" \
     -d '{"items": [...]}'

# File upload
curl -X POST http://localhost:8001/ingest/file \
     -F "file=@docs/paper.md"

# Health check
curl http://localhost:8001/health

# Stats
curl http://localhost:8001/stats
```

### 4. **batch_ingest.py** (Bulk Processing)
Process entire repository or directories:

```bash
# Dry run (list files)
python tools/batch_ingest.py --dir theory/ --dry-run

# Process directory
python tools/batch_ingest.py --dir docs/

# Process entire repo
python tools/batch_ingest.py --all
```

Saves results to `batch_ingest_results.json`.

---

## Pipeline Guarantees

### ✅ Deterministic Chunking
- Uses tiktoken cl100k_base (same as GPT-4o-mini)
- Fixed chunk size: 512 tokens
- Fixed overlap: 50 tokens
- Respects sentence boundaries
- **Result:** Same input = same chunks, always

### ✅ Perfect Sync
- Single transaction for Neo4j writes
- Rollback to Qdrant if Neo4j fails
- UUID-based point IDs in Qdrant
- Unambiguous graph paths in Neo4j
- **Result:** Qdrant ↔ Neo4j never drift

### ✅ LLM Concept Extraction
- GPT-4o-mini with structured output
- JSON mode with schema validation
- Fallback to regex keywords if LLM fails
- **Result:** Intelligent, domain-relevant concepts

### ✅ Rollback Safety
- Qdrant points saved with UUIDs
- Neo4j transaction with explicit tx.rollback()
- Failed chunks deleted from Qdrant
- **Result:** No partial ingestion, ever

### ✅ Progress Visibility
- Token encoding progress
- Chunk creation counter
- Embedding generation progress
- Neo4j operation status
- **Result:** No silent hangs

---

## Data Structure

### Qdrant Schema
```json
{
  "id": "uuid-string",
  "vector": [3072-dim embedding],
  "payload": {
    "text": "chunk text",
    "chunk_index": 0,
    "document_id": "uuid",
    "source": "README.md",
    "metadata": {...}
  }
}
```

### Neo4j Schema
```cypher
(Document {id: "uuid", source: "README.md", created_at: timestamp})
  -[:HAS_CHUNK {chunk_index: 0}]->
(Chunk {id: "uuid", text: "...", tokens: 512})
  -[:MENTIONS]->
(Concept {name: "Energy-Flow Cosmology"})
```

### Query Example
```cypher
// Find all chunks mentioning a concept
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(concept:Concept {name: "Energy-Flow Cosmology"})
RETURN d.source, c.text, c.id
```

---

## Migration from Old System

### OLD (deprecated):
```python
# ❌ Direct Qdrant insert - NO SYNC
qdrant.upsert(collection_name="efc", points=[...])

# ❌ Direct Neo4j write - NO VECTOR
session.run("CREATE (n:Document {id: $id})", id=doc_id)

# ❌ Manual concept extraction - INCONSISTENT
concepts = extract_keywords(text)
```

### NEW (required):
```python
# ✅ Use ingestion hook - PERFECT SYNC
from tools.ingestion_hook import ingest_text

result = ingest_text(
    text=text,
    source="migration",
    input_type="document"
)
# → Automatic: chunking + embedding + concepts + sync
```

---

## Testing the Pipeline

### 1. Test Single Document
```bash
python tools/orchestrator_v2.py --input README.md --type document
```

Expected output:
- ✅ N chunks created
- ✅ M concepts extracted
- ✅ Qdrant points inserted
- ✅ Neo4j nodes created
- ✅ Document ID returned

### 2. Test via API
```bash
# Start API
uvicorn tools.ingestion_api:app --port 8001 &

# Test ingestion
curl -X POST http://localhost:8001/ingest \
     -H "Content-Type: application/json" \
     -d '{"text": "Test content", "source": "test"}'

# Check stats
curl http://localhost:8001/stats
```

### 3. Test Batch Processing
```bash
# Dry run
python tools/batch_ingest.py --dir theory/ --dry-run

# Process small directory
python tools/batch_ingest.py --dir theory/
```

### 4. Validate Sync
```bash
python tools/validator.py --test all
```

---

## Troubleshooting

### Problem: "Infinite loop" / script hangs
**Solution:** Already fixed in v2 with `advance = max(len(chunk_tokens) - overlap, 1)`

### Problem: "Not a valid point ID"
**Solution:** Already fixed in v2 with `str(uuid.uuid4())` for chunk IDs

### Problem: "LLM concept extraction fails"
**Solution:** Fallback to regex keywords is automatic

### Problem: "Neo4j transaction fails"
**Solution:** Automatic rollback removes Qdrant points

### Problem: "No progress indicator"
**Solution:** All stages now print progress

---

## Future Enhancements

### 🔜 GNN Integration (Step 8)
Currently marked TODO in orchestrator:
```python
# TODO: Update GNN index
# - Map chunk UUIDs to GNN node indices
# - Update bridge file
# - Enable structural_score in hybrid search
```

### 🔜 Incremental Updates
Support for updating existing documents without re-ingesting:
```python
update_document(document_id, new_text)
```

### 🔜 Batch Optimization
Parallel processing for large-scale ingestion:
```python
batch_ingest_parallel(files, workers=4)
```

---

## Production Deployment

### Environment Variables Required
```bash
# .env file
QDRANT_URL=https://...
QDRANT_API_KEY=...
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
OPENAI_API_KEY=sk-...
COHERE_API_KEY=...
```

### Docker Deployment
```bash
# Build ingestion API
docker build -f Dockerfile.ingestion_api -t efc-ingestion:v2 .

# Run
docker run -p 8001:8001 --env-file .env efc-ingestion:v2
```

### Monitoring
- Health endpoint: `GET /health`
- Stats endpoint: `GET /stats`
- Logs: All operations print structured logs

---

## Summary

**🔒 REMEMBER:**
1. **ALL data MUST go through orchestrator_v2**
2. **Use ingestion_hook.py in Python code**
3. **Use ingestion_api.py for HTTP clients**
4. **Use batch_ingest.py for bulk processing**
5. **NEVER write directly to Qdrant or Neo4j**

This ensures:
- ✅ Perfect sync across all systems
- ✅ 100% deterministic chunking
- ✅ Intelligent concept extraction
- ✅ Rollback safety
- ✅ Production reliability
