# 🌉 Universal Memory Bridge - Implementation Plan

## Executive Summary

**Problem**: Current memory sync is one-directional, domain-isolated, and lacks semantic cross-domain inference.

**Solution**: Universal Memory Bridge - adaptive, bidirectional synchronization across all storage layers with semantic matching and logical inference.

---

## Current State (What Works)

### ✅ Core Infrastructure
1. **MCP Server** (`mcp/symbiosis_mcp_server.py`) - Exposes tools to LM Studio
2. **Optimal Memory System** (`tools/optimal_memory_system.py`) - **9-layer architecture**:
   - **Layer 1**: CMC (Canonical Memory Core) - Absolute truth
   - **Layer 2**: SMM (Semantic Mesh Memory) - Dynamic context
   - **Layer 2.5**: Neo4j Graph Layer - Structural relationships
   - **Layer 3**: DDE (Dynamic Domain Engine) - Auto-domain detection
   - **Layer 4**: AME (Adaptive Memory Enforcer) - Intelligent override
   - **Layer 5**: MLC (Meta-Learning Cortex) - User pattern learning
   - **Layer 6**: MIR (Memory Interference Regulator) - Noise/conflict detection
   - **Layer 7**: MCA (Memory Consistency Auditor) - Cross-layer validation
   - **Layer 8**: MCE (Memory Compression Engine) - Recursive summarization
   - **Plus**: EFC Theory Engine - Domain-specific cosmology reasoning
3. **Chat Memory** (`tools/chat_memory.py`) - Private memory with label isolation
4. **Orchestrator v2** (`tools/orchestrator_v2.py`) - Token-chunking + authority filtering
5. **Sync Tools**:
   - `sync_qdrant.py` - Orphan removal (Neo4j→Qdrant verification)
   - `sync_rag_to_neo4j.py` - Qdrant→Neo4j with dedup

### ❌ Gaps (What's Missing)

1. **No DDE in Orchestrator**: Ingestion lacks adaptive domain detection
2. **One-Directional Sync**: No bidirectional flow or cross-domain inference
3. **No Semantic Cross-Domain Matching**: Missing logical inference across domains
4. **No Event-Driven Sync**: API mutations don't trigger memory updates
5. **No GNN Inference Layer**: GNN embeddings not used for relation discovery

---

## Universal Memory Bridge Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  UNIVERSAL MEMORY BRIDGE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │  Qdrant    │←──→│   Neo4j    │←──→│    GNN     │       │
│  │ (Vectors)  │    │  (Graph)   │    │(Embeddings)│       │
│  └────────────┘    └────────────┘    └────────────┘       │
│         ↑                 ↑                  ↑             │
│         │                 │                  │             │
│         └─────────────────┴──────────────────┘             │
│                           │                                │
│                  ┌────────┴────────┐                       │
│                  │  Bridge Layer   │                       │
│                  │  (Orchestrator) │                       │
│                  └─────────────────┘                       │
│                           │                                │
│         ┌─────────────────┼─────────────────┐              │
│         ↓                 ↓                 ↓              │
│  ┌──────────┐      ┌──────────┐     ┌──────────┐         │
│  │Documents │      │   APIs   │     │  Chat    │         │
│  │  (raw)   │      │(mutations)│    │ (Memory) │         │
│  └──────────┘      └──────────┘     └──────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Key Features:
1. Bidirectional sync (all directions)
2. Adaptive domain detection (DDE integrated)
3. Semantic cross-domain matching (LLM + embeddings)
4. Logical inference (GNN-based relation discovery)
5. Event-driven updates (API mutations → sync)
```

---

## Implementation Plan

### Phase 1: Integrate DDE into Orchestrator
**Goal**: Auto-detect domains during ingestion

**Changes to `tools/orchestrator_v2.py`**:
```python
from dynamic_domain_engine import DynamicDomainEngine

# Initialize DDE
dde = DynamicDomainEngine()

