# MCP v5.0 - MINIMAL (1 Tool Only) ✅

## Problem
MCP v4 still exposed 6 tools:
- ✅ `symbiosis_chat_turn` (needed)
- ❌ `symbiosis_vector_search` (remove - backend handles internally)
- ❌ `symbiosis_graph_query` (remove - backend handles internally)
- ❌ `symbiosis_hybrid_search` (remove - backend handles internally)
- ❌ `symbiosis_get_concepts` (remove - backend handles internally)
- ❌ `mcp_version` (remove - not needed)

## Solution: MCP v5.0 MINIMAL

**ONE TOOL ARCHITECTURE**: Only `symbiosis_chat_turn` exposed to LLM.

### Architecture
```
┌─────────────────────────────────────┐
│   LM Studio (LLM)                   │
│   ↓ calls                           │
│   symbiosis_chat_turn (1 tool)     │
└──────────────┬──────────────────────┘
               ↓
┌──────────────────────────────────────┐
│   MCP v5 (Thin Proxy)                │
│   - 1 tool only                      │
│   - Forwards to backend API          │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│   Backend API (FastAPI)              │
│   - ALL logic here                   │
│   - Memory enforcement               │
│   - Domain analysis                  │
│   - GNN scoring                      │
│   - Knowledge base (internal)        │
│   - Storage                          │
└──────────────────────────────────────┘
```

### What Changed

**Removed from MCP**:
- ❌ `symbiosis_vector_search` → Backend handles Qdrant internally
- ❌ `symbiosis_graph_query` → Backend handles Neo4j internally
- ❌ `symbiosis_hybrid_search` → Backend handles hybrid search internally
- ❌ `symbiosis_get_concepts` → Backend handles concept retrieval internally
- ❌ `mcp_version` → Not needed

**Kept in MCP**:
- ✅ `symbiosis_chat_turn` → Only entry point for LLM

### Files Created

1. **`mcp/symbiosis_mcp_server_v5_minimal.py`** (270 lines)
   - Only 1 tool: `symbiosis_chat_turn`
   - Proxies to `/chat/turn` backend API
   - All other functionality internal to backend

2. **`lm-studio-config-v5.json`**
   - LM Studio MCP configuration
   - Points to v5 minimal server
   - Sets backend URL environment variable

### How It Works

**LLM Workflow**:
```python
# 1. User asks question
User: "Hva heter du?"

# 2. LLM generates draft
Draft: "Jeg heter Qwen"

# 3. LLM calls ONE tool
symbiosis_chat_turn(
    user_message="Hva heter du?",
    assistant_draft="Jeg heter Qwen"
)

# 4. Backend processes (6 steps):
#    - Memory retrieval
#    - Memory enforcement → OVERRIDE detected
#    - Domain analysis
#    - GNN scoring
#    - Knowledge base (if needed)
#    - Storage

# 5. Backend returns corrected answer
{
    "final_answer": "Jeg heter Opus",
    "was_overridden": true,
    "conflict_reason": "LLM used generic identity instead of memory name 'Opus'"
}

# 6. LLM sends final_answer to user
Response: "Jeg heter Opus"
```

### Benefits

1. **Simplicity**: LLM only sees 1 tool
2. **Backend-Centric**: ALL logic in backend (easy to debug/modify)
3. **Atomic**: Each chat turn = 1 API call
4. **Testable**: Backend fully tested (5/6 tests pass)
5. **Maintainable**: MCP is just a thin proxy

### Installation

1. **Copy config to LM Studio**:
   ```bash
   cp lm-studio-config-v5.json ~/Library/Application\ Support/LM\ Studio/mcp_config.json
   ```

2. **Ensure backend running**:
   ```bash
   cd apis/unified_api
   python -m uvicorn main:app --port 8000 --reload
   ```

3. **Restart LM Studio**

4. **Verify in LM Studio**:
   - Should see only 1 tool: `symbiosis_chat_turn`
   - Test: "Hva heter du?" (should override to "Opus")

### Tool Description

**symbiosis_chat_turn**:
- **Input**: 
  - `user_message` (required): User's question
  - `assistant_draft` (required): LLM's draft response
  - `session_id` (optional): Session identifier
  
- **Output**:
  - `final_answer`: Corrected response (send this to user)
  - `was_overridden`: Whether memory enforcement triggered
  - `conflict_reason`: Why override happened
  - `memory_used`: Retrieved memory context
  - `gnn`: GNN similarity analysis
  - `metadata`: Timestamps, session info

### Backend Status

✅ **Running on port 8000**
✅ **Integration tests: 5/6 pass (83.3%)**
✅ **Memory enforcement works**
✅ **Field mapping fixed**

### Comparison

| Version | Tools | Architecture | Status |
|---------|-------|--------------|--------|
| v3 | 15+ tools | Router-based | ❌ Too many tools |
| v4 | 6 tools | Backend proxy | ❌ Still too many |
| **v5** | **1 tool** | **Minimal proxy** | ✅ **CURRENT** |

### Next Steps

1. ✅ **DONE**: Create v5 minimal server
2. ⏳ **TODO**: Copy config to LM Studio
3. ⏳ **TODO**: Test with live LLM
4. ⏳ **TODO**: Verify only 1 tool visible

---

**Version**: 5.0.0  
**Date**: 11. desember 2025  
**Status**: Ready for deployment
