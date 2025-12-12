# Feedback Layer - Neo4j Schema & Architecture
# ============================================

## Purpose

**Capture human feedback on private chunks/concepts** for:
- Learning signal (future bias control)
- Quality validation
- Memory classification refinement
- Training buffer for alignment

## Placement in Architecture

```
Input → private_orchestrator → Neo4j/Qdrant
                                    ↓
                            memory_classifier
                                    ↓
                            FEEDBACK LAYER ← YOU ARE HERE
                                    ↓
                            (future: intention layer)
```

## Core Principle

> **Feedback points to stable node IDs, not text.**

This enables:
- Temporal tracking (how feedback evolves)
- Multi-source validation
- Training signal accumulation

---

## Neo4j Schema

### `:Feedback` Node

```cypher
(:Feedback {
  id: String (UUID),
  timestamp: Integer (Unix timestamp),
  
  // Feedback type
  signal: String,  // "correct" | "incorrect" | "good" | "bad" | "unsure" | "neutral"
  strength: Float, // 0.0-1.0 confidence in feedback
  
  // Context
  context: String, // Optional: why this feedback was given
  session_id: String, // Optional: group related feedback
  
  // Metadata
  source: String,  // "manual" | "heuristic" | "llm_agreement"
  created_at: DateTime
})
```

### Relationships

#### 1. Feedback → Chunk

```cypher
(:Feedback)-[:EVALUATES {
  aspect: String  // "classification" | "content" | "relevance"
}]->(:PrivateChunk)
```

#### 2. Feedback → Concept

```cypher
(:Feedback)-[:EVALUATES {
  aspect: String  // "extraction" | "accuracy" | "usefulness"
}]->(:PrivateConcept)
```

#### 3. Feedback → Memory Classification

```cypher
(:Feedback)-[:VALIDATES {
  original_class: String,  // STM | LONGTERM | DISCARD
  suggested_class: String  // What it should be
}]->(:PrivateChunk)
```

#### 4. Feedback Chains (evolving opinions)

```cypher
(:Feedback)-[:SUPERSEDES]->(:Feedback)
```

Allows tracking changing evaluations over time.

---

## Safety Rules

### ✅ Anti-Bias Rules

**Rule 1: No single-source LONGTERM promotion**
```cypher
// INVALID: Single feedback promoting to LONGTERM
MATCH (f:Feedback {signal: "good"})-[:EVALUATES]->(c:PrivateChunk)
SET c.memory_class = "LONGTERM"  // ❌ FORBIDDEN

// VALID: Requires consensus
MATCH (c:PrivateChunk)<-[:EVALUATES]-(f:Feedback)
WHERE f.signal = "good"
WITH c, count(f) as positive_count
WHERE positive_count >= 2  // Multiple signals required
SET c.memory_class = "LONGTERM"  // ✅ SAFE
```

**Rule 2: No feedback-to-EFC direct path**
```cypher
// INVALID: Feedback directly promoting to EFC
MATCH (f:Feedback)-[:EVALUATES]->(c:PrivateChunk)
WHERE f.signal = "correct"
CREATE (c)-[:PROMOTED_TO]->(:EFCSeed)  // ❌ FORBIDDEN

// VALID: Manual gate required
MATCH (c:PrivateChunk {memory_class: "LONGTERM", verified: true})
WHERE NOT exists((c)-[:PROMOTED_TO]->())
// Manual inspection before promotion
```

**Rule 3: Feedback decay**
```cypher
// Old feedback loses weight
MATCH (f:Feedback)-[:EVALUATES]->(c:PrivateChunk)
WHERE timestamp() - f.timestamp > 86400000 * 30  // 30 days
SET f.strength = f.strength * 0.8
```

---

## Feedback Types

### 1. Classification Feedback

**"This chunk's memory class is wrong"**

```cypher
CREATE (f:Feedback {
  id: randomUUID(),
  timestamp: timestamp(),
  signal: "incorrect",
  strength: 1.0,
  context: "This is clearly long-term, not STM",
  source: "manual"
})

MATCH (c:PrivateChunk {id: $chunk_id})
CREATE (f)-[:VALIDATES {
  original_class: c.memory_class,
  suggested_class: "LONGTERM"
}]->(c)
```

### 2. Concept Extraction Feedback

**"This concept was extracted incorrectly"**

```cypher
CREATE (f:Feedback {
  id: randomUUID(),
  timestamp: timestamp(),
  signal: "incorrect",
  strength: 1.0,
  context: "This is not about 'entropy' in the physics sense",
  source: "manual"
})

MATCH (c:PrivateConcept {name: $concept_name})
CREATE (f)-[:EVALUATES {
  aspect: "accuracy"
}]->(c)
```

