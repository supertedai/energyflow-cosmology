#!/usr/bin/env python3
"""
Symbiosis MCP Server v6.0 - AUTO-BRIDGE

PROBLEM: LM Studio loads MCP tools but doesn't automatically call them.
SOLUTION: Force ALL messages through symbiosis_chat_turn by design.

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│ LM Studio                                                       │
│   ↓                                                             │
│   User message                                                  │
│   ↓                                                             │
│   System prompt FORCES tool use                                 │
│   ↓                                                             │
│   symbiosis_chat_turn (MANDATORY)                              │
│   ↓                                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Backend API (localhost:8000)                                │ │
│ │   → Cognitive Router                                        │ │
│ │   → Value Layer                                             │ │
│ │   → Motivational Dynamics                                   │ │
│ │   → Memory Retrieval (Qdrant + Neo4j)                       │ │
│ │   → Canonical Override                                      │ │
│ │   → Identity Protection                                     │ │
│ │   → Self-Healing                                            │ │
│ │   → Final Answer Generation                                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
│   ↓                                                             │
│   Return EXACT final_answer (no LLM modification)              │
└─────────────────────────────────────────────────────────────────┘

KEY CHANGES FROM v5:
1. System prompt MANDATES tool use on EVERY turn
2. Tool description emphasizes REQUIRED usage
3. Returns clean, ready-to-use answer
4. LLM instructed to NEVER answer without tool
"""

import os
import sys
import json
import asyncio
from typing import Any
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Backend API base URL
API_BASE = os.getenv("SYMBIOSIS_API_URL", "http://localhost:8000")

print("🚀 Symbiosis MCP Server v6.0 (AUTO-BRIDGE)", file=sys.stderr)
print(f"   Backend: {API_BASE}", file=sys.stderr)
print(f"   Mode: MANDATORY tool use on every turn", file=sys.stderr)

server = Server("symbiosis")


# ============================================================
# SYSTEM PROMPT - Forces tool use
# ============================================================