# In ingest_pipeline():
def ingest_pipeline(text, input_type, source, metadata=None):
    # ... existing code ...
    
    # NEW: Classify domain
    domain_signal = dde.classify(clean_text)
    domain = domain_signal.domain
    confidence = domain_signal.confidence
    
    # Add to metadata
    metadata["domain"] = domain
    metadata["domain_confidence"] = confidence
    
    # Update chunk metadata
    for chunk in chunks:
        chunk.metadata["domain"] = domain
        chunk.metadata["domain_confidence"] = confidence
    
    # ... rest of ingestion ...
```

**Testing**:
```bash
python tools/orchestrator_v2.py --input "theory/formal/efc_master.tex" --type document
# Verify: chunks have domain="cosmology" in payload
```

---

### Phase 2: Bidirectional Neo4j↔Qdrant Sync
**Goal**: Keep Neo4j and Qdrant fully synchronized

**Create `tools/sync_universal.py`**:
```python
#!/usr/bin/env python3
"""
sync_universal.py - Universal Bidirectional Sync
================================================

Synchronizes:
1. Neo4j → Qdrant (missing vectors)
2. Qdrant → Neo4j (missing chunks)
3. Cross-domain semantic matching
4. GNN-based inference

Usage:
    python tools/sync_universal.py --mode full
    python tools/sync_universal.py --mode neo4j_to_qdrant
    python tools/sync_universal.py --mode qdrant_to_neo4j
    python tools/sync_universal.py --mode cross_domain
"""

from typing import List, Dict, Optional
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import numpy as np

class UniversalSync:
    def __init__(self):
        self.neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.dde = DynamicDomainEngine()
    
    def sync_neo4j_to_qdrant(self):
        """Find Neo4j chunks missing from Qdrant and add them."""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (c:Chunk)
                RETURN c.id AS chunk_id, c.text AS text, c.domain AS domain
            """)
            
            for record in result:
                chunk_id = record["chunk_id"]
                text = record["text"]
                domain = record["domain"]
                
                # Check if exists in Qdrant
                try:
                    self.qdrant.retrieve(collection_name="efc", ids=[chunk_id])
                except:
                    # Missing - add to Qdrant
                    vector = embed_text(text)
                    self.qdrant.upsert(
                        collection_name="efc",
                        points=[PointStruct(
                            id=chunk_id,
                            vector=vector,
                            payload={
                                "text": text,
                                "domain": domain,
                                "source": "neo4j_sync"
                            }
                        )]
                    )
                    print(f"✅ Added {chunk_id} to Qdrant")
    
    def sync_qdrant_to_neo4j(self):
        """Find Qdrant points missing from Neo4j and add them."""
        # ... (similar to sync_rag_to_neo4j.py but with domain awareness)
    
    def sync_cross_domain(self):
        """Find semantic relationships across domains."""
        # 1. Get all domains
        domains = self._get_all_domains()
        
        # 2. For each domain pair
        for domain_a in domains:
            for domain_b in domains:
                if domain_a >= domain_b:
                    continue
                
                # 3. Find semantically similar chunks across domains
                similarities = self._find_cross_domain_similarities(domain_a, domain_b)
                
                # 4. Create RELATED_TO relationships in Neo4j
                for sim in similarities:
                    if sim["score"] > 0.75:  # High confidence threshold
                        self._create_cross_domain_link(sim["chunk_a"], sim["chunk_b"], sim["score"])
    
    def _find_cross_domain_similarities(self, domain_a: str, domain_b: str) -> List[Dict]:
        """Use Qdrant + LLM to find semantic matches across domains."""
        # Scroll chunks from domain_a
        chunks_a = self.qdrant.scroll(
            collection_name="efc",
            scroll_filter=Filter(must=[FieldCondition(key="domain", match=MatchValue(value=domain_a))]),
            limit=100
        )[0]
        
        similarities = []
        for chunk_a in chunks_a:
            # Search for similar chunks in domain_b
            results = self.qdrant.search(
                collection_name="efc",
                query_vector=chunk_a.vector,
                query_filter=Filter(must=[FieldCondition(key="domain", match=MatchValue(value=domain_b))]),
                limit=3
            )
            
            for result in results:
                if result.score > 0.75:
                    similarities.append({
                        "chunk_a": chunk_a.id,
                        "chunk_b": result.id,
                        "score": result.score,
                        "domain_a": domain_a,
                        "domain_b": domain_b
                    })
        
        return similarities
    
    def _create_cross_domain_link(self, chunk_a_id: str, chunk_b_id: str, score: float):
        """Create RELATED_ACROSS_DOMAINS relationship in Neo4j."""
        with self.neo4j.session() as session:
            session.run("""
                MATCH (a:Chunk {id: $chunk_a})
                MATCH (b:Chunk {id: $chunk_b})
                MERGE (a)-[r:RELATED_ACROSS_DOMAINS]->(b)
                SET r.similarity = $score,
                    r.discovered = datetime()
            """, chunk_a=chunk_a_id, chunk_b=chunk_b_id, score=score)
```

---

### Phase 3: GNN Inference Layer
**Goal**: Use GNN embeddings to discover new relationships

**Create `tools/gnn_inference.py`**:
```python
#!/usr/bin/env python3
"""
gnn_inference.py - GNN-Based Relationship Discovery
===================================================

