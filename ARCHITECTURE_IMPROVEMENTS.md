# 🏗️ Architecture Improvements - Critical Path

**Based on**: Fundamental analysis of 9-layer memory system  
**Date**: 2025-12-12  
**Priority**: HIGH - These are foundational improvements needed before scale

---

## 📋 Executive Summary

Current architecture is **functionally sound** with excellent separation of concerns.
However, 5 critical weaknesses must be addressed to prevent:
- Memory inflation
- Performance degradation
- Pattern noise
- Query inefficiency

All improvements are **low effort, high impact**.

---

## 🎯 Critical Improvements (Priority Order)

### 1️⃣ Canonical Memory Schema (HIGHEST PRIORITY)

**Problem**: Layer 1 (CMC) can grow uncontrolled without fact restrictions.

**Impact**: 
- Redundant facts
- Conflicting entries
- Search degradation

**Solution**: Implement strict schema for canonical facts.

**File**: `tools/canonical_memory_schema.json`

```json
{
  "schema_version": "1.0",
  "allowed_domains": {
    "identity": {
      "max_facts": 10,
      "allowed_keys": ["name", "birthday", "location", "occupation"],
      "example": "Brukeren heter Morten"
    },
    "family": {
      "max_facts": 15,
      "allowed_keys": ["children", "partner", "parents", "siblings"],
      "example": "3 barn: Joakim, Isak Andreas, Susanna"
    },
    "preferences": {
      "max_facts": 20,
      "allowed_keys": ["interface_style", "language", "communication_style", "notification_prefs"],
      "example": "Foretrekker norsk språk"
    },
    "professional": {
      "max_facts": 15,
      "allowed_keys": ["skills", "projects", "expertise", "tools"],
      "example": "Ekspert i Energy-Flow Cosmology"
    }
  },
  "global_limits": {
    "max_total_facts": 100,
    "max_fact_length": 500,
    "min_confidence": 0.7
  },
  "validation_rules": {
    "require_domain": true,
    "require_key": true,
    "require_confidence": true,
    "allow_duplicates": false
  }
}
```

**Implementation**:
- Add to `canonical_memory_core.py`:
  ```python
  def validate_fact(self, domain: str, key: str, value: str) -> bool:
      schema = load_schema()
      if domain not in schema["allowed_domains"]:
          raise ValueError(f"Domain {domain} not in schema")
      if key not in schema["allowed_domains"][domain]["allowed_keys"]:
          raise ValueError(f"Key {key} not allowed in domain {domain}")
      # Check domain limits
      # Check global limits
      return True
  ```

**Effort**: 2 hours  
**Impact**: Prevents 80% of memory inflation issues

---

### 2️⃣ Multi-Fact Synthesis (USER-VISIBLE BUG)

**Problem**: Queries like "Hvem er barna mine?" return only first fact, not all three children.

**Impact**: 
- Incomplete responses
- User frustration
- Reduced system trust

**Solution**: Implement aggregation in Layer 5 (AME).

**File**: `tools/adaptive_memory_enforcer.py`

**Current code** (line ~290):
```python
def _retrieve_canonical_facts(self, query_text: str, limit: int = 5):
    results = self.canonical_memory.query_related_facts(query_text, limit)
    return [r.payload.get("value") for r in results]
```

**New code**:
```python
def _retrieve_canonical_facts(self, query_text: str, limit: int = 10):
    results = self.canonical_memory.query_related_facts(query_text, limit)
    
    # Group by domain
    facts_by_domain = {}
    for r in results:
        domain = r.payload.get("domain")
        key = r.payload.get("key")
        value = r.payload.get("value")
        
        if domain not in facts_by_domain:
            facts_by_domain[domain] = {}
        if key not in facts_by_domain[domain]:
            facts_by_domain[domain][key] = []
        facts_by_domain[domain][key].append(value)
    
    # Synthesize multi-facts
    synthesized = []
    for domain, keys in facts_by_domain.items():
        for key, values in keys.items():
            if len(values) > 1:
                # Multiple facts for same key → synthesize
                if domain == "family" and key == "children":
                    synthesized.append(f"Barna dine heter {', '.join(values)}")
                else:
                    synthesized.append("; ".join(values))
            else:
                synthesized.append(values[0])
    
    return synthesized
```

**Effort**: 1 hour  
**Impact**: Fixes immediate user-facing bug

---

### 3️⃣ Semantic Mesh Aging (PERFORMANCE)

**Problem**: Layer 2 (SMM) grows indefinitely with every conversation.

**Impact**:
- Qdrant search slows down
- Irrelevant old context retrieved
- Storage costs increase

