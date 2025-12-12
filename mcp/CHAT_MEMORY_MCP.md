# Complete MCP Tools via Symbiosis Server

## Setup Complete! ✅

MCP-serveren har nå **9 verktøy** som dekker hele EFC + Private Memory-systemet.

## 🔧 Tilgjengelige verktøy

### EFC/Theory Search (4 verktøy)

#### 1. `symbiosis_vector_search`
Semantic search i Qdrant EFC-samling.

#### 2. `symbiosis_graph_query`  
Cypher queries mot Neo4j EFC-graf.

#### 3. `symbiosis_hybrid_search`
Kombinert graph + vector search.

#### 4. `symbiosis_get_concepts`
Finn konsepter i grafen.

---

### Private Memory (4 verktøy)

#### 5. `chat_memory_store`
Lagrer viktige chat-interaksjoner.

**Bruk automatisk** for hver viktig melding!

```json
{
  "user_message": "Jeg heter Morten og er gift med Elisabet",
  "assistant_message": "Hyggelig å møte deg, Morten!",
  "importance": "high"
}
```

**Importance levels:**
- `high`: Identitet, familie, jobb, viktige fakta
- `medium`: Preferanser, hobbyer, interesser
- `low`: Hilsener, vær, small talk (lagres ikke)

#### 6. `chat_memory_retrieve`
Henter relevante minner.

**Bruk automatisk** ved starten av hver samtale!

```json
{
  "query": "Hvem er brukeren?",
  "k": 5
}
```

Returnerer:
```
🧠 Relevant Memories:

1. [LONGTERM, score: 0.67] Jeg heter Morten og er gift med Elisabet
2. [LONGTERM, score: 0.57] Jeg jobber som forsker ved UiO
```

#### 7. `chat_memory_profile`
Henter full brukerprofil.

Ingen argumenter nødvendig.

Returnerer:
```
👤 User Profile:

Key Concepts:
  - Morten (mentioned 1x)
  - Elisabet (mentioned 1x)
  - forskning (mentioned 1x)

Key Facts:
  1. Jeg heter Morten og er gift med Elisabet
  2. Jeg jobber som forsker ved UiO
```

#### 8. `chat_memory_feedback`
Marker et minne som nyttig eller feil.

Brukes når brukeren bekrefter/korrigerer informasjon.

```json
{
  "chunk_id": "6fa8824e-6daa-44bf-8b68-a6dbbcbecb67",
  "signal": "useful",
  "context": "User confirmed marriage info"
}
```

Returnerer:
```
✅ Marked memory 6fa8824e... as useful
```

---

### System Tools (1 verktøy)

#### 9. `authority_check`
Sjekk om en fil er autoritativ EFC-teori eller brukerinnhold.

```json
{
  "file_path": "theory/README.md"
}
```

Returnerer:
```
📋 Authority Check: theory/README.md

Authoritative: ✅ YES
Trust Score: 1.0
Authority Level: core
Reason: Core theory file
```

## Workflow i LM Studio

### Ved hver samtale:

1. **Start**: Kall `chat_memory_retrieve` med query "Hvem er brukeren?"
2. **Under samtale**: Hvis bruker deler viktig info → kall `chat_memory_store`
3. **Når usikker**: Kall `chat_memory_profile` for full oversikt

### Eksempel

**Bruker**: "Hei! Jeg heter Morten og jobber med kosmologi"

**LLM** (internt):
1. Kaller `chat_memory_store`:
   ```json
   {
     "user_message": "Hei! Jeg heter Morten og jobber med kosmologi",
     "assistant_message": "Hyggelig å møte deg, Morten! Spennende at du jobber med kosmologi.",
     "importance": "high"
   }
   ```

**LLM** (til bruker):
> "Hyggelig å møte deg, Morten! Spennende at du jobber med kosmologi. Jeg har lagret denne informasjonen, så jeg husker det til neste gang."

---

**Neste samtale, neste dag:**

**Bruker**: "Hei igjen!"

**LLM** (internt):
1. Kaller `chat_memory_retrieve`:
   ```json
   {
     "query": "Hvem er brukeren?",
     "k": 3
   }
   ```
   Får tilbake:
   ```
   1. [LONGTERM, score: 0.82] Jeg heter Morten og jobber med kosmologi
   ```

**LLM** (til bruker):
> "Hei Morten! Hyggelig å høre fra deg igjen. Hvordan går det med kosmologiforskningen?"

## Restart MCP Server

Hvis du har oppdatert serveren, må du restarte MCP i LM Studio:

1. Åpne LM Studio Settings
2. Gå til "Developer" → "MCP Servers"
3. Klikk "Restart" på "symbiosis"
4. Verifiser at alle 7 verktøy er tilgjengelige (4 gamle + 3 nye)

## Debugging

Test manuelt:
```bash
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
python tools/chat_memory.py retrieve --query "Hvem er brukeren?"
```

Sjekk logs:
```bash
tail -f symbiose_gnn_output/chat_memory.jsonl
```

## Automatic Importance Detection

Hvis `importance` ikke spesifiseres, detekteres den automatisk:

**High keywords**: "my name is", "i am", "married to", "work at", "live in", "remember"
**Medium keywords**: "like", "prefer", "enjoy", "interested in", "hobby"
**Low keywords**: "weather", "hello", "hi", "thanks"

## Architecture

```
LM Studio Chat
    ↓
MCP Tool Call (chat_memory_store/retrieve/profile)
    ↓
tools/chat_memory.py
    ↓
tools/private_orchestrator.py → Neo4j + Qdrant
    ↓
tools/memory_classifier.py → LLM classification
    ↓
Persistent storage (:PrivateChunk, "private" collection)
```

## Configuration

Din `lm-studio-config.json` er oppdatert med alle nødvendige environment-variabler:

```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": ["/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server.py"],
      "env": {
        "SYMBIOSIS_API_URL": "http://localhost:8000",
        "NEO4J_URI": "...",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "...",
        "QDRANT_URL": "...",
        "QDRANT_API_KEY": "...",
        "OPENAI_API_KEY": "..."
      }
    }
  }
}
```

## Status

✅ **9 MCP-verktøy totalt**:
  - 4 EFC/Theory tools (vector, graph, hybrid, concepts)
  - 4 Private Memory tools (store, retrieve, profile, feedback)
  - 1 System tool (authority check)

✅ chat_memory.py produksjonsklar (Phase 21 fixes)
✅ Selektiv LONGTERM-promotering
✅ Adaptive embedding dimensions
✅ Label-based namespace isolation
✅ Full environment-variabel konfigurasjon

**Neste steg**: Restart MCP server i LM Studio og test!
