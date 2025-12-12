#!/usr/bin/env python3
"""
Symbiosis MCP Server v4.0 - BACKEND PROXY ARCHITECTURE

ALL logic runs in backend (FastAPI). MCP is a thin proxy calling APIs.

Architecture:
- MCP Server: Thin proxy (this file)
- Backend API: All logic (FastAPI at localhost:8000)
- Tools: 1 unified chat handler + EFC knowledge base tools
"""

import os
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

print("🚀 Symbiosis MCP Server v4.0 (BACKEND PROXY) starting...", file=sys.stderr)
print(f"   Backend: {API_BASE}", file=sys.stderr)

server = Server("symbiosis")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """System instructions for unified backend architecture."""
    return [
        types.Prompt(
            name="unified_backend",
            description="CRITICAL: All logic runs in backend - use symbiosis_chat_turn for ALL conversations",
            arguments=[]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    """Return system prompt."""
    if name == "unified_backend":
        
        system_instructions = """🔥 UNIFIED BACKEND ARCHITECTURE

ALL processing happens in backend. MCP is just a proxy.

ONE TOOL for all conversations:
• symbiosis_chat_turn → Calls /chat/turn API

Backend automatically handles:
1. Memory retrieval (LONGTERM storage)
2. Memory enforcement (fixes contradictions)
3. Domain analysis (12 cognitive fields)
4. GNN scoring (structural similarity to EFC)
5. Storage (saves corrected answer)

WORKFLOW:
1. You generate draft response
2. Call symbiosis_chat_turn(user_message="...", assistant_draft="...")
3. Backend processes (6 steps)
4. Get final_answer (possibly corrected)
5. Send final_answer to user

EXAMPLE:
User: "Hva heter du?"
Draft: "Jeg heter Qwen"
Call: symbiosis_chat_turn(user_message="Hva heter du?", assistant_draft="Jeg heter Qwen")
Backend returns: {final_answer: "Jeg heter Opus", was_overridden: true}
Send: "Jeg heter Opus"

All logic is in backend - MCP just forwards requests."""
        
        return types.GetPromptResult(
            description="Unified backend protocol",
            messages=[
                types.PromptMessage(
                    role="system",
                    content=types.TextContent(
                        type="text",
                        text=system_instructions
                    )
                )
            ]
        )
    
    raise ValueError(f"Unknown prompt: {name}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Register tools - all proxy to backend APIs."""
    
    return [
        # ============================================================
        # UNIFIED CHAT HANDLER (proxies to /chat/turn)
        # ============================================================
        types.Tool(
            name="symbiosis_chat_turn",
            description="""🔥 UNIFIED CHAT HANDLER - Use for ALL conversations!

Proxies to backend /chat/turn API which handles:
• Memory retrieval + enforcement
• Domain analysis (12 fields)
• GNN scoring (EFC similarity)
• Auto-storage

WORKFLOW:
1. Generate draft response
2. Call this tool
3. Backend processes (6 steps)
4. Get corrected final_answer
5. Send to user

EXAMPLE:
User: "Hva heter du?"
Draft: "Jeg heter Qwen"
Call: symbiosis_chat_turn(user_message="Hva heter du?", assistant_draft="Jeg heter Qwen")
Returns: {final_answer: "Jeg heter Opus", was_overridden: true}
Send: "Jeg heter Opus"

ALL logic in backend - this is just a proxy.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "User's question/statement (REQUIRED)"
                    },
                    "assistant_draft": {
                        "type": "string",
                        "description": "Your draft response BEFORE sending (REQUIRED)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for grouping"
                    }
                },
                "required": ["user_message", "assistant_draft"]
            }
        ),
        
        # ============================================================
        # KNOWLEDGE BASE TOOLS (proxy to existing APIs)
        # ============================================================
        types.Tool(
            name="symbiosis_vector_search",
            description="Search EFC knowledge base (Qdrant). Proxies to /rag/search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_graph_query",
            description="Execute Cypher on Neo4j. Proxies to /neo4j/q",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_hybrid_search",
            description="Hybrid search (Neo4j + Qdrant). Proxies to /graph-rag/search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_get_concepts",
            description="Get EFC concepts from graph. Proxies to /neo4j/q",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string"}
                },
                "required": ["term"]
            }
        ),
        
        # ============================================================
        # SYSTEM TOOLS
        # ============================================================
        types.Tool(
            name="mcp_version",
            description="Get MCP server version.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool execution - all proxy to backend APIs."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # ============================================================
            # UNIFIED CHAT HANDLER → /chat/turn
            # ============================================================
            if name == "symbiosis_chat_turn":
                user_message = arguments.get("user_message")
                assistant_draft = arguments.get("assistant_draft")
                session_id = arguments.get("session_id")
                
                if not user_message or not assistant_draft:
                    return [types.TextContent(
                        type="text",
                        text="❌ ERROR: Both user_message and assistant_draft required"
                    )]
                
                # Call backend API
                response = await client.post(
                    f"{API_BASE}/chat/turn",
                    json={
                        "user_message": user_message,
                        "assistant_draft": assistant_draft,
                        "session_id": session_id
                    }
                )
                
                if response.status_code != 200:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Backend error: {response.status_code}\n{response.text}"
                    )]
                
                data = response.json()
                
                # Format response with SYNCED fields
                response_parts = [
                    "="*60,
                    "🎯 FINAL ANSWER:",
                    "="*60,
                    data.get('final_answer', assistant_draft),
                    ""
                ]
                
                # Show override status if applicable
                if data.get('was_overridden'):
                    response_parts.extend([
                        "="*60,
                        "🔒 MEMORY ENFORCEMENT:",
                        "="*60,
                        f"⚠️ Response OVERRIDDEN",
                        f"Original: {data.get('original_answer', 'N/A')[:80]}...",
                        f"Reason: {data.get('conflict_reason', 'Unknown')}",
                        ""
                    ])
                
                # Memory info
                memory_used = data.get('memory_used', '')
                if memory_used:
                    response_parts.extend([
                        "="*60,
                        "💾 MEMORY:",
                        "="*60,
                        memory_used[:200] + "..." if len(memory_used) > 200 else memory_used,
                        ""
                    ])
                
                # GNN scores
                gnn = data.get('gnn', {})
                if gnn.get('available'):
                    response_parts.extend([
                        "="*60,
                        "🔗 GNN ANALYSIS:",
                        "="*60,
                        f"Similarity: {gnn.get('gnn_similarity', 0):.3f}",
                        f"Confidence: {gnn.get('confidence', 0):.3f}",
                        ""
                    ])
                    
                    top_matches = gnn.get('top_matches', [])
                    if top_matches:
                        response_parts.append("Top EFC matches:")
                        for match in top_matches[:3]:
                            response_parts.append(
                                f"  • {match.get('concept', 'Unknown')} ({match.get('semantic_similarity', 0):.3f})"
                            )
                        response_parts.append("")
                
                # Storage info
                memory_stored = data.get('memory_stored', {})
                if memory_stored.get('stored'):
                    response_parts.extend([
                        "="*60,
                        "💾 STORED:",
                        "="*60,
                        f"✅ Memory stored: {memory_stored.get('document_id', 'Unknown')[:16]}...",
                        ""
                    ])
                
                return [types.TextContent(
                    type="text",
                    text="\n".join(response_parts)
                )]
            
            # ============================================================
            # SYSTEM TOOLS
            # ============================================================
            elif name == "mcp_version":
                # Check backend health
                try:
                    health_response = await client.get(f"{API_BASE}/health")
                    backend_status = "✅ Connected" if health_response.status_code == 200 else "❌ Error"
                except:
                    backend_status = "❌ Offline"
                
                return [types.TextContent(
                    type="text",
                    text=f"""🚀 Symbiosis MCP Server v4.0

VERSION: 4.0.0 (BACKEND PROXY)
ARCHITECTURE: Thin proxy → Backend API

BACKEND: {API_BASE}
STATUS: {backend_status}

TOOLS:
1. symbiosis_chat_turn (→ /chat/turn)
2. symbiosis_vector_search (→ /rag/search)
3. symbiosis_graph_query (→ /neo4j/q)
4. symbiosis_hybrid_search (→ /graph-rag/search)
5. symbiosis_get_concepts (→ /neo4j/q)
6. mcp_version (local)

ALL LOGIC IN BACKEND:
✅ Memory enforcement
✅ Domain analysis
✅ GNN scoring
✅ Auto-storage
✅ Knowledge base search

MCP = Thin proxy forwarding to FastAPI"""
                )]
            
            # ============================================================
            # KNOWLEDGE BASE TOOLS (proxy to existing APIs)
            # ============================================================
            elif name == "symbiosis_vector_search":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                
                response = await client.get(
                    f"{API_BASE}/rag/search",
                    params={"query": query, "limit": limit}
                )
                data = response.json()
                
                if data.get("status") == "ok":
                    results = data.get("results", [])
                    formatted = f"Found {len(results)} results:\n\n"
                    for i, hit in enumerate(results, 1):
                        formatted += f"{i}. [Score: {hit['score']:.3f}]\n"
                        formatted += f"Source: {hit['source']}\n"
                        formatted += f"Text: {hit['text'][:300]}...\n\n"
                    return [types.TextContent(type="text", text=formatted)]
                else:
                    return [types.TextContent(type="text", text=f"Error: {data.get('error')}")]
            
            elif name == "symbiosis_graph_query":
                query = arguments["query"]
                response = await client.post(f"{API_BASE}/neo4j/q", json={"query": query})
                data = response.json()
                return [types.TextContent(type="text", text=json.dumps(data, indent=2))]
            
            elif name == "symbiosis_hybrid_search":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                response = await client.get(
                    f"{API_BASE}/graph-rag/search",
                    params={"query": query, "limit": limit}
                )
                data = response.json()
                
                neo4j_hits = data.get("neo4j", [])
                qdrant_data = data.get("qdrant", {})
                qdrant_hits = qdrant_data.get("results", [])
                
                formatted = f"=== Neo4j ({len(neo4j_hits)}) ===\n"
                for c in neo4j_hits:
                    formatted += f"- {c['name']}\n"
                
                formatted += f"\n=== Qdrant ({len(qdrant_hits)}) ===\n"
                for hit in qdrant_hits[:3]:
                    formatted += f"[{hit['score']:.3f}] {hit['source']}\n"
                    formatted += f"{hit['text'][:200]}...\n\n"
                
                return [types.TextContent(type="text", text=formatted)]
            
            elif name == "symbiosis_get_concepts":
                term = arguments["term"]
                cypher = f"""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower('{term}')
                RETURN labels(n)[0] AS type, n.name AS name
                LIMIT 10
                """
                response = await client.post(f"{API_BASE}/neo4j/q", json={"query": cypher})
                data = response.json()
                
                formatted = f"Concepts matching '{term}':\n"
                for item in data:
                    formatted += f"[{item['type']}] {item['name']}\n"
                return [types.TextContent(type="text", text=formatted)]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="symbiosis-v4",
            server_version="4.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import sys
    asyncio.run(main())