**Solution**: Implement automatic pruning + aging.

**File**: `tools/semantic_mesh_memory.py`

**New methods**:
```python
def prune_old_conversations(self, days_threshold: int = 180):
    """Remove conversations older than threshold"""
    cutoff_timestamp = datetime.now() - timedelta(days=days_threshold)
    
    # Get all old points
    old_points = self.client.scroll(
        collection_name="semantic_mesh",
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="timestamp",
                    range=models.Range(lt=cutoff_timestamp.isoformat())
                )
            ]
        ),
        limit=1000
    )
    
    # Delete in batches
    ids_to_delete = [p.id for p in old_points[0]]
    if ids_to_delete:
        self.client.delete(
            collection_name="semantic_mesh",
            points_selector=ids_to_delete
        )
        logger.info(f"Pruned {len(ids_to_delete)} old conversations")

def decay_unused_facts(self, usage_threshold: int = 30):
    """Lower score for rarely used facts"""
    # Implementation: add usage_count to metadata
    # Decay score = base_score * (0.5 + 0.5 * usage_count / 10)
    pass
```

**Cron job** (add to system):
```bash
# Daily cleanup - run at 3 AM
0 3 * * * cd /Users/morpheus/energyflow-cosmology && python -c "from tools.semantic_mesh_memory import SemanticMeshMemory; smm = SemanticMeshMemory(); smm.prune_old_conversations(180)"
```

**Effort**: 2 hours  
**Impact**: Prevents semantic_mesh from becoming bottleneck

---

### 4️⃣ Neo4j Vector Optimization (CRITICAL FOR EFC QUERIES)

**Problem**: Neo4j not optimized for graph-vector hybrid queries.

**Impact**:
- Slow EFC theory queries
- Poor graph traversal performance
- Memory inefficiency

**Solution**: Enable vector indexes + graph-specific settings.

**File**: `neo4j/neo4j.conf` (create if not exists)

```conf
# Memory allocation
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# Vector index optimization
db.index.vector.enabled=true
db.index.vector.ephemeral_graph_enabled=true

# Graph traversal optimization
cypher.min_replan_interval=10s
cypher.statistics_divergence_threshold=0.75

# Query optimization
dbms.query_cache_size=1000
dbms.query_plan_cache_size=1000

# Relationship index (for SUPPORTS, CONSTRAINS, etc.)
dbms.relationship_index.enabled=true
```

**Cypher indexes** (run once):
```cypher
-- Vector similarity index for Concept embeddings
CREATE VECTOR INDEX concept_embeddings IF NOT EXISTS
FOR (c:Concept)
ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

-- Text index for fast concept lookup
CREATE TEXT INDEX concept_name IF NOT EXISTS
FOR (c:Concept) ON (c.name);

-- Composite index for document chunks
CREATE INDEX chunk_document IF NOT EXISTS
FOR (ch:Chunk) ON (ch.document_id, ch.chunk_id);

-- Relationship type index
CREATE LOOKUP INDEX rel_type_lookup IF NOT EXISTS
FOR ()-[r]-() ON TYPE(r);
```

**Verification script**: `scripts/verify_neo4j_perf.py`
```python
from neo4j import GraphDatabase
import time

driver = GraphDatabase.driver(...)

with driver.session() as session:
    # Test 1: Concept retrieval
    start = time.time()
    result = session.run("MATCH (c:Concept {name: 'Entropy'}) RETURN c")
    print(f"Concept lookup: {time.time() - start:.3f}s")
    
    # Test 2: Graph traversal
    start = time.time()
    result = session.run("""
        MATCH (c:Concept {name: 'Entropy'})-[:SUPPORTS*1..3]->(related)
        RETURN related.name LIMIT 10
    """)
    print(f"Graph traversal: {time.time() - start:.3f}s")
    
    # Test 3: Vector similarity (if embeddings exist)
    # ...
```

**Effort**: 3 hours (includes testing)  
**Impact**: 3-10x speedup on EFC queries

---

### 5️⃣ Router Decision Logging (OBSERVABILITY)

**Problem**: No visibility into which layers activate per turn.

**Impact**:
- Difficult debugging
- No performance metrics
- Can't optimize routing logic

**Solution**: Add structured logging to Router V4.

**File**: `tools/symbiosis_router_v4.py`