### 3. Quality Feedback

**"This is valuable / not valuable"**

```cypher
CREATE (f:Feedback {
  id: randomUUID(),
  timestamp: timestamp(),
  signal: "good",  // or "bad"
  strength: 0.8,
  context: "Key insight about information theory",
  source: "manual"
})

MATCH (c:PrivateChunk {id: $chunk_id})
CREATE (f)-[:EVALUATES {
  aspect: "relevance"
}]->(c)
```

### 4. Uncertainty Signal

**"I'm not sure about this"**

```cypher
CREATE (f:Feedback {
  id: randomUUID(),
  timestamp: timestamp(),
  signal: "unsure",
  strength: 0.5,
  context: "Need more time to evaluate",
  source: "manual"
})

MATCH (c:PrivateChunk {id: $chunk_id})
CREATE (f)-[:EVALUATES {
  aspect: "classification"
}]->(c)
```

---

## Queries for Analysis

### 1. Find chunks with conflicting feedback

```cypher
MATCH (c:PrivateChunk)<-[e:EVALUATES]-(f:Feedback)
WITH c, collect(f.signal) as signals
WHERE size([s IN signals WHERE s = "good"]) > 0
  AND size([s IN signals WHERE s = "bad"]) > 0
RETURN c.id, c.text, signals
```

### 2. Find candidates for LONGTERM promotion

```cypher
MATCH (c:PrivateChunk {memory_class: "STM"})<-[:EVALUATES]-(f:Feedback)
WHERE f.signal IN ["good", "correct"]
  AND f.strength >= 0.7
WITH c, count(f) as positive_count, collect(f.source) as sources
WHERE positive_count >= 2
  AND size([s IN sources WHERE s = "manual"]) >= 1  // At least one manual
RETURN c.id, c.text, positive_count, sources
ORDER BY positive_count DESC
```

### 3. Feedback quality over time

```cypher
MATCH (f:Feedback)-[:EVALUATES]->(c:PrivateChunk)
WITH date(datetime({epochMillis: f.timestamp})) as day,
     f.signal as signal,
     count(*) as count
RETURN day, signal, count
ORDER BY day DESC
LIMIT 30
```

### 4. Most corrected concepts

```cypher
MATCH (c:PrivateConcept)<-[:EVALUATES]-(f:Feedback {signal: "incorrect"})
WITH c, count(f) as correction_count
WHERE correction_count > 1
RETURN c.name, c.type, correction_count
ORDER BY correction_count DESC
```

---

## Integration with memory_classifier.py

### Current flow:
```
memory_classifier.py
  ↓
Set memory_class (STM/LONGTERM/DISCARD)
```

### Enhanced flow with feedback:
```
memory_classifier.py
  ↓
Set memory_class
  ↓
feedback_listener.py (manual review)
  ↓
:Feedback nodes created
  ↓
(future) Re-classify based on feedback accumulation
```

---

## Storage Strategy

### Neo4j (structural)
- `:Feedback` nodes
- Relationships to chunks/concepts
- Temporal tracking

### Optional: JSON buffer
For offline analysis / training data export:

```json
{
  "feedback_id": "uuid",
  "timestamp": 1234567890,
  "signal": "correct",
  "strength": 1.0,
  "target_type": "chunk",
  "target_id": "chunk-uuid",
  "context": "...",
  "source": "manual"
}
```

Store in: `symbiose_gnn_output/feedback_buffer.jsonl`

---

## Anti-Patterns (What NOT to do)

❌ **Direct promotion without verification**
```cypher
// DON'T
MATCH (f:Feedback {signal: "good"})-[:EVALUATES]->(c:PrivateChunk)
SET c.memory_class = "LONGTERM"
```

❌ **Ignoring feedback decay**
```cypher
// DON'T
MATCH (f:Feedback)-[:EVALUATES]->(c)
RETURN c
// Should weight by recency
```

❌ **Single-source trust**
```cypher
// DON'T
MATCH (f:Feedback {source: "llm"})-[:EVALUATES]->(c)
SET c.verified = true
// Needs multiple sources or manual confirmation
```

---

## Next Steps

1. **Implement feedback_listener.py** (CLI/API for creating feedback)
2. **Test feedback accumulation** (multiple signals on same chunk)
3. **Build feedback-aware re-classifier** (uses feedback to refine memory_class)
4. **Export to training buffer** (prepare for bias control layer)

---

## Status

✅ **Schema defined**  
🔜 **Implementation**: feedback_listener.py  
🔜 **Testing**: feedback accumulation & consensus  
🔜 **Integration**: memory re-classification based on feedback

---

*Schema v1.0 - 2025-12-10*
