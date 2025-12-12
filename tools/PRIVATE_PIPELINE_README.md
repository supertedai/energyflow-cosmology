# Private Pipeline - Architecture & Usage
# =====================================

## Purpose

**Isolated personal knowledge graph** for chat, reflection, notes.  
**Physically separated** from EFC theory graph.

## Key Differences from EFC Pipeline

| Aspect | EFC (orchestrator_v2) | Private (private_orchestrator) |
|--------|----------------------|-------------------------------|
| **Namespace** | `:Document`, `:Chunk`, `:Concept` | `:PrivateDocument`, `:PrivateChunk`, `:PrivateConcept` |
| **Qdrant Collection** | `efc` | `private` |
| **Authority Filter** | Yes (strict) | No (accepts everything) |
| **GNN Training** | Yes | No (read-only later) |
| **Memory Classification** | No | Yes (STM/LONGTERM/DISCARD) |
| **Feedback Support** | Not yet | Yes (next phase) |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ PRIVATE PIPELINE                                         │
│                                                          │
│  Input (chat/reflection/note)                           │
│    ↓                                                     │
│  private_orchestrator.py                                │
│    ↓                                                     │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │ Neo4j (private) │    │ Qdrant (private)│            │
│  │ :PrivateDocument│    │ collection:     │            │
│  │ :PrivateChunk   │    │   "private"     │            │
│  │ :PrivateConcept │    │                 │            │
│  └─────────────────┘    └─────────────────┘            │
│    ↓                                                     │
│  memory_classifier.py                                   │
│    ↓                                                     │
│  Tags: STM | LONGTERM | DISCARD                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Usage Examples

### 1. Ingest a chat message

```bash
python tools/private_orchestrator.py \
  --input "I'm thinking about how entropy relates to information..." \
  --type chat
```

### 2. Ingest a reflection

```bash
python tools/private_orchestrator.py \
  --input reflection.txt \
  --type reflection
```

### 3. Classify memory

After ingestion, classify chunks:

```bash
# Get document ID from orchestrator output
python tools/memory_classifier.py \
  --document-id <uuid>
```

Or use heuristic classification (no LLM):

```bash
python tools/memory_classifier.py \
  --document-id <uuid> \
  --no-llm
```

## Memory Classification

**STM (Short-Term Memory)**
- Context-dependent thoughts
- Time-sensitive
- Temporary reflections
- Example: "I wonder if this works..."

**LONGTERM**
- Stable insights
- Reusable understanding
- Resolved questions
- Worth keeping
- **Candidates for EFC promotion**

**DISCARD**
- Filler ("hmm", "let me think")
- Noise
- No lasting value

## Controlled Transfer: Private → EFC

**NOT YET IMPLEMENTED**

Later flow:
```
:PrivateChunk {memory_class: "LONGTERM", verified: true}
  -[:PROMOTED_TO]->
:EFCSeed
  → orchestrator_v2.py (re-ingest)
  → becomes official EFC
```

Manual only in v1.

## Safety Guarantees

✅ **No crossover**: Private and EFC namespaces physically separated  
✅ **No pollution**: Private concepts never train GNN  
✅ **Rollback safe**: Transaction control in both pipelines  
✅ **No single-source classification**: Memory class may not be set to LONGTERM by a single automated signal alone (requires LLM + heuristic agreement OR manual override)  
✅ **Explicit promotion**: LONGTERM must be manually approved before EFC transfer

## What's Next

**Phase 2 - Feedback Layer**
- Add after memory classification
- Before intention/steering
- Structure: See `FEEDBACK_SCHEMA.md` (to be created)

**Phase 3 - Intention Layer**
- Decision gate
- Controls what persists
- Uses both Private + EFC context

**Phase 4 - Multi-agent Orchestration**
- Routing
- Bias control
- Stabilization

## Testing

```bash
# Test private pipeline
python tools/private_orchestrator.py \
  --input "Test private thought" \
  --type chat

# Verify isolation
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as session:
    efc = session.run('MATCH (n:Concept) RETURN count(n)').single()[0]
    private = session.run('MATCH (n:PrivateConcept) RETURN count(n)').single()[0]
    print(f'EFC Concepts: {efc}')
    print(f'Private Concepts: {private}')

driver.close()
"
```

Should show separate counts.

## Files

```
tools/
├── orchestrator_v2.py           # EFC pipeline (gold standard)
├── private_orchestrator.py      # Private pipeline
├── memory_classifier.py         # STM/LONGTERM/DISCARD (initial)
├── memory_classifier_v2.py      # Feedback-aware reclassification
├── feedback_listener.py         # Feedback logging
├── intention_gate.py            # Read-only observation
├── steering_layer.py            # Active promotion/demotion (NEW)
├── export_trainer.py            # Training data export
├── FEEDBACK_SCHEMA.md           # Feedback Neo4j schema
└── PRIVATE_PIPELINE_README.md   # This file
```

## Intention Gate (Read-Only v1)

**Purpose**: Observe and analyze, never modify.

```bash
# View all chunks with suggestions
python tools/intention_gate.py

# Analyze specific chunk
python tools/intention_gate.py --chunk-id <uuid>

# Find promotion candidates
python tools/intention_gate.py --action-filter promote

# Export for external analysis
python tools/intention_gate.py --json > intentions.json
```

