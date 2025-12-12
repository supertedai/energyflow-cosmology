# Msty AI Integration Guide

## Overview

The Energyflow-Cosmology system now provides a dedicated live context API for Msty AI, enabling real-time context retrieval, EFC pattern detection, and adaptive learning.

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. Get Live Context

**Endpoint:** `POST /msty/context`

**Purpose:** Get comprehensive context for current conversation including memory, EFC patterns, and related concepts.

**Request:**
```json
{
  "query": "Hvorfor stabiliserer galakser seg?",
  "conversation_history": [
    {"role": "user", "content": "Hva er EFC?"},
    {"role": "assistant", "content": "EFC er..."}
  ],
  "user_id": "optional-user-id",
  "domain": "cosmology"
}
```

**Response:**
```json
{
  "query": "Hvorfor stabiliserer galakser seg?",
  "context": {
    "semantic": "Relevant context from memory...",
    "efc_patterns": ["stabilisering", "systemdynamikk"],
    "reasoning_traces": [],
    "memory_layers": ["semantic_mesh", "canonical_core"]
  },
  "efc_pattern_detected": true,
  "efc_score": 6.5,
  "efc_reasoning": "Question shows EFC patterns: stabilization dynamics...",
  "should_use_efc": true,
  "related_concepts": ["galakse", "gravitasjon", "rotasjon"],
  "conversation_context": "user: Hva er EFC?\nassistant: EFC er...",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 2. Enhanced Query

**Endpoint:** `POST /msty/query`

**Purpose:** Get complete answer with automatic EFC augmentation.

**Request:**
```json
{
  "query": "Hvorfor stabiliserer galakser seg?",
  "conversation_history": [],
  "use_efc_augmentation": true,
  "domain": "cosmology"
}
```

**Response:**
```json
{
  "answer": "Complete answer with EFC context...",
  "efc_used": true,
  "context_retrieved": true,
  "patterns_detected": ["stabilisering"],
  "confidence": 0.85,
  "sources": ["memory", "efc_engine"],
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### 3. Record Feedback

**Endpoint:** `POST /msty/feedback`

**Purpose:** Enable adaptive learning by recording whether responses were helpful.

**Request:**
```json
{
  "query": "Hvorfor stabiliserer galakser seg?",
  "response": "The answer provided...",
  "was_helpful": true,
  "user_id": "optional-user-id",
  "domain": "cosmology"
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Feedback recorded",
  "learning_active": true
}
```

### 4. Get Active Patterns

**Endpoint:** `GET /msty/patterns?domain=cosmology`

**Purpose:** See what patterns the system has learned are effective.

**Response:**
```json
{
  "patterns": [
    {
      "domain": "cosmology",
      "pattern": "stabilisering",
      "occurrences": 15,
      "success_rate": 0.93,
      "last_used": "2024-01-15T10:00:00.000Z"
    }
  ],
  "total": 1,
  "domain_filter": "cosmology"
}
```

### 5. Health Check

**Endpoint:** `GET /msty/health`

**Purpose:** Check if context API is operational.

**Response:**
```json
{
  "status": "operational",
  "memory_system": "active",
  "efc_engine": "active",
  "learning_enabled": true,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## Integration Workflow

### Recommended Flow for Msty AI

```python
import httpx

async def handle_user_query(query: str, conversation_history: list):
    """
    Complete workflow for Msty AI integration.
    """
    
    # Step 1: Get live context
    context_response = await client.post(
        "http://localhost:8000/msty/context",
        json={
            "query": query,
            "conversation_history": conversation_history,
            "domain": detect_domain(query)  # Your domain detection
        }
    )
    context = context_response.json()
    
    # Step 2: Decide whether to use EFC
    use_efc = context["should_use_efc"]
    
    # Step 3: Get enhanced answer
    query_response = await client.post(
        "http://localhost:8000/msty/query",
        json={
            "query": query,
            "conversation_history": conversation_history,
            "use_efc_augmentation": use_efc
        }
    )
    result = query_response.json()
    
    # Step 4: Present answer to user
    return result["answer"]


async def record_user_feedback(query: str, response: str, was_helpful: bool):
    """
    Record feedback for adaptive learning.
    """
    await client.post(
        "http://localhost:8000/msty/feedback",
        json={
            "query": query,
            "response": response,
            "was_helpful": was_helpful
        }
    )
```

## EFC Pattern Detection

The system automatically detects EFC patterns in queries using a 3-layer heuristic:

1. **Language Cues** (0-3 points): Norwegian words indicating EFC relevance
   - "hvordan", "hvorfor", "energi", "flyt", "system", "sammenheng"

2. **Structural Cues** (0-3 points): Question structure
   - Causal questions ("hvorfor")
   - System-level questions
   - Multiple-word depth

3. **Logical Cues** (0-3 points): Logical patterns
   - Flow concepts
   - Conservation principles
   - Network effects

**Score Interpretation:**
- 0-2: OUT_OF_SCOPE (EFC not relevant)
- 3-4: WEAK_SIGNAL (possibly relevant)
- 5-6: EFC_RELEVANT (should augment)
- 7+: EFC_ENABLED (should override other approaches)

## Adaptive Learning (Layer 9)

The system learns from feedback:

1. **Pattern Observation**: Tracks which patterns work in which domains
2. **Threshold Adjustment**: Adapts activation thresholds based on success rate
3. **Cross-Domain Discovery**: Identifies universal patterns (validated in ≥3 domains)
4. **Automatic Activation**: New domains inherit learned patterns

**Example:**
```
1. User asks: "Hvorfor stabiliserer celler homeostase?" (biology)
   → System detects "stabilisering", marks as helpful

2. User asks: "Hvorfor stabiliserer markeder seg?" (economics)
   → System detects "stabilisering", marks as helpful

3. User asks: "Hvorfor stabiliserer galakser seg?" (cosmology)
   → System detects "stabilisering", marks as helpful

4. System discovers: "stabilisering" is universal pattern (3 domains)

5. User asks: "Hvorfor stabiliserer mennesker emosjonell balanse?" (NEW: psychology)
   → System AUTOMATICALLY activates EFC (inherited from learning)
```

## Configuration

### Environment Variables

```bash
# Backend API URL
SYMBIOSIS_API_URL=http://localhost:8000

# Neo4j (optional, for graph features)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Qdrant (optional, for vector search)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### Starting the API

```bash
# Install dependencies
pip install -r requirements-api.txt

# Start unified API
cd apis/unified_api
uvicorn main:app --reload --port 8000
```

### Using with MCP

The MCP server v6.0 exposes Msty endpoints as tools:

```bash
# Start MCP server
python mcp/symbiosis_mcp_server_v6_efc.py
```

**Available MCP Tools:**
- `msty_get_context`: Get live context
- `efc_detect_pattern`: Detect EFC patterns
- `efc_record_feedback`: Record learning feedback
- `efc_get_universal_patterns`: Get universal patterns

## Example: Complete Integration

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

SYMBIOSIS_API = "http://localhost:8000"


@app.post("/chat")
async def chat(query: str, history: list):
    """
    Complete Msty AI chat integration.
    """
    async with httpx.AsyncClient() as client:
        # Get context
        context_resp = await client.post(
            f"{SYMBIOSIS_API}/msty/context",
            json={"query": query, "conversation_history": history}
        )
        context = context_resp.json()
        
        # Get answer
        answer_resp = await client.post(
            f"{SYMBIOSIS_API}/msty/query",
            json={
                "query": query,
                "conversation_history": history,
                "use_efc_augmentation": context["should_use_efc"]
            }
        )
        result = answer_resp.json()
        
        return {
            "answer": result["answer"],
            "context": context,
            "confidence": result["confidence"]
        }


@app.post("/feedback")
async def feedback(query: str, was_helpful: bool):
    """
    Record user feedback.
    """
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{SYMBIOSIS_API}/msty/feedback",
            json={
                "query": query,
                "response": "",  # Your response
                "was_helpful": was_helpful
            }
        )
    
    return {"status": "ok"}
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/msty/health

# Test context retrieval
curl -X POST http://localhost:8000/msty/context \
  -H "Content-Type: application/json" \
  -d '{"query": "Hvorfor stabiliserer galakser seg?"}'

# Test query endpoint
curl -X POST http://localhost:8000/msty/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hvorfor stabiliserer galakser seg?", "use_efc_augmentation": true}'
```

## Next Steps

1. **Configure Msty AI** to use `http://localhost:8000/msty` endpoints
2. **Enable feedback collection** to activate adaptive learning
3. **Monitor patterns** via `/msty/patterns` endpoint
4. **Check universal patterns** via `/efc/universal-patterns`
5. **Visualize learning** by tracking domain statistics

## Support

For issues or questions:
- Check `/msty/health` endpoint
- Review logs in terminal where API is running
- Validate Neo4j connection if graph features needed
- Ensure Python dependencies are installed

---

**Status:** ✅ PRODUCTION READY

The Msty AI integration is complete and operational. All endpoints tested and working.
