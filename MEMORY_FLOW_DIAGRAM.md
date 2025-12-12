# 🧠 Memory Flow Diagram - Complete System Architecture

## 📊 System Overview

```
LM Studio (User Interface)
    ↓
MCP Server (v6_efc)
    ↓
Backend API (FastAPI port 8000)
    ↓
Symbiosis Router V4 (Orchestrator)
    ↓
9-Layer Optimal Memory System
    ↓
Databases (Qdrant + Neo4j)
```

---

## 🎯 Complete Data Flow (Step-by-Step)

### 1️⃣ USER INPUT → MCP SERVER
```
User types in LM Studio chat
    ↓
LM Studio Config: lm-studio-config-v6-efc.json
    ├─ Points to: mcp/symbiosis_mcp_server_v6_efc.py
    ├─ Environment: SYMBIOSIS_API_URL=http://localhost:8000
    └─ Tools: efc_record_feedback (Layer 9 learning)
    ↓
MCP Server Starts
    Location: mcp/symbiosis_mcp_server_v6_efc.py
    Port: stdio (MCP protocol)
    Function: Bridge LM Studio ↔ Backend
```

### 2️⃣ MCP → BACKEND API
```
MCP sends HTTP POST request
    ↓
URL: http://localhost:8000/chat/turn
    ↓
Payload:
    {
        "user_message": "Hei",
        "assistant_draft": "Hei! Hvordan kan jeg hjelpe deg?",
        "session_id": "lm_studio_session_123"
    }
    ↓
Backend Entry Point: apis/unified_api/main.py
    ├─ FastAPI app initialization
    ├─ Imports all routers
    └─ Runs on port 8000
```

### 3️⃣ BACKEND ROUTING
```
main.py receives request
    ↓
Routes to: apis/unified_api/routers/chat.py
    ↓
Endpoint: POST /chat/turn
    ↓
Function: handle_turn()
    ├─ Validates input
    ├─ Extracts user_message, assistant_draft, session_id
    └─ Calls: symbiosis_router_v4.handle_chat_turn()
```

### 4️⃣ SYMBIOSIS ROUTER V4 (ORCHESTRATOR)
```
Location: tools/symbiosis_router_v4.py
Function: Master orchestrator for 9-layer memory system

Flow:
    ┌─────────────────────────────────────┐
    │ handle_chat_turn()                  │
    │  - user_message: "Hei"              │
    │  - assistant_draft: "Hei! ..."      │
    │  - session_id: "lm_studio_..."      │
    └─────────────────────────────────────┘
            ↓
    Runtime Sequence (per chat turn):
    1. Layer 4 (DDE) → Analyze input & decide which layers to activate
    2. Read layers (1-3) → Fetch relevant memory (on demand)
    3. Layer 5 (AME) → Fact enforcement & contradiction check
    4. Layer 6 (MLC) → Pattern learning (if applicable)
    5. Maintenance layers (7-9) → Runs on writes/updates, not every turn
```

---

## 🏗️ 9-LAYER OPTIMAL MEMORY SYSTEM

### **Runtime Flow (per chat turn):**
```
1. Layer 4 (DDE) → Routing & decision
2. Layers 1-3 → Read memory (on-demand)
3. Layer 5 (AME) → Fact enforcement
4. Layer 6 (MLC) → Pattern learning (if applicable)
5. Layers 7-9 → Maintenance (write-time only, not per turn)
```

---

### **Layer 4: Dynamic Decision Engine (DDE)** 🎯 RUNS FIRST
```
File: tools/dynamic_decision_engine.py
Purpose: Routing logic (which layers to activate)
When: Beginning of every chat turn

Methods:
    - analyze_input(user_message, assistant_draft)
    - decide_layers(analysis_result)
    - get_routing_decision(user_message)

Logic:
    IF query contains identity words → activate Layer 5 (AME)
    IF query is philosophical → activate Layer 3 (Neo4j)
    IF query needs context → activate Layer 2 (SMM)
    ALWAYS activate Layer 1 (CMC) for fact checking

Output:
    routing_decision = {
        "activated_layers": [1, 3, 5],
        "decision_reason": "identity + EFC-domain",
        "contradiction_check": true
    }
```

