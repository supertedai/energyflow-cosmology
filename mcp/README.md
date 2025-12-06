# Symbiosis MCP Server

🧠 **GNN-Hybrid Graph-RAG** via Model Context Protocol

Exposer Symbiosis (Qdrant + Neo4j + GNN) til LM Studio.

---

## ✅ Ny funksjonalitet (6. des 2025)

**GNN-Hybrid Search** er nå integrert:
- 🧠 **10,183 noder** med 64-dim GNN embeddings
- ⚖️ Hybrid scoring: `α × semantic + (1-α) × structural`
- 🎯 Strukturell likhet via graf-læring

Se [GNN_HYBRID_IMPLEMENTATION.md](../docs/GNN_HYBRID_IMPLEMENTATION.md) for detaljer.

## Setup

1. **Installer MCP Python SDK:**
```bash
pip install mcp httpx
```

2. **Start Symbiosis API** (hvis ikke allerede kjører):
```bash
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
uvicorn apis.unified_api.main:app --port 8000
```

3. **Test MCP Server:**
```bash
python symbiosis_mcp_server.py
```

## LM Studio Configuration

**Viktig**: Kopier konfigurasjonen fra `lm-studio-config.json` til LM Studio sin MCP-konfigurasjonsfil.

### Metode 1: Manuell kopiering
Legg til innholdet fra `mcp/lm-studio-config.json` i LM Studio sin MCP-konfigurasjonsfil:
- **macOS/Linux**: `~/.lmstudio/mcp-config.json`
- **Windows**: `%USERPROFILE%\.lmstudio\mcp-config.json`

Eller kjør dette kommandoen for å kopiere automatisk:
```bash
# macOS/Linux
cp mcp/lm-studio-config.json ~/.lmstudio/mcp-config.json

# Hvis filen allerede finnes, merge med jq
jq -s '.[0] * .[1]' ~/.lmstudio/mcp-config.json mcp/lm-studio-config.json > ~/.lmstudio/mcp-config-merged.json
mv ~/.lmstudio/mcp-config-merged.json ~/.lmstudio/mcp-config.json
```

### Metode 2: LM Studio UI
1. Åpne LM Studio
2. Gå til Settings → MCP Servers
3. Add New Server
4. Fyll inn:
   - Name: `symbiosis`
   - Command: `python`
   - Args: `/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server.py`
   - Env: `SYMBIOSIS_API_URL=http://localhost:8000`

## Available Tools

- `symbiosis_vector_search` - Semantic search via Qdrant
- `symbiosis_graph_query` - Cypher queries to Neo4j
- `symbiosis_hybrid_search` - Combined graph + vector search
- `symbiosis_get_concepts` - List concepts matching term

## Usage Example in LM Studio

```
User: "Search Symbiosis for information about energy flow cosmology"

LM Studio → calls symbiosis_vector_search(query="energy flow cosmology", limit=5)
          → returns top 5 semantic matches with scores

User: "What concepts are related to entropy?"

LM Studio → calls symbiosis_get_concepts(term="entropy")
          → returns Neo4j concept nodes
```

## Docker Alternative

See `Dockerfile.mcp` for containerized deployment.
