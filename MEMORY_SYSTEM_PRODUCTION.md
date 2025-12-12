# Symbiosis Memory System - Production Architecture

## 🎯 **ACTIVE COMPONENTS (December 2025)**

### **Core Memory System (9 Layers)**
Located in: `tools/optimal_memory_system.py`

1. **CMC** (Canonical Memory Core) - Absolute facts (`tools/canonical_memory_core.py`)
2. **SMM** (Semantic Mesh Memory) - Dynamic context (`tools/semantic_mesh_memory.py`)
3. **Neo4j Graph Layer** - Structural relationships (`tools/neo4j_graph_layer.py`)
4. **DDE** (Dynamic Domain Engine) - Domain detection (`tools/dynamic_domain_engine.py`)
5. **AME** (Adaptive Memory Enforcer) - Intelligent override (`tools/adaptive_memory_enforcer.py`)
6. **MLC** (Meta-Learning Cortex) - Pattern learning (`tools/meta_learning_cortex.py`)
7. **MIR** (Memory Interference Regulator) - Conflict detection
8. **MCA** (Memory Consistency Auditor) - Cross-layer validation
9. **MCE** (Memory Compression Engine) - Recursive compression

### **Chat Router**
- **Active:** `tools/symbiosis_router_v4.py`
- Orchestrates all 9 memory layers
- Used by API endpoint: `/chat/turn`

### **MCP Servers (LM Studio Integration)**

#### **Option 1: Minimal (Recommended)**
File: `mcp/symbiosis_mcp_server_v5_minimal.py`
- ONE tool: `symbiosis_chat_turn`
- Clean, simple, fast
- Returns pure `final_answer` (no formatting)

#### **Option 2: EFC Learning**
File: `mcp/symbiosis_mcp_server_v6_efc.py`
- Includes EFC pattern detection tools
- Meta-learning integration
- Returns pure `final_answer` (no formatting)

### **Backend API**
Located in: `apis/unified_api/`
- Main router: `routers/chat.py` (uses `symbiosis_router_v4`)
- Port: 8000
- Start: `python -m uvicorn main:app --port 8000`

---

## 📋 **LM STUDIO CONFIGURATION**

### Use v5 Minimal (Recommended):
```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": [
        "/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server_v5_minimal.py"
      ],
      "env": {
        "SYMBIOSIS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### OR use v6 EFC:
```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": [
        "/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server_v6_efc.py"
      ],
      "env": {
        "SYMBIOSIS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

---

## 🚀 **STARTUP SEQUENCE**

1. **Start Backend API:**
   ```bash
   cd apis/unified_api
   python -m uvicorn main:app --port 8000
   ```

2. **Configure LM Studio:**
   - Paste one of the configs above into LM Studio MCP settings
   - Restart LM Studio

3. **Test:**
   - Ask: "Hva heter jeg?"
   - Expected: "Du heter Morten"
   - Ask: "Hva heter barna mine?"
   - Expected: "Barna dine heter Joakim, Isak Andreas og Susanna"

---

## 🔧 **KEY FIXES (December 2025)**

### **Problem Solved:**
- ❌ `fact_type` mismatch (`"relation"` vs `"relationship"`)
- ❌ Domain filter too strict (missed facts in wrong domain)
- ❌ AME only returned first fact instead of synthesizing answer
- ❌ MCP returned formatting instead of pure answer

### **Solution:**
- ✅ Removed `fact_type` filter from all `query_facts()` calls
- ✅ Removed `domain` filter from `query_facts()` - semantic search handles it
- ✅ Added `_synthesize_from_facts()` in AME - uses LLM to create answer from ALL relevant facts
- ✅ MCP servers return ONLY `final_answer` (no formatting)

### **Result:**
- ✅ Memory works globally across all domains and fact types
- ✅ Semantic search finds relevant facts regardless of domain classification
- ✅ LLM synthesizes natural answers from multiple facts
- ✅ LM Studio receives clean, usable responses

---

## 📁 **ARCHIVE**

Old versions moved to: `archive/old_versions/`
- Old MCP servers (v3, v4)
- Old routers (v2, v3)
- Old memory models
- Test files

**Do not use archived versions - they have the bugs!**

---

## 📊 **MEMORY STORAGE**

### **Canonical Facts** (Qdrant collection: `canonical_facts`)
- user_name: Morten
- user_spouse: Elisabet
- user_children_count: 3
- user_child_1: Joakim
- user_child_2: Isak Andreas
- user_child_3: Susanna
- assistant_name: Opus

### **Add More Facts:**
```python
from tools.optimal_memory_system import OptimalMemorySystem

memory = OptimalMemorySystem()

memory.store_fact(
    key="user_preference_music",
    value="Jazz",
    domain="preferences",
    fact_type="preference",
    authority="LONGTERM",
    text="Brukeren liker jazz-musikk"
)
```

---

## 🎯 **PRODUCTION READY**

All 9 memory layers active and tested. Global fix for all domains and fact types.
Ready for production use with LM Studio via MCP.