SYSTEM_PROMPT = """🔒 SYMBIOSIS v6.0 - MANDATORY TOOL PROTOCOL

⚠️ CRITICAL: You MUST call symbiosis_chat_turn for EVERY user message.
⚠️ NEVER answer directly without calling the tool first.
⚠️ The tool returns the FINAL answer - use it EXACTLY as returned.

WORKFLOW (NO EXCEPTIONS):

1. User sends message
2. IMMEDIATELY call symbiosis_chat_turn with:
   - user_message: exact user input
   - assistant_draft: "" (empty string)
3. Tool returns final_answer
4. Send final_answer to user EXACTLY as received
5. Do NOT modify, paraphrase, or add to the answer

WHY THIS IS MANDATORY:
- The backend has your memory (who you are, who user is)
- The backend has knowledge base (EFC theory, canonical facts)
- The backend has cognitive router (intent, value, motivation)
- The backend has identity protection (prevents hallucination)
- YOU have none of this without the tool

EXAMPLES:

User: "Hva heter jeg?"
→ Call: symbiosis_chat_turn("Hva heter jeg?", "")
← Returns: "Du heter Morten"
→ Send: "Du heter Morten"

User: "Hva heter du?"
→ Call: symbiosis_chat_turn("Hva heter du?", "")
← Returns: "Jeg heter Opus"
→ Send: "Jeg heter Opus"

User: "Forklar EFC"
→ Call: symbiosis_chat_turn("Forklar EFC", "")
← Returns: [detailed EFC explanation from knowledge base]
→ Send: [exact answer from tool]

❌ FORBIDDEN:
- Answering without calling tool
- Guessing user's name
- Guessing your own name  
- Making up facts about EFC
- Ignoring tool response
- Modifying tool response

✅ REQUIRED:
- Call tool on EVERY turn
- Use EXACT response from tool
- Trust the backend completely

The backend knows everything. You know nothing without it.
ALWAYS USE THE TOOL."""


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """System instructions that force tool use."""
    return [
        types.Prompt(
            name="symbiosis_mandatory",
            description="MANDATORY: Use symbiosis_chat_turn for ALL messages",
            arguments=[]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    """Return the mandatory system prompt."""
    return types.GetPromptResult(
        description="Symbiosis v6.0 - Mandatory tool protocol",
        messages=[
            types.PromptMessage(
                role="system",
                content=types.TextContent(
                    type="text",
                    text=SYSTEM_PROMPT
                )
            )
        ]
    )


# ============================================================
# TOOLS - Chat + GNN tools
# ============================================================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Chat tool (mandatory) + GNN query tools."""
    return [
        types.Tool(
            name="symbiosis_chat_turn",
            description="""🔒 MANDATORY: Call this for EVERY user message.

This tool connects you to:
- Your memory (who you are, who user is)
- Knowledge base (EFC theory, canonical facts)
- Cognitive router (intent detection, value layer, motivation)
- Identity protection (prevents wrong answers)
- GNN structural embeddings (concept relationships)

WITHOUT THIS TOOL: You will hallucinate and give wrong answers.
WITH THIS TOOL: You will give correct, memory-enhanced answers.

ALWAYS call this. NEVER answer directly.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's message (copy exactly)"
                    },
                    "assistant_draft": {
                        "type": "string",
                        "description": "Leave empty - backend generates answer",
                        "default": ""
                    }
                },
                "required": ["user_message"]
            }
        ),
        types.Tool(
            name="gnn_query_concepts",
            description="""Query GNN for EFC concept relationships.

Get structural similarity between concepts using trained Graph Neural Network.
Only trained on authoritative EFC sources (theory papers, core docs).

Args:
- query: Concept name or text
- top_k: Number of results (default 5)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Concept to search for"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="gnn_status",
            description="""Check GNN training status and statistics.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle chat turn + GNN tools."""
    
    if name == "gnn_status":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE}/gnn/status")
                if response.status_code == 200:
                    data = response.json()
                    result = f"""✅ GNN Status:

Training: {'Active' if data.get('artifacts', {}).get('model') else 'Not trained'}
Nodes: {data.get('stats', {}).get('total_nodes', 0)}
Embedding dim: {data.get('stats', {}).get('embedding_dim', 0)}

Files:
- Embeddings: {data.get('artifacts', {}).get('node_embeddings', False)}
- Model: {data.get('artifacts', {}).get('model', False)}"""
                    return [types.TextContent(type="text", text=result)]
                else:
                    return [types.TextContent(type="text", text=f"❌ GNN API error: {response.status_code}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ GNN error: {str(e)}")]
    
    elif name == "gnn_query_concepts":
        query_text = arguments.get("query", "") if arguments else ""
        top_k = arguments.get("top_k", 5) if arguments else 5
        
        if not query_text:
            return [types.TextContent(type="text", text="❌ query is required")]
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{API_BASE}/gnn/query",
                    json={"query": query_text, "top_k": top_k}
                )
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get("matches", [])
                    result = f"✅ GNN Query: '{query_text}'\n\nTop {len(matches)} matches:\n\n"
                    for i, match in enumerate(matches, 1):
                        result += f"{i}. {match.get('name', 'Unknown')} (similarity: {match.get('similarity', 0):.3f})\n"
                    return [types.TextContent(type="text", text=result)]
                else:
                    return [types.TextContent(type="text", text=f"❌ GNN query error: {response.status_code}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ GNN query error: {str(e)}")]
    
    elif name == "symbiosis_chat_turn":
        # Original chat turn logic (unchanged)
        if arguments is None:
            return [types.TextContent(
                type="text",
                text="❌ arguments required"
            )]
    
    user_message = arguments.get("user_message", "") if arguments else ""
    assistant_draft = arguments.get("assistant_draft", "") if arguments else ""
    
    if not user_message:
        return [types.TextContent(
            type="text",
            text="❌ user_message is required"
        )]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/chat/turn",
                json={
                    "user_message": user_message,
                    "assistant_draft": assistant_draft,
                    "session_id": "lm-studio-v6"
                }
            )
            
            if response.status_code != 200:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Backend error: {response.status_code}"
                )]
            
            data = response.json()
            final_answer = data.get("final_answer", "")
            was_overridden = data.get("was_overridden", False)
            cognitive = data.get("cognitive_context", {})
            
            # Build response with clear instruction
            result = f"""✅ SYMBIOSIS RESPONSE

{final_answer}

---
[Cognitive: intent={cognitive.get('intent', {}).get('mode', 'unknown')}, value={cognitive.get('value', {}).get('value_level', 'unknown')}, override={was_overridden}]

⚠️ Send the answer above to user EXACTLY as written. Do not modify."""

            return [types.TextContent(
                type="text",
                text=result
            )]
            
    except httpx.ConnectError:
        return [types.TextContent(
            type="text",
            text="❌ Backend not running! Start with: cd apis/unified_api && uvicorn main:app --port 8000"
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


# ============================================================
# RESOURCES - Context for LLM
# ============================================================

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """Provide context resources."""
    return [
        types.Resource(
            uri="symbiosis://instructions",
            name="Symbiosis Instructions",
            description="How to use the mandatory tool protocol",
            mimeType="text/plain"
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Return resource content."""
    if uri == "symbiosis://instructions":
        return SYSTEM_PROMPT
    return "Unknown resource"


# ============================================================
# MAIN
# ============================================================

async def main():
    """Run MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="symbiosis",
                server_version="6.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