**What it calculates:**
- `importance` (0-1): Weighted positive feedback, reduced by negatives
- `uncertainty` (0-1): High if few signals, conflict, or low diversity
- `confidence` (0-1): Based on signal count (full at 5+ signals)
- `conflict` (bool): Positive AND negative signals present
- `risk` (low/medium/high): Overall assessment
- `quality_flags`: Temporal clustering, low source diversity

**Suggestions:**
- `promote`: Consider for LONGTERM/EFC promotion
- `wait`: Too unstable, needs more time
- `review`: High conflict or quality issues
- `none`: No action needed

**Safety features:**
- Temporal weighting (exponential decay, 30-day half-life)
- Source differentiation (manual=1.0, llm=0.7, heuristic=0.5)
- Consensus requirements (≥2 signals, ≥1 manual)
- Time-in-class check (≥24h for promotion)
- Quality flags for spam/bias detection

## Full Workflow Example

```bash
# 1. Ingest private knowledge
python tools/private_orchestrator.py --input note.txt --type reflection

# 2. Initial classification
python tools/memory_classifier.py <doc-id>

# 3. Log feedback (multiple times over days)
python tools/feedback_listener.py \
  --chunk-id <uuid> \
  --signal good \
  --aspect relevance \
  --strength 0.9

# 4. Reclassify with feedback (dry-run first)
python tools/memory_classifier_v2.py <doc-id> --dry-run
python tools/memory_classifier_v2.py <doc-id>

# 5. Observe intentions (read-only)
python tools/intention_gate.py --action-filter promote

# 6. Export training data
python tools/export_trainer.py --format jsonl --output training.jsonl --include-intentions

# 7. Steering (active promotion/demotion)
python tools/steering_layer.py --dry-run  # Test first
python tools/steering_layer.py --apply-all  # Apply all eligible actions
```

## Export Trainer

**Purpose**: Extract Private knowledge + Feedback + Intentions to structured formats for offline analysis, GNN training, and steering simulation.

```bash
# Statistics only (no export)
python tools/export_trainer.py --stats-only

# Export to JSONL (streaming, line-delimited)
python tools/export_trainer.py --format jsonl --output training.jsonl

# Export with intention scores
python tools/export_trainer.py --format jsonl --include-intentions

# Export to Parquet (requires pyarrow)
python tools/export_trainer.py --format parquet --output training.parquet

# Export to CSV (flattened, chunk-level only)
python tools/export_trainer.py --format csv --output training.csv
```

**What it exports:**
- **Chunks**: text, memory_class, created_at, feedback aggregation, concept count
- **Feedback**: individual signals with timestamps, sources, aspects
- **Concepts**: names, types, chunk relationships
- **Intentions**: importance, uncertainty, confidence, conflict, risk, suggested_action (if `--include-intentions`)
- **Statistics**: class distribution, feedback patterns, promotion candidates, conflict metrics

**Use cases:**
- 📊 Analyze feedback patterns and classification accuracy
- 🧪 Test steering logic offline before implementation
- 🎯 Train GNN on feedback→classification relationships
- 🔍 Detect bias (temporal clustering, source imbalance)
- 📈 Track system evolution over time

## Steering Layer (Write-Enabled v1)

**Purpose**: Active memory management with safety gates. First write-enabled layer after observation phases.

```bash
# Dry-run mode (test without changes)
python tools/steering_layer.py --dry-run

# Apply specific action type
python tools/steering_layer.py --dry-run --action promote
python tools/steering_layer.py --dry-run --action demote

# Specific chunk
python tools/steering_layer.py --chunk-id <uuid> --action promote

# Apply all eligible actions (REQUIRES CONFIRMATION)
python tools/steering_layer.py --apply-all
```

**Safety gates enforced:**
1. ✅ Consensus requirement (≥2 signals, ≥1 manual)
2. ✅ Time-in-class minimum (24h for promotion)
3. ✅ Quality threshold (importance > 0.75, confidence > 0.6)
4. ✅ Conflict detection (requires manual review)
5. ✅ Risk assessment (no high-risk auto-promotion)
6. ✅ Audit logging (all decisions tracked)

**Actions:**
- **promote**: STM → LONGTERM (meets all criteria)
- **demote**: LONGTERM → STM (unstable, high uncertainty)
- **discard**: ANY → DISCARD (confirmed low value, requires manual)

**What it updates:**
- Neo4j: `memory_class`, `promoted_at`, `promotion_reason`, `demoted_at`, `demotion_reason`, `discarded_at`
- Qdrant: `memory_class` in payload

**Audit log:**
- Location: `symbiose_gnn_output/steering_audit.jsonl`
- Contains: decision_id, timestamp, chunk_id, action, from/to class, scores, feedback counts, dry_run flag, success/error

## Status

✅ **Phase 1 Complete**: Private pipeline isolated  
✅ **Phase 2 Complete**: Feedback layer implemented  
✅ **Phase 2.1 Complete**: Feedback-aware reclassification  
✅ **Phase 3 Complete**: Intention gate (read-only observation)  
✅ **Phase 4 Complete**: Steering layer (write-enabled with safety gates)  
✅ **Phase 5 Complete**: Training data export with statistics  
🎉 **All core phases complete** - System operational with full learning loop

---

*Built 2025-12-10*