---

## 📖 READ LAYERS (On-Demand Memory Retrieval)

### **Layer 1: Canonical Memory Core (CMC)**
```
File: tools/canonical_memory_core.py
Purpose: Ground truth facts (identity, family, preferences)

Methods:
    - set_fact(domain, key, value, confidence)
    - get_fact(domain, key)
    - get_facts_for_domain(domain)
    - query_related_facts(query_text)

Storage:
    Qdrant collection: "canonical_facts"
    Metadata: {domain, key, value, confidence, timestamp}

Example Facts:
    domain="identity" key="name" value="Brukeren heter Morten"
    domain="family" key="children" value="3 barn: Joakim, Isak Andreas, Susanna"
```

### **Layer 2: Semantic Mesh Memory (SMM)**
```
File: tools/semantic_mesh_memory.py
Purpose: Conversational context + semantic patterns

Methods:
    - store_turn(user_msg, assistant_msg, session_id, metadata)
    - retrieve_similar_conversations(query, limit, threshold)
    - get_session_history(session_id, limit)

Storage:
    Qdrant collection: "semantic_mesh"
    Metadata: {session_id, role, timestamp, turn_number}

Use Case:
    "Remember conversation about EFC theory from yesterday"
```

### **Layer 3: Neo4j Graph Memory**
```
File: tools/neo4j_graph_memory.py
Purpose: Knowledge graph (concepts, relationships, ontology)

Methods:
    - store_concept(name, description, properties)
    - link_concepts(from_concept, to_concept, relation_type)
    - query_graph(cypher_query)
    - find_related_concepts(concept_name, max_depth)

Storage:
    Neo4j database
    Nodes: Concept, Document, Chunk
    Relationships: SUPPORTS, CONSTRAINS, PART_OF, DERIVES_FROM

Example:
    (Entropy)-[:SUPPORTS]->(Second Law)
    (EFC Theory)-[:DERIVES_FROM]->(Cosmology)
```

---

## ✅ ENFORCEMENT LAYER

### **Layer 5: Adaptive Memory Enforcer (AME)** ⭐ CRITICAL
```
File: tools/adaptive_memory_enforcer.py
Purpose: Intelligent fact correction with LLM-based contradiction detection

Methods:
    - enforce_memory(user_msg, assistant_draft, session_id)
        ↓
    - _should_check_facts(user_msg, assistant_draft)
        ├─ Identity questions? → YES
        ├─ Factual claims? → YES
        └─ Casual chat? → NO (skip)
        ↓
    - _retrieve_canonical_facts(query_text)
        └─ Searches Layer 1 (CMC) for relevant facts
        ↓
    - _decide(assistant_draft, canonical_facts)
        ├─ Calls _contradicts() for each fact
        ├─ IF contradiction → OVERRIDE path
        └─ IF no contradiction → TRUST_LLM path
        ↓
    - _contradicts(draft, canonical_fact) ⭐ LLM-BASED
        ├─ Sends prompt to local LM Studio
        ├─ URL: http://localhost:1234/v1/chat/completions
        ├─ Model: <local-model>
        ├─ Prompt: "Does this draft contradict this fact?"
        ├─ Returns: {contradicts: true/false, explanation: "..."}
        └─ Fallback: Pattern matching (numbers, names, negations)

Decision Paths:
    1. OVERRIDE:
        - Contradiction detected by LLM
        - Return canonical fact verbatim
        - Example: "Jeg vet ikke" → "Brukeren heter Morten"
    
    2. TRUST_LLM:
        - No contradiction detected
        - Use LLM's draft as-is
        - NO augmentation (removed AUGMENT path completely!)

Example Flow:
    User: "Hva heter jeg?"
    Draft: "Jeg vet ikke"
    Canonical: "Brukeren heter Morten"
    LLM Check: "YES, these contradict"
    Decision: OVERRIDE
    Output: "Brukeren heter Morten"

Why LLM-Based?
    - Understands semantic contradiction (not just keyword matching)
    - Detects: numbers, names, negations, implicit contradictions
    - Fallback: Pattern matching if LLM fails
```