Uses GNN node embeddings to:
1. Discover implicit relationships between concepts
2. Predict missing links in knowledge graph
3. Cluster related concepts across domains

Integration:
- Reads GNN embeddings from symbiose_gnn_output/
- Compares with Neo4j graph structure
- Suggests new relationships based on embedding proximity
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase

class GNNInferenceEngine:
    def __init__(self, gnn_embeddings_path: str = "symbiose_gnn_output/node_embeddings.npy"):
        self.embeddings = np.load(gnn_embeddings_path)
        self.neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def discover_missing_links(self, threshold: float = 0.85):
        """Find concept pairs with high embedding similarity but no Neo4j relationship."""
        with self.neo4j.session() as session:
            # Get all concepts
            result = session.run("MATCH (c:Concept) RETURN c.id AS id, c.name AS name")
            concepts = [(r["id"], r["name"]) for r in result]
            
            # Compute pairwise similarities
            similarities = cosine_similarity(self.embeddings)
            
            # Find high-similarity pairs without existing relationships
            for i, (id_a, name_a) in enumerate(concepts):
                for j, (id_b, name_b) in enumerate(concepts):
                    if i >= j:
                        continue
                    
                    if similarities[i][j] > threshold:
                        # Check if relationship exists
                        rel_exists = session.run("""
                            MATCH (a:Concept {id: $id_a})
                            MATCH (b:Concept {id: $id_b})
                            RETURN EXISTS((a)-[]-(b)) AS exists
                        """, id_a=id_a, id_b=id_b).single()["exists"]
                        
                        if not rel_exists:
                            # Suggest new relationship
                            print(f"💡 Suggested link: {name_a} <-> {name_b} (sim={similarities[i][j]:.3f})")
                            
                            # Optionally auto-create
                            session.run("""
                                MATCH (a:Concept {id: $id_a})
                                MATCH (b:Concept {id: $id_b})
                                MERGE (a)-[r:INFERRED_RELATION]->(b)
                                SET r.similarity = $sim,
                                    r.method = 'gnn_inference',
                                    r.discovered = datetime()
                            """, id_a=id_a, id_b=id_b, sim=float(similarities[i][j]))
```

---

### Phase 4: Event-Driven API Sync
**Goal**: API mutations trigger memory updates

**Create `tools/event_sync.py`**:
```python
#!/usr/bin/env python3
"""
event_sync.py - Event-Driven Memory Sync
=========================================

Listens for API events and triggers sync:
1. Document uploaded → orchestrator_v2.py
2. Fact stored → optimal_memory_system.py
3. Chunk updated → sync_universal.py
4. Relationship created → gnn_inference.py

Integration:
- FastAPI middleware for event emission
- Redis pub/sub or in-memory queue
- Async workers process events
"""

from fastapi import FastAPI, Request
from typing import Dict, Any
import asyncio