**Add to `handle_chat_turn()`**:
```python
async def handle_chat_turn(self, user_message: str, assistant_draft: str, session_id: str):
    routing_log = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "user_message_length": len(user_message),
        "activated_layers": [],
        "layer_timings": {},
        "routing_reason": "",
        "contradiction_detected": False,
        "final_decision": ""
    }
    
    # Layer 4: DDE
    start = time.time()
    routing_decision = await self.dde.analyze_input(user_message, assistant_draft)
    routing_log["layer_timings"]["dde"] = time.time() - start
    routing_log["activated_layers"] = routing_decision["layers"]
    routing_log["routing_reason"] = routing_decision["reason"]
    
    # Layer 1-3: Read layers (if activated)
    if 1 in routing_decision["layers"]:
        start = time.time()
        # ... canonical memory logic
        routing_log["layer_timings"]["canonical"] = time.time() - start
    
    # Layer 5: AME
    start = time.time()
    result = await self.ame.enforce_memory(user_message, assistant_draft, session_id)
    routing_log["layer_timings"]["ame"] = time.time() - start
    routing_log["contradiction_detected"] = result["was_overridden"]
    routing_log["final_decision"] = "OVERRIDE" if result["was_overridden"] else "TRUST_LLM"
    
    # Log to file
    log_file = Path("logs/router_decisions.jsonl")
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "a") as f:
        f.write(json.dumps(routing_log) + "\n")
    
    return result
```

**Analysis script**: `scripts/analyze_routing.py`
```python
import json
from pathlib import Path
from collections import Counter

logs = [json.loads(line) for line in Path("logs/router_decisions.jsonl").read_text().splitlines()]

print(f"Total turns analyzed: {len(logs)}")
print(f"Contradictions detected: {sum(1 for l in logs if l['contradiction_detected'])}")
print(f"Average AME time: {sum(l['layer_timings']['ame'] for l in logs) / len(logs):.3f}s")

layer_usage = Counter()
for log in logs:
    for layer in log["activated_layers"]:
        layer_usage[layer] += 1

print("\nLayer activation frequency:")
for layer, count in layer_usage.most_common():
    print(f"  Layer {layer}: {count} times ({count/len(logs)*100:.1f}%)")
```

**Effort**: 2 hours  
**Impact**: Complete observability into system behavior

---

## 📊 Implementation Timeline

### Week 1: Critical Fixes
- **Day 1**: Canonical Memory Schema (#1) - 2 hours
- **Day 2**: Multi-Fact Synthesis (#2) - 1 hour
- **Day 3**: Test + validate schema + synthesis

### Week 2: Performance
- **Day 1**: Neo4j Optimization (#4) - 3 hours
- **Day 2**: Semantic Mesh Aging (#3) - 2 hours
- **Day 3**: Router Logging (#5) - 2 hours

### Week 3: Validation
- **Day 1-2**: Full system integration tests
- **Day 3**: Performance benchmarks + documentation

**Total effort**: ~15 hours  
**Expected impact**: 5-10x improvement in reliability and performance

---

## 🎯 Success Metrics

### Before Improvements:
- Canonical facts: Unlimited growth
- Multi-fact queries: Return only first fact
- Semantic mesh: ~51 old vectors (cleaned manually)
- Neo4j queries: No indexes, slow traversal
- Router decisions: No visibility

### After Improvements:
- Canonical facts: Max 100, strict schema, validated
- Multi-fact queries: Synthesized complete responses
- Semantic mesh: Auto-pruned every 180 days
- Neo4j queries: 3-10x faster with vector indexes
- Router decisions: Complete JSONL logs for analysis

---

## 🔐 Risk Assessment

### Low Risk:
- Schema validation (can disable if issues)
- Router logging (pure observability)

### Medium Risk:
- Multi-fact synthesis (needs extensive testing)
- Semantic aging (need backup before first run)

### High Risk:
- Neo4j config changes (restart required, affects all queries)
  **Mitigation**: Test on dev instance first

---

## 📚 Additional Recommendations

### 1. Pattern Learning Validation (Layer 6)
- **Issue**: MLC thresholds untested in production
- **Fix**: Add validation script to test pattern quality
- **Priority**: Medium (affects learning accuracy)

### 2. Confidence Decay Rules (Layer 8)
- **Issue**: No decay implementation yet
- **Fix**: Define decay curves per domain
- **Priority**: Low (system works without it)

### 3. Causal Chain Visualization (Layer 9)
- **Issue**: No UI to see fact dependencies
- **Fix**: Create simple viz tool
- **Priority**: Low (debugging aid only)

---

## 🚀 Next Steps

1. **Review this document** - validate priorities
2. **Create canonical_memory_schema.json** - start with schema
3. **Implement multi-fact synthesis** - user-facing bug fix
4. **Test in isolation** - validate before full integration
5. **Deploy to production** - monitor router logs closely

---

**Status**: 🟡 Draft - awaiting review  
**Owner**: @morpheus  
**Last updated**: 2025-12-12