---

## 🧠 META LAYER (Background/Periodic)

### **Layer 6: Meta-Learning Context (MLC)**
```
File: tools/meta_learning_context.py
Purpose: Cross-domain pattern learning (EFC Layer 9)
When: Activated when sufficient signal exists for pattern detection (not every turn)

Methods:
    - record_pattern(pattern_type, context, domains)
    - detect_universal_patterns(threshold=3)
    - augment_response(response, detected_patterns)

Storage:
    JSON: meta_patterns.json
    Qdrant collection: "meta_patterns"

Example:
    Pattern: "Conservation principles apply universally"
    Domains: ["physics", "information_theory", "biology"]
    Status: Universal (≥3 domains)

Note: This is a meta-layer that runs periodically, not inline with every chat turn.
```

---

## 🔧 MAINTENANCE LAYERS (Write-Time Only)

**Important**: Layers 7-9 run when facts are written/updated, NOT on every chat turn.
They maintain memory integrity, confidence, and causal relationships.

### **Layer 7: Memory Integrity Regulator (MIR)**
```
File: tools/memory_integrity_regulator.py
Purpose: Conflict detection + resolution
When: Triggered when new facts are added or updated

Methods:
    - check_conflicts(new_fact, existing_facts)
    - resolve_conflict(fact_a, fact_b)
    - audit_memory_consistency()

Logic:
    IF fact_new.value != fact_existing.value:
        IF fact_new.confidence > fact_existing.confidence:
            UPDATE fact
        ELSE:
            FLAG conflict for human review
```

### **Layer 8: Memory Confidence Adjuster (MCA)**
```
File: tools/memory_confidence_adjuster.py
Purpose: Dynamic confidence scoring
When: Runs on fact usage, updates, and periodic aging

Methods:
    - adjust_confidence(fact, feedback)
    - decay_old_facts(time_threshold)
    - boost_frequently_used(fact)

Example:
    Fact: "User prefers dark mode"
    Initial confidence: 0.8
    After 5 successful uses: 0.95
    After 30 days unused: 0.7 (decay)
```

### **Layer 9: Memory Causality Engine (MCE)**
```
File: tools/memory_causality_engine.py
Purpose: Track fact dependencies + causal chains
When: Triggered when facts with dependencies are modified or deleted

Methods:
    - link_causality(cause_fact, effect_fact)
    - trace_causal_chain(fact_id)
    - invalidate_dependent_facts(root_fact_id)

Example:
    IF fact="User lives in Oslo" is deleted
    THEN invalidate dependent facts:
        - "User's timezone is CET"
        - "User speaks Norwegian"
```

---

## 🔄 Complete Request/Response Flow

### Example 1: Simple Greeting (No Memory Needed)
```
1. User: "Hei"
2. LM Studio → MCP v6 → Backend (8000) → Router v4
3. Router v4 calls:
   ├─ Layer 4 (DDE): "No fact checking needed"
   └─ Layer 5 (AME): _should_check_facts() → FALSE
4. Router returns: assistant_draft unchanged
5. Backend → MCP → LM Studio
6. Output: "Hei! Hvordan kan jeg hjelpe deg?"
```

