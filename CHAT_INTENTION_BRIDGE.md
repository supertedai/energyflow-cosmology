# Chat → Intention Bridge

**Version:** 1.0.0  
**Date:** 2025-12-10  
**Status:** ✅ Complete and tested

## Purpose

Connect chat interactions directly to Intention Gate analysis without automatic execution.

**Philosophy:** "Ingen skriving. Ingen makt. Kun speiling."

## Architecture

```
Chat Turn
   ↓
Store → Private Memory (chat namespace)
   ↓
Retrieve → Find relevant chunks (semantic search)
   ↓
Analyze → Intention Gate + GNN scoring
   ↓
Suggest → Return recommendations (NO WRITES)
```

## Safety Principles

❌ **NO automatic promotion**  
❌ **NO memory class changes**  
❌ **NO steering execution**  
✅ **ONLY observation and suggestions**

## Components

### 1. chat_intention_bridge.py (310 lines)

**Main Function:**
```python
analyze_chat_turn(
    user_message: str,
    assistant_message: str,
    importance: str = "medium"
) -> dict
```

**Flow:**
1. Store chat turn via `store_chat_turn()`
2. Retrieve relevant chunks via `retrieve_relevant_memory()`
3. Fetch chunks with feedback from Neo4j
4. Run `intention_gate` analysis on each chunk
5. Enhance with GNN scoring (if available)
6. Return structured suggestions

**Output:**
```python
{
    "stored_chunk_id": "uuid",
    "suggestions": [
        {
            "chunk_id": "uuid",
            "memory_class": "STM",
            "text_preview": "...",
            "action": "wait",
            "reason": "Quality issues: no_feedback",
            "confidence": 0.0,
            "gnn_similarity": 0.53,
            "gnn_top_matches": [...]
        }
    ],
    "timestamp": "2025-12-10T20:05:05"
}
```

### 2. MCP Integration (v2.3.0)

**Tool:** `chat_intention_analyze`

**Description:** Bridge chat turns to intention analysis. Stores chat, retrieves relevant chunks, analyzes with GNN scoring, returns suggestions. Read-only (NO automatic promotion).

**Parameters:**
- `user_message` (required): User's message in current turn
- `assistant_message` (required): Assistant's message in current turn  
- `importance` (optional): "high" | "medium" | "low" (default: "medium")

**Example Call:**
```json
{
  "name": "chat_intention_analyze",
  "arguments": {
    "user_message": "What is entropy?",
    "assistant_message": "Entropy measures disorder...",
    "importance": "medium"
  }
}
```

**LLM Response:**
```
🎯 **Intention Gate Analysis**

Stored new chunk: None
Analyzed 7 existing chunks

**WAIT** (5 chunks):
  • Personal info chunks (LONGTERM, no_feedback)
  • GNN Similarity: 0.07

**NONE** (2 chunks):
  • Theory chunks (STM, moderate confidence)
  • GNN Similarity: 0.50, 0.53
```

## Usage

### Command Line

```bash
# Basic usage
python tools/chat_intention_bridge.py \
  --user "What is entropy?" \
  --assistant "Entropy measures disorder..."

# With importance
python tools/chat_intention_bridge.py \
  --user "My name is Morten" \
  --assistant "Nice to meet you, Morten!" \
  --importance high

# JSON output (for programmatic use)
python tools/chat_intention_bridge.py \
  --user "Tell me about EFC" \
  --assistant "EFC is..." \
  --json
```

### Via MCP (LM Studio/Claude Desktop)

The LLM can call `chat_intention_analyze` automatically when it wants to understand if recent chat should affect memory promotion.

**Use cases:**
- User asks about theory → Check if theory content should promote
- Important personal information shared → Analyze if should move to LONGTERM
- User corrects information → See if related chunks need review

## GNN Integration

**Hybrid Two-Stage Scoring:**

1. **String Filter** → Find 50 candidate EFC concepts
2. **Semantic Similarity** → Embed in same space (OpenAI)
3. **GNN Weighting** → Boost by centrality (high-degree nodes)

**Domain Filtering:**
- Personal content (identity, preferences) → Skip GNN (returns 0.0)
- Theory content → Full GNN scoring (0.0-1.0)

