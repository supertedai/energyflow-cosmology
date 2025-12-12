# 🚨 CRITICAL: LM Studio må fullstendig restartes!

## Problemet:
Du får fortsatt 404-feil selv om koden er fikset. Dette betyr at **LM Studio bruker gammel cache**.

## Løsning (steg for steg):

### 1. Avslutt LM Studio FULLSTENDIG
```bash
# Ikke bare "restart MCP", men:
# 1. Quit LM Studio fullstendig (Cmd+Q)
# 2. Vent 5 sekunder
# 3. Start LM Studio på nytt
```

### 2. Verifiser versjon
Når LM Studio starter igjen, kjør dette verktøyet **først**:
```
Tool: mcp_version
```

**Forventet output:**
```
🚀 Symbiosis MCP Server

Version: 2.0.0 (Phase 22)
Status: ✅ 404 fix applied
Architecture: Direct Python imports (no API)
```

**Hvis du får 404 her også**, betyr det at LM Studio ikke laster den nye filen.

### 3. Test chat_memory_store
```
Tool: chat_memory_store
Arguments: {
  "user_message": "Test versjon 2",
  "assistant_message": "Testing...",
  "importance": "high"
}
```

**Forventet:**
```
✅ Memory stored!
Importance: high
Concepts: Test, versjon
Document ID: [uuid]
```

## Hvis det FORTSATT ikke fungerer:

### Debug-test (kjør i terminal):
```bash
cd /Users/morpheus/energyflow-cosmology
source .venv/bin/activate
python mcp/test_mcp_tools.py
```

**Forventet:**
```
✅ All MCP tool imports working!
```

### Sjekk MCP-konfigurasjon:
```bash
cat ~/Library/Application\ Support/LM\ Studio/mcp_config.json
```

Skal inneholde:
```json
{
  "mcpServers": {
    "symbiosis": {
      "command": "/Users/morpheus/energyflow-cosmology/.venv/bin/python",
      "args": ["/Users/morpheus/energyflow-cosmology/mcp/symbiosis_mcp_server.py"]
    }
  }
}
```

### Alternativ: Kopier config manuelt
```bash
# Hvis LM Studio ikke leser lm-studio-config.json:
cp /Users/morpheus/energyflow-cosmology/mcp/lm-studio-config.json \
   ~/Library/Application\ Support/LM\ Studio/mcp_config.json

# Så restart LM Studio fullstendig
```

## Hva ble fikset i v2.0.0:

### Før (v1.x):
```python
async with httpx.AsyncClient() as client:
    if name == "chat_memory_store":
        # Alle tool calls inne i HTTP-blokk
        # → Prøvde å kalle API → 404
```

### Etter (v2.0.0):
```python
# chat_memory verktøy utenfor HTTP-blokk
if name == "chat_memory_store":
    from chat_memory import store_chat_turn  # Direkte import!
    result = store_chat_turn(...)
    return result

# Kun EFC-verktøy bruker HTTP
async with httpx.AsyncClient() as client:
    if name == "symbiosis_vector_search":
        # API-kall
```

## TL;DR:
1. **Quit LM Studio fullstendig** (ikke bare restart MCP)
2. **Start på nytt**
3. **Kjør `mcp_version` først** for å verifisere v2.0.0
4. **Test `chat_memory_store`**

Hvis det fungerer nå: **🎉 Du er klar!**

Hvis ikke: Send output fra `mcp_version` og vi debugger videre.