### Example 2: Identity Question (Memory Override)
```
1. User: "Hva heter jeg?"
2. LM Studio → MCP v6 → Backend (8000) → Router v4
3. Router v4 calls:
   ├─ Layer 4 (DDE): "Identity query detected"
   ├─ Layer 5 (AME): _should_check_facts() → TRUE
   │   ├─ _retrieve_canonical_facts("identity name")
   │   │   └─ Layer 1 (CMC): Returns "Brukeren heter Morten"
   │   ├─ _decide(draft="Jeg vet ikke", facts=["Morten"])
   │   │   ├─ _contradicts() calls LLM at localhost:1234
   │   │   │   Prompt: "Draft: 'Jeg vet ikke' vs Fact: 'Morten'"
   │   │   │   LLM: {contradicts: true}
   │   │   └─ Decision: OVERRIDE
   │   └─ Returns: "Brukeren heter Morten"
   └─ Layer 7 (MIR): Validates no conflicts
4. Backend → MCP → LM Studio
5. Output: "Brukeren heter Morten"
```

### Example 3: EFC Theory Question (Graph + Learning)
```
1. User: "Hva er entropiprinsippet i EFC?"
2. LM Studio → MCP v6 → Backend (8000) → Router v4
3. Router v4 calls:
   ├─ Layer 4 (DDE): "EFC theory query detected"
   ├─ Layer 3 (Neo4j): Query for (Entropy)-[:PART_OF]->(EFC)
   │   └─ Returns: Graph structure + related concepts
   ├─ Layer 2 (SMM): Retrieve similar past conversations
   │   └─ Returns: Previous entropy discussions
   ├─ Layer 6 (MLC): Check for universal patterns
   │   └─ Detects: "Conservation principles" pattern
   └─ Layer 5 (AME): No identity facts → TRUST_LLM
4. Backend → MCP → LM Studio
5. Output: "I EFC representerer entropi..." (enriched with context)
6. MCP v6 tool: efc_record_feedback() → stores pattern in Layer 6
```

---

## 📁 File Structure Reference

### Core Memory Modules (i rekkefølge)

**🎯 Orchestrator:**
1. [`tools/symbiosis_router_v4.py`](tools/symbiosis_router_v4.py) - Master orchestrator (kaller alle 9 lag)

**🧠 9-Layer Memory System:**
2. [`tools/canonical_memory_core.py`](tools/canonical_memory_core.py) - **Layer 1**: Ground truth facts
3. [`tools/semantic_mesh_memory.py`](tools/semantic_mesh_memory.py) - **Layer 2**: Conversational context
4. [`tools/neo4j_graph_memory.py`](tools/neo4j_graph_memory.py) - **Layer 3**: Knowledge graph
5. [`tools/dynamic_decision_engine.py`](tools/dynamic_decision_engine.py) - **Layer 4**: Routing logic
6. [`tools/adaptive_memory_enforcer.py`](tools/adaptive_memory_enforcer.py) - **Layer 5**: Fact enforcement ⭐ CRITICAL
7. [`tools/meta_learning_context.py`](tools/meta_learning_context.py) - **Layer 6**: EFC pattern learning
8. [`tools/memory_integrity_regulator.py`](tools/memory_integrity_regulator.py) - **Layer 7**: Conflict resolution
9. [`tools/memory_confidence_adjuster.py`](tools/memory_confidence_adjuster.py) - **Layer 8**: Confidence scoring
10. [`tools/memory_causality_engine.py`](tools/memory_causality_engine.py) - **Layer 9**: Causal dependencies

### MCP Servers (LM Studio Integration)

**🟢 ACTIVE:**
- [`mcp/symbiosis_mcp_server_v6_efc.py`](mcp/symbiosis_mcp_server_v6_efc.py) - Full EFC + 9 layers (PRODUCTION)

**📦 Alternative:**
- [`mcp/symbiosis_mcp_server_v5_minimal.py`](mcp/symbiosis_mcp_server_v5_minimal.py) - Simple version (1 tool only)

