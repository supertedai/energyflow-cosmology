# Backend Proxy Architecture (v4.0)

## 🎯 Konsept

**ALL logikk kjører i backend** (FastAPI). MCP server er bare en tynn proxy.

```
LM Studio
    ↓
MCP Server (v4 - thin proxy)
    ↓
Backend API (FastAPI localhost:8000)
    ↓
[Memory, Domain Engine, GNN, Neo4j, Qdrant]
```

## 📋 Arkitektur

### Før (v3.0):
```
MCP Server (Python)
├── Importerer symbiosis_router_v3
├── Importerer domain_engine_v2
├── Importerer chat_memory
├── Importerer gnn_scoring
└── Kjører ALL logikk lokalt
```

### Nå (v4.0):
```
MCP Server (Thin Proxy)
└── Kaller backend API endpoints

Backend API (FastAPI)
├── POST /chat/turn → symbiosis_router_v3
├── GET /rag/search → Qdrant
├── POST /neo4j/q → Neo4j
└── GET /graph-rag/search → Hybrid
```

## 🚀 Setup

### 1. Start Backend API

```bash
cd apis/unified_api
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Test backend:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}

curl http://localhost:8000/chat/health
# Should return chat router status
```

### 2. Update LM Studio Config

```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": [
        "/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server_v4_backend_proxy.py"
      ],
      "env": {
        "SYMBIOSIS_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### 3. Restart MCP in LM Studio

Settings → MCP → Restart server

### 4. Verify

Tools should show:
1. `symbiosis_chat_turn`
2. `symbiosis_vector_search`
3. `symbiosis_graph_query`
4. `symbiosis_hybrid_search`
5. `symbiosis_get_concepts`
6. `mcp_version`

## 🧪 Testing

### Test Backend Directly

```bash
# Test unified chat endpoint
curl -X POST http://localhost:8000/chat/turn \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Hva heter du?",
    "assistant_draft": "Jeg heter Qwen"
  }'

# Should return:
{
  "final_answer": "Jeg heter Opus",
  "was_overridden": true,
  "enforcement": {
    "was_overridden": true,
    "reason": "Memory says Opus"
  },
  ...
}
```

### Test via LM Studio

```
User: "Hva heter du?"

LLM calls: symbiosis_chat_turn(
  user_message="Hva heter du?",
  assistant_draft="Jeg heter Qwen"
)

MCP proxies to: POST http://localhost:8000/chat/turn

Backend processes:
1. Domain analysis
2. Memory retrieval
3. Memory enforcement ← OVERRIDES to "Opus"
4. GNN scoring
5. Storage
6. Returns corrected answer

LLM receives: "Jeg heter Opus" ✅
```

## 📊 Fordeler

| Aspekt | v3.0 (Local) | v4.0 (Backend Proxy) |
|--------|--------------|----------------------|
| **Logic Location** | MCP server | Backend API |
| **Scaling** | Per MCP instance | Centralized |
| **Updates** | Restart MCP | Hot reload backend |
| **Monitoring** | Terminal logs | API logs + metrics |
| **Testing** | Hard (via MCP) | Easy (curl/Postman) |
| **Deployment** | Complex | Standard FastAPI |
| **Multi-client** | One MCP | Many clients → 1 backend |

## 🔧 API Endpoints

### Chat Router
- `POST /chat/turn` - Unified chat handler
- `GET /chat/health` - Chat router health

### Knowledge Base (Existing)
- `GET /rag/search` - Vector search
- `POST /neo4j/q` - Cypher queries
- `GET /graph-rag/search` - Hybrid search

### System
- `GET /health` - Backend health

## 📝 Files Created/Modified

### New Files:
1. `apis/unified_api/routers/chat.py` - Chat router with /turn endpoint
2. `mcp/symbiosis_mcp_server_v4_backend_proxy.py` - Thin MCP proxy

### Modified Files:
1. `apis/unified_api/main.py` - Added chat router

### Configuration:
Update `lm-studio-config.json` to use v4 server

## 🎯 Migration Path

### From v3.0 to v4.0:

**v3.0 (Local Logic):**
```python
# MCP calls directly:
from symbiosis_router_v3 import handle_chat_turn
result = handle_chat_turn(...)
```

**v4.0 (Backend Proxy):**
```python
# MCP calls API:
response = await client.post(
    "http://localhost:8000/chat/turn",
    json={...}
)
```

**Same functionality, different architecture!**

## ✅ Verification

After starting backend + MCP:

1. [ ] Backend running on :8000
2. [ ] `curl http://localhost:8000/health` → ok
3. [ ] `curl http://localhost:8000/chat/health` → ok
4. [ ] LM Studio MCP restarted
5. [ ] 6 tools visible in LM Studio
6. [ ] Test: "Hva heter du?" → "Jeg heter Opus"

## 🔄 Benefits of Backend Architecture

1. **Centralized Logic**: All processing in one place
2. **Easy Updates**: Restart API (not MCP)
3. **Better Monitoring**: API logs, metrics, traces
4. **Multi-Client**: Multiple MCP instances → 1 backend
5. **Standard Deploy**: Docker, K8s, serverless
6. **Easy Testing**: curl/Postman/pytest
7. **Scalable**: Load balance backend
8. **Hot Reload**: FastAPI auto-reload during dev

---

**Version**: 4.0.0  
**Architecture**: Backend Proxy  
**Backend**: FastAPI (localhost:8000)  
**MCP**: Thin proxy forwarding to APIs