class MemorySyncEventBus:
    def __init__(self):
        self.listeners = []
    
    def subscribe(self, listener):
        self.listeners.append(listener)
    
    async def emit(self, event: Dict[str, Any]):
        for listener in self.listeners:
            await listener(event)

# Global event bus
event_bus = MemorySyncEventBus()

# Event handlers
async def handle_document_event(event: Dict):
    if event["type"] == "document_uploaded":
        # Trigger orchestrator
        from orchestrator_v2 import ingest_pipeline
        result = ingest_pipeline(
            text=event["text"],
            input_type=event["doc_type"],
            source=event["source"]
        )
        print(f"✅ Document {event['doc_id']} ingested")

async def handle_fact_event(event: Dict):
    if event["type"] == "fact_stored":
        # Trigger cross-domain sync
        from sync_universal import UniversalSync
        sync = UniversalSync()
        sync.sync_cross_domain()
        print(f"✅ Cross-domain sync triggered")

# Subscribe handlers
event_bus.subscribe(handle_document_event)
event_bus.subscribe(handle_fact_event)

# FastAPI middleware
async def event_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Emit events based on endpoint
    if request.url.path.startswith("/store"):
        await event_bus.emit({
            "type": "fact_stored",
            "timestamp": datetime.now().isoformat()
        })
    
    return response
```

---

## Testing Strategy

### Unit Tests
```bash
# Test DDE integration
python -c "from tools.orchestrator_v2 import *; test_domain_classification()"

# Test bidirectional sync
python tools/sync_universal.py --mode full --dry-run

# Test GNN inference
python tools/gnn_inference.py --threshold 0.85 --dry-run

# Test event bus
python -m pytest tests/test_event_sync.py
```

### Integration Tests
```bash
# Full pipeline test
python tools/orchestrator_v2.py --input "theory/formal/efc_master.tex" --type document
python tools/sync_universal.py --mode cross_domain
python tools/gnn_inference.py --discover-links

# Verify in Neo4j
cypher-shell "MATCH (c:Chunk)-[r:RELATED_ACROSS_DOMAINS]->(d:Chunk) RETURN count(r)"
```

---

## Rollout Plan

### Week 1: Phase 1 (DDE Integration)
- [ ] Integrate `DynamicDomainEngine` into `orchestrator_v2.py`
- [ ] Test domain classification on existing documents
- [ ] Update ingestion API to expose domain metadata

### Week 2: Phase 2 (Bidirectional Sync)
- [ ] Implement `sync_universal.py`
- [ ] Test Neo4j→Qdrant sync
- [ ] Test Qdrant→Neo4j sync
- [ ] Test cross-domain matching

### Week 3: Phase 3 (GNN Inference)
- [ ] Implement `gnn_inference.py`
- [ ] Generate GNN embeddings for existing graph
- [ ] Discover missing links
- [ ] Validate with domain experts

### Week 4: Phase 4 (Event-Driven Sync)
- [ ] Implement `event_sync.py`
- [ ] Add FastAPI middleware
- [ ] Test event propagation
- [ ] Deploy to production

---

## Success Metrics

1. **Sync Completeness**: 100% of Neo4j chunks exist in Qdrant and vice versa
2. **Cross-Domain Links**: At least 50 high-confidence (>0.75) cross-domain relationships discovered
3. **GNN Inference**: At least 20 new concept relationships discovered via GNN
4. **Event Latency**: API mutations trigger sync within 5 seconds
5. **Domain Accuracy**: DDE classifies domains with >90% confidence

---

## References

- **Current Orchestrator**: `tools/orchestrator_v2.py`
- **Optimal Memory System**: `tools/optimal_memory_system.py`
- **Dynamic Domain Engine**: `tools/dynamic_domain_engine.py`
- **Existing Sync**: `tools/sync_qdrant.py`, `tools/sync_rag_to_neo4j.py`
- **MCP Server**: `mcp/symbiosis_mcp_server.py`

---

**Next Steps**: Start with Phase 1 (DDE integration) to establish domain-aware ingestion foundation.