**🗄️ ARCHIVED:**
- [`mcp/symbiosis_mcp_server.py`](mcp/symbiosis_mcp_server.py) - v3 (old)
- [`mcp/symbiosis_mcp_server_v2.py`](mcp/symbiosis_mcp_server_v2.py) - v2
- [`mcp/symbiosis_mcp_server_v4.py`](mcp/symbiosis_mcp_server_v4.py) - v4

### Backend API (FastAPI port 8000)

**Entry Point:**
- [`apis/unified_api/main.py`](apis/unified_api/main.py) - FastAPI app initialization

**Routers:**
- [`apis/unified_api/routers/chat.py`](apis/unified_api/routers/chat.py) - POST /chat/turn endpoint
- [`apis/unified_api/routers/efc_meta_learning.py`](apis/unified_api/routers/efc_meta_learning.py) - EFC learning endpoints
- [`apis/unified_api/routers/msty_context.py`](apis/unified_api/routers/msty_context.py) - Context management

### Configuration Files

**LM Studio MCP Config:**
- [`lm-studio-config-v6-efc.json`](lm-studio-config-v6-efc.json) - 🟢 ACTIVE: Full system
- [`lm-studio-config-v5.json`](lm-studio-config-v5.json) - Minimal version

**Environment & Documentation:**
- `.env` - Database credentials (NEVER commit!)
- [`VERSION_CONTROL.md`](VERSION_CONTROL.md) - Complete version documentation
- [`MEMORY_FLOW_DIAGRAM.md`](MEMORY_FLOW_DIAGRAM.md) - This file (you are here)

### Supporting Tools & Scripts

**Ingestion Pipeline:**
- [`tools/orchestrator_v2.py`](tools/orchestrator_v2.py) - Data ingestion orchestrator
- [`tools/authority_filter.py`](tools/authority_filter.py) - Authoritative source validation
- [`tools/batch_ingest.py`](tools/batch_ingest.py) - Batch document processing

**EFC Pattern Learning:**
- [`tools/efc_pattern_learner.py`](tools/efc_pattern_learner.py) - Cross-domain pattern detection
- [`tools/chat_intention_bridge.py`](tools/chat_intention_bridge.py) - Chat → EFC learning bridge

**Testing & Monitoring:**
- [`test_theory_auth.py`](test_theory_auth.py) - Test authority filter
- [`test_backend_chat.py`](test_backend_chat.py) - Test backend chat API
- [`test_memory_system.py`](test_memory_system.py) - Test memory layers
- [`cleanup_test_databases.py`](cleanup_test_databases.py) - Clean test collections
- [`monitor_ingest.sh`](monitor_ingest.sh) - Monitor ingestion progress
- [`monitor_augmentation.sh`](monitor_augmentation.sh) - Monitor augmentation logs

---

## 🔧 System Dependencies

### Databases
```
Qdrant (Vector Database)
├── URL: From .env QDRANT_URL
├── Collections:
│   ├── efc (9,588 vectors) - Production EFC data
│   ├── canonical_facts (0 vectors) - Layer 1 storage
│   └── semantic_mesh (0 vectors) - Layer 2 storage
└── API Key: From .env QDRANT_API_KEY

Neo4j (Graph Database)
├── URL: From .env NEO4J_URI
├── Nodes: 13,648 production nodes
├── Labels: Concept, Document, Chunk
├── Relationships: SUPPORTS, CONSTRAINS, PART_OF
└── Credentials: .env NEO4J_USER / NEO4J_PASSWORD
```

### LLM Services
```
Local LM Studio
├── API: http://localhost:1234/v1/chat/completions
├── Used by: adaptive_memory_enforcer.py (_contradicts method)
├── Purpose: Semantic contradiction detection
└── Model: User's selected model (e.g., llama-3.3-70b-instruct)

OpenAI Client
├── Configured in: adaptive_memory_enforcer.py
├── Base URL: http://localhost:1234/v1
├── API Key: "lm-studio" (placeholder)
└── Fallback: Pattern matching if LLM fails
```

---

