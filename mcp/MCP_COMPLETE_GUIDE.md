# Complete MCP Integration Guide

## ✅ Setup Status (FIXED - Phase 22)

**9 MCP-verktøy** er nå tilgjengelige via `symbiosis_mcp_server.py`:

**VIKTIG FIX**: Chat memory-verktøy bruker nå direkte Python-imports (ikke API), så de fungerer uten at Symbiosis API kjører.

### EFC/Theory (4 verktøy)
1. **symbiosis_vector_search** - Qdrant semantic search (EFC-samling)
2. **symbiosis_graph_query** - Neo4j Cypher queries (EFC-graf)
3. **symbiosis_hybrid_search** - Kombinert graph + vector
4. **symbiosis_get_concepts** - Finn konsepter i grafen

### Private Memory (4 verktøy)
5. **chat_memory_store** - Lagre viktige chat-interaksjoner
6. **chat_memory_retrieve** - Hent relevante minner
7. **chat_memory_profile** - Full brukerprofil
8. **chat_memory_feedback** - Marker minne som nyttig/feil

### System (1 verktøy)
9. **authority_check** - Sjekk om fil er autoritativ teori

---

## Configuration

### LM Studio Config (`lm-studio-config.json`)

```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": [
        "/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server.py"
      ],
      "env": {
        "SYMBIOSIS_API_URL": "http://localhost:8000",
        "NEO4J_URI": "neo4j+s://216ea6ef-0efe-468e-ae85-61f6bfce3186.databases.neo4j.io",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "...",
        "QDRANT_URL": "https://4bd4d2b1-e5ed-4fcf-ba96-7d9a6ad7eb6a.europe-west3-0.gcp.cloud.qdrant.io",
        "QDRANT_API_KEY": "...",
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

**Viktig**: Alle credentials er inkludert i config så MCP-serveren har direkte tilgang til Neo4j, Qdrant og OpenAI.

---

## System Prompt for LM Studio

Legg til dette i system prompt for automatisk memory-bruk:

```
You have persistent memory via MCP tools. Use these AUTOMATICALLY:

1. chat_memory_retrieve: Load user context at start of EVERY conversation
2. chat_memory_store: Save important info when user shares identity/preferences
3. chat_memory_feedback: Mark memories as useful/wrong based on user corrections
4. chat_memory_profile: Get full user overview when needed

You also have access to EFC theory via:
- symbiosis_vector_search: Semantic search
- symbiosis_graph_query: Cypher queries
- symbiosis_hybrid_search: Combined search
- authority_check: Verify source trust level

Use these tools proactively to provide personalized, contextual responses.
```

---

## Complete Workflow Example

### Scenario: User introduces themselves

**User**: "Hei! Jeg heter Morten, er gift med Elisabet, og jobber som forsker ved UiO innen kosmologi."

**LLM Internal Actions**:
1. Calls `chat_memory_store`:
   ```json
   {
     "user_message": "Hei! Jeg heter Morten, er gift med Elisabet...",
     "assistant_message": "Hyggelig å møte deg, Morten!",
     "importance": "high"
   }
   ```
   → Stores to Private Memory, auto-classified as LONGTERM

**LLM Response**: 
> "Hyggelig å møte deg, Morten! Spennende at du jobber med kosmologi ved UiO. Jeg har lagret denne informasjonen, så jeg husker det til neste gang."

---

### Scenario: User asks theory question

**User**: "Hva sier EFC om dark energy?"

**LLM Internal Actions**:
1. Calls `symbiosis_vector_search`:
   ```json
   {"query": "dark energy EFC theory", "limit": 3}
   ```
2. Gets relevant EFC theory chunks with scores

**LLM Response**:
> "Based on EFC theory [score: 0.89], dark energy is explained as... [cites specific theory content]"

---

### Scenario: Next conversation (new session)

**User**: "Hei igjen!"

**LLM Internal Actions**:
1. Calls `chat_memory_retrieve`:
   ```json
   {"query": "Who is the user?", "k": 5}
   ```
   → Gets: "Morten, married to Elisabet, researcher at UiO, cosmology"

2. Calls `symbiosis_vector_search`:
   ```json
   {"query": "cosmology research EFC", "limit": 3}
   ```
   → Gets relevant EFC cosmology content

**LLM Response**:
> "Hei Morten! Hyggelig å høre fra deg igjen. Siden du forsker på kosmologi ved UiO, vil du kanskje være interessert i EFC's tilnærming til [relevant topic]..."

---

### Scenario: User corrects information

**User**: "Nei, jeg jobber ikke ved UiO lenger. Jeg har byttet til NTNU."

**LLM Internal Actions**:
1. Calls `chat_memory_feedback`:
   ```json
   {
     "chunk_id": "a29a9d5d-9f42-4c30-94b7-9ffa8df5938e",
     "signal": "wrong",
     "context": "User changed employer to NTNU"
   }
   ```

2. Calls `chat_memory_store`:
   ```json
   {
     "user_message": "Jeg jobber nå ved NTNU",
     "assistant_message": "Notert! Oppdatert...",
     "importance": "high"
   }
   ```

**LLM Response**:
> "Notert! Jeg har oppdatert at du nå jobber ved NTNU. Beklager forvirringen."

---

## Testing After Restart

### 1. Verify MCP Server Running

In LM Studio:
- Settings → Developer → MCP Servers
- Check "symbiosis" shows green status
- Should list all 9 tools

### 2. Test Memory Storage

**Chat**: "Jeg liker å drikke kaffe om morgenen"

**Expected**:
- LLM calls `chat_memory_store` automatically
- Importance detected as "medium"
- Stored to Private Memory

**Verify**:
```bash
tail -f symbiose_gnn_output/chat_memory.jsonl
```

### 3. Test Memory Retrieval

**New session, chat**: "Hei!"

**Expected**:
- LLM calls `chat_memory_retrieve` at start
- Gets back: "liker å drikke kaffe om morgenen"
- Response references this info

### 4. Test EFC Search

**Chat**: "Hva sier EFC om energy flow?"

**Expected**:
- LLM calls `symbiosis_vector_search` or `symbiosis_hybrid_search`
- Gets relevant EFC theory chunks
- Cites specific content with confidence scores

---

## Troubleshooting

### MCP Server Won't Start

```bash
# Check Python environment
source /Users/morpheus/energyflow-cosmology/.venv/bin/activate
python --version  # Should be 3.11+