**Example Scores:**
- "My name is Morten" → GNN: 0.07 (filtered)
- "Entropy drives cosmic evolution" → GNN: 0.65-0.75 (boosted)

## Output Format

### Human-Readable (default)

```
🎯 **Intention Gate Analysis**

Stored new chunk: 8649
Analyzed 10 existing chunks

**WAIT** (8 chunks):
  • Hei! Jeg heter Morten...
    Class: LONGTERM → Confidence: 0.00
    Reason: Quality issues: no_feedback
  
  • Jeg jobber som forsker...
    Class: LONGTERM → Confidence: 0.00
    Reason: Quality issues: no_feedback, low_gnn_similarity
    GNN Similarity: 0.07

**NONE** (2 chunks):
  • Bootstrap test - energy flow patterns...
    Class: STM → Confidence: 0.40
    Reason: No action needed
    GNN Similarity: 0.50

---
Timestamp: 2025-12-10T20:05:05
```

### JSON (--json flag)

```json
{
  "stored_chunk_id": "216ea6ef-...",
  "suggestions": [
    {
      "chunk_id": "bf90fd1b-...",
      "memory_class": "LONGTERM",
      "text_preview": "Hei! Jeg heter Morten...",
      "action": "wait",
      "reason": "Quality issues: no_feedback",
      "confidence": 0.0,
      "gnn_similarity": null,
      "gnn_available": false
    },
    {
      "chunk_id": "a58f9c98-...",
      "memory_class": "STM",
      "text_preview": "Bootstrap test...",
      "action": "none",
      "reason": "No action needed",
      "confidence": 0.4,
      "gnn_similarity": 0.50,
      "gnn_available": true,
      "gnn_top_matches": [
        {
          "concept": "entropy",
          "semantic_similarity": 0.52,
          "weighted_similarity": 0.58
        }
      ]
    }
  ],
  "timestamp": "2025-12-10T20:05:05.449154"
}
```

## Testing

### Unit Tests

```bash
# Test with personal content (should skip GNN)
python tools/chat_intention_bridge.py \
  --user "Hva heter du?" \
  --assistant "Jeg heter Morten"

# Expected: GNN ~0.07 or skipped

# Test with theory content (should use GNN)
python tools/chat_intention_bridge.py \
  --user "What is entropy?" \
  --assistant "Entropy measures disorder in systems"

# Expected: GNN ~0.50-0.65
```

### Integration Test (MCP)

1. Start MCP server: `python mcp/symbiosis_mcp_server.py`
2. In LM Studio/Claude Desktop, call tool:
   ```json
   {
     "name": "chat_intention_analyze",
     "arguments": {
       "user_message": "Tell me about EFC",
       "assistant_message": "EFC is a theoretical framework..."
     }
   }
   ```
3. Verify: Returns structured suggestions, NO writes to memory classes

## Bugs Fixed

### v1.0.0 (2025-12-10)

1. **TypeError on sorting None timestamps**
   - Location: Line 169
   - Fix: `c.get("created_at") or 0` instead of `c.get("created_at", 0)`
   - Reason: `dict.get(key, default)` returns None if key exists with None value

2. **TypeError on time calculation with None**
   - Location: intention_gate.py line ~249
   - Fix: Check if `chunk_created_at is None` before subtraction
   - Reason: `now - None` throws TypeError

## Dependencies

- `chat_memory.py` - Store and retrieve chat turns
- `intention_gate.py` - Analyze chunks and suggest actions
- `gnn_scoring.py` - GNN-based structural similarity
- `private_orchestrator.py` - Private Memory pipeline
- Neo4j - Store chunks with feedback
- Qdrant - Semantic search
- OpenAI API - Embeddings for GNN scoring

## Future Enhancements

1. **Batch Analysis** - Analyze multiple chat turns at once
2. **Trend Detection** - Track recurring themes across chats
3. **Auto-feedback** - Learn from user reactions to suggestions
4. **Confidence Tuning** - Adjust GNN weights based on domain
5. **MCP Streaming** - Stream suggestions as they're analyzed

## Version History

- **v1.0.0** (2025-12-10)
  - Initial release
  - Complete chat → intention bridge
  - GNN integration with domain filtering
  - MCP v2.3.0 integration
  - Bug fixes for None timestamps
  - Production ready

## License

Part of Energy Flow Cosmology project.  
© 2025 Morten Grødem