## 🚀 Startup Sequence

### 1. Start Databases (Already Running)
```bash
# Qdrant - cloud hosted (always on)
# Neo4j - check status:
curl http://localhost:7474/browser/

# If Neo4j down:
neo4j start
```

### 2. Start Backend API
```bash
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
cd apis/unified_api
python -m uvicorn main:app --port 8000 --reload &

# Verify:
curl http://localhost:8000/docs
```

### 3. Configure LM Studio MCP
```
1. Open LM Studio
2. Go to: Developer → MCP Settings
3. Load config: lm-studio-config-v6-efc.json
4. Verify SYMBIOSIS_API_URL=http://localhost:8000
5. Restart LM Studio (critical!)
```

### 4. Verify MCP Connection
```bash
# Check MCP server logs in LM Studio
# Should see: "MCP server v6_efc started successfully"
# Should see: Tool registered: efc_record_feedback
```

### 5. Test Complete Flow
```
In LM Studio chat:
1. "Hei" → Should return greeting (no augmentation)
2. "Hva heter jeg?" → Should override with canonical fact
3. "Hva er EFC?" → Should query graph + learning patterns
```

---

## 🐛 Troubleshooting Flow

### Issue: "Hei" returns identity facts
```
Problem: AUGMENT logic still active
Solution: Already fixed - adaptive_memory_enforcer.py AUGMENT removed
Verify: Check line 220-325 in adaptive_memory_enforcer.py
```

### Issue: Backend not responding
```
Problem: Wrong startup command
Fix:
    ❌ uvicorn tools.symbiosis_router_v4:app
    ✅ cd apis/unified_api && uvicorn main:app --port 8000
```

### Issue: MCP not connecting
```
Problem: LM Studio not restarted after config change
Fix:
    1. Quit LM Studio completely
    2. Restart LM Studio
    3. Check Developer → MCP Settings
    4. Verify v6_efc config loaded
```

### Issue: Contradiction detection failing
```
Problem: LM Studio not running on port 1234
Fix:
    1. Start LM Studio
    2. Load a model
    3. Check localhost:1234/v1/models
    4. Fallback: Pattern matching will activate
```

---

## 📊 Memory System Statistics

### Current State (After Cleanup)
```
Qdrant:
├── efc: 9,588 vectors (production)
├── canonical_facts: 0 vectors (clean)
├── semantic_mesh: 0 vectors (clean)
└── private: 0 vectors (deleted)

Neo4j:
├── Production nodes: 13,648
├── Private nodes: 0 (deleted)
├── Concepts: ~5,000
├── Documents: ~1,500
└── Relationships: ~8,000

Layer Status:
✅ All 9 layers operational
✅ No AUGMENT pollution
✅ LLM contradiction detection active
✅ Pattern matching fallback ready
```

---

## 🎯 Next Steps

### Pending Implementation
1. **Multi-Fact Synthesis** (Layer 5 enhancement)
   - Query: "Hvem er barna mine?"
   - Current: Returns first fact only
   - Needed: Merge related facts intelligently

2. **EFC Pattern Learning** (Layer 6 testing)
   - Use efc_record_feedback tool in LM Studio
   - Test cross-domain pattern detection
   - Verify universal patterns (≥3 domains)

3. **Production Deployment**
   - Create .env.example template
   - Document deployment checklist
   - Test with fresh Python environment

---

## 📚 Reference Documentation

- **System Overview**: START-HERE.md
- **Version Control**: VERSION_CONTROL.md
- **Ingestion Pipeline**: tools/INGESTION_PIPELINE.md
- **API Documentation**: api/README_API.md
- **EFC Theory**: theory/formal/efc_master.pdf
- **Meta Layer**: meta/README.md

---

**Last Updated**: 2025-12-12  
**System Status**: 🟢 Operational - Ready for production testing  
**Private Data**: ✅ Fully cleaned (0 vectors, 0 nodes)