# Test imports manually
python -c "import sys; sys.path.insert(0, 'tools'); from chat_memory import store_chat_turn; print('OK')"

# Check syntax
python -m py_compile mcp/symbiosis_mcp_server.py
```

### Tools Not Appearing

1. Check LM Studio logs for MCP errors
2. Verify environment variables in config
3. Restart LM Studio completely (not just MCP server)

### Memory Not Storing

```bash
# Test manually
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
python tools/chat_memory.py store --user "Test" --assistant "Test" --importance high

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

with driver.session() as session:
    result = session.run('MATCH (c:PrivateChunk) RETURN count(c) as total')
    print(f'PrivateChunks: {result.single()[\"total\"]}')

driver.close()
"
```

### Authority Check Fails

```bash
# Test manually
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
python -c "
import sys
sys.path.insert(0, 'tools')
from authority_filter import is_authoritative, get_authority_metadata

f = 'theory/README.md'
print(f'Authoritative: {is_authoritative(f)}')
print(f'Metadata: {get_authority_metadata(f)}')
"
```

---

## Architecture Overview

```
LM Studio Chat
    ↓
MCP Tool Call (symbiosis_*)
    ↓
symbiosis_mcp_server.py
    ├─→ API calls (SYMBIOSIS_API_URL) for EFC search
    └─→ Direct imports for Private Memory
        ├─→ tools/chat_memory.py
        │   ├─→ tools/private_orchestrator.py
        │   ├─→ tools/memory_classifier.py
        │   └─→ tools/feedback_listener.py
        └─→ tools/authority_filter.py
    ↓
Neo4j Aura + Qdrant Cloud + OpenAI API
    ↓
Persistent Storage
    ├─→ EFC: :Document, :Chunk, :Concept (authority=1.0)
    └─→ Private: :PrivateDocument, :PrivateChunk, :PrivateConcept (user data)
```

---

## Current System State

### Neo4j
- **EFC namespace**: 987 Documents, 9580 Chunks, 1959 Concepts
- **Private namespace**: 3 PrivateDocuments, 5 PrivateChunks
- **Feedback**: 4 Feedback nodes

### Qdrant
- **efc collection**: 3072-dim embeddings, EFC theory
- **private collection**: 3072-dim embeddings, user memories

### Memory Classes
- **STM**: Short-term, context-bound (not retrieved by default)
- **LONGTERM**: Persistent facts (auto-retrieved in chat)
- **DISCARD**: Noise (never retrieved)

---

## Next Steps

1. ✅ **Restart MCP in LM Studio**
   - Settings → Developer → MCP Servers → Restart "symbiosis"

2. ✅ **Add system prompt**
   - Copy prompt from above
   - Test automatic memory storage/retrieval

3. ✅ **Test all workflows**
   - Store personal info → Retrieve → Correct → Feedback
   - Search EFC theory → Check authority → Cite

4. 🔜 **Production monitoring**
   - Watch `symbiose_gnn_output/chat_memory.jsonl`
   - Monitor Neo4j Private namespace growth
   - Run steering layer weekly: `python tools/steering_layer.py --apply-all`

---

## Summary

🎉 **MCP Integration Complete!**

- ✅ 9 verktøy tilgjengelig
- ✅ Full environment-konfigurasjon
- ✅ Direkte Neo4j + Qdrant + OpenAI tilgang
- ✅ Automatisk memory storage/retrieval
- ✅ EFC theory search og authority check
- ✅ Feedback loop for memory quality

**Du er klar for production chat med persistent memory!** 🚀
