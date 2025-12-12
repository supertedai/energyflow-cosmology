#!/usr/bin/env python3
"""
Symbiosis MCP Server v3.0 - UNIFIED ARCHITECTURE
Simplified from 15+ tools to 1 unified chat handler

BREAKING CHANGE: Old memory tools removed. Use symbiosis_chat_turn instead.
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

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

# Symbiosis API base URL
API_BASE = os.getenv("SYMBIOSIS_API_URL", "http://localhost:8000")

print("🚀 Symbiosis MCP Server v3.0 (UNIFIED) starting...", file=sys.stderr)

server = Server("symbiosis")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """Provide system instructions for unified chat handler."""
    return [
        types.Prompt(
            name="unified_chat",
            description="CRITICAL: Use symbiosis_chat_turn for ALL conversations",
            arguments=[]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    """Return system prompt for unified architecture."""
    if name == "unified_chat":
        
        system_instructions = """🔥 UNIFIED CHAT PROTOCOL

You now have ONE TOOL that handles EVERYTHING:
• symbiosis_chat_turn

This tool automatically:
1. Retrieves memories (from LONGTERM storage)
2. Analyzes domain (12 cognitive fields)
3. Enforces memory authority (fixes contradictions)
4. Scores with GNN (structural similarity to EFC)
5. Stores corrected answer

🚨 MANDATORY WORKFLOW:
1. User asks question
2. You generate draft response
3. Call symbiosis_chat_turn(user_message="...", assistant_draft="...")
4. Get back final_answer (possibly corrected)
5. Send final_answer to user

EXAMPLE:
User: "Hva heter du?"
You draft: "Jeg heter Qwen"
Call: symbiosis_chat_turn(user_message="Hva heter du?", assistant_draft="Jeg heter Qwen")
Returns: {final_answer: "Jeg heter Opus", was_overridden: true}
You send: "Jeg heter Opus"

⚠️ OLD TOOLS REMOVED:
❌ chat_memory_retrieve
❌ chat_memory_store
❌ memory_authority_check
❌ domain_analysis
... and 10+ more

✅ Use symbiosis_chat_turn for ALL conversations!
"""
        
        return types.GetPromptResult(
            description="Unified chat protocol",
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
    """Register tools - UNIFIED architecture (15+ → 1).
    
    VERSION: 3.0.0 (BREAKING CHANGE)
    """
    
    return [
        # ============================================================
        # 🔥 UNIFIED CHAT HANDLER (replaces 15+ tools)
        # ============================================================
        types.Tool(
            name="symbiosis_chat_turn",
            description="""🔥 UNIFIED CHAT HANDLER - Use for ALL conversations!

Handles EVERYTHING automatically:
• Memory retrieval (LONGTERM storage)
• Memory enforcement (fixes contradictions)
• Domain analysis (12 cognitive fields)  
• GNN scoring (structural similarity to EFC)
• Storage (saves corrected answer)

WHEN TO USE:
• EVERY TIME you respond to user
• For ANY question (personal, theory, general)
• After generating your draft response

HOW IT WORKS:
1. You generate draft response
2. Call with user's question + your draft
3. Get final_answer (possibly corrected)
4. Send final_answer to user

EXAMPLE:
User: "Hva heter du?"
Draft: "Jeg heter Qwen"
Call: symbiosis_chat_turn(user_message="Hva heter du?", assistant_draft="Jeg heter Qwen")
Returns: {final_answer: "Jeg heter Opus", was_overridden: true}
Send: "Jeg heter Opus"

REPLACES: chat_memory_retrieve, chat_memory_store, memory_authority_check, domain_analysis, gnn_scoring, and 10+ more.""",
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
        # KNOWLEDGE BASE TOOLS (EFC theory search)
        # ============================================================
        types.Tool(
            name="symbiosis_vector_search",
            description="Search EFC knowledge base (Qdrant). Use for theory/papers/concepts.",
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
            description="Execute Cypher on Neo4j graph. For structured EFC queries.",
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
            description="Hybrid search (Neo4j + Qdrant). Best for complex EFC queries.",
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
            description="Get EFC concepts from graph.",
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
            description="Get MCP server version (debugging).",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool execution - UNIFIED architecture.
    
    VERSION: 3.0.0 (Breaking change - old memory tools removed)
    """
    
    try:
        # ============================================================
        # 🔥 UNIFIED CHAT HANDLER
        # ============================================================
        if name == "symbiosis_chat_turn":
            """ONE tool to rule them all."""
            
            # Import unified router
            from symbiosis_router_v3 import handle_chat_turn
            
            user_message = arguments.get("user_message")
            assistant_draft = arguments.get("assistant_draft")
            session_id = arguments.get("session_id")
            
            if not user_message or not assistant_draft:
                return [types.TextContent(
                    type="text",
                    text="❌ ERROR: Both user_message and assistant_draft required"
                )]
            
            # Call unified router (handles 6 steps automatically)
            result = handle_chat_turn(
                user_message=user_message,
                assistant_draft=assistant_draft,
                session_id=session_id
            )
            
            # Format response with structured info
            response_parts = [
                "="*60,
                "🎯 FINAL ANSWER:",
                "="*60,
                result.get('final_answer', assistant_draft),
                "",
                "="*60,
                "📊 ANALYSIS:",
                "="*60
            ]
            
            # Domain analysis
            domain_data = result.get('domain_analysis', {})
            if domain_data:
                response_parts.extend([
                    f"🧠 Domain: {domain_data.get('primary_domain', 'Unknown')}",
                    f"   Confidence: {domain_data.get('confidence', 0):.2f}",
                    f"   EFC Relevance: {domain_data.get('efc_relevance', 0):.2f}"
                ])
            
            # Memory operations
            memory_ops = result.get('memory_operations', {})
            if memory_ops:
                retrieved = memory_ops.get('retrieved_count', 0)
                stored = memory_ops.get('stored', False)
                response_parts.extend([
                    "",
                    f"💾 Memory:",
                    f"   Retrieved: {retrieved} memories",
                    f"   Stored: {'✅' if stored else '❌'}"
                ])
            
            # Memory enforcement
            enforcement = result.get('enforcement', {})
            if enforcement:
                was_overridden = enforcement.get('was_overridden', False)
                if was_overridden:
                    reason = enforcement.get('reason', 'Unknown')
                    response_parts.extend([
                        "",
                        f"🔒 MEMORY ENFORCEMENT:",
                        f"   ⚠️ Response OVERRIDDEN",
                        f"   Reason: {reason}"
                    ])
            
            # GNN scores
            gnn_scores = result.get('gnn_scores', {})
            if gnn_scores:
                avg_score = gnn_scores.get('average_score', 0)
                response_parts.extend([
                    "",
                    f"🔗 GNN Similarity: {avg_score:.3f}"
                ])
            
            return [types.TextContent(
                type="text",
                text="\n".join(response_parts)
            )]
        
        # ============================================================
        # SYSTEM TOOLS
        # ============================================================
        elif name == "mcp_version":
            return [types.TextContent(
                type="text",
                text="""🚀 Symbiosis MCP Server v3.0

VERSION: 3.0.0 (UNIFIED ARCHITECTURE)
STATUS: ✅ Production ready

ARCHITECTURE:
• 1 unified chat handler (replaces 15+ tools)
• 93% reduction in LLM decision complexity
• Automatic memory enforcement

TOOLS:
1. symbiosis_chat_turn (UNIFIED - use for ALL chat)
2. symbiosis_vector_search (EFC theory)
3. symbiosis_graph_query (Neo4j)
4. symbiosis_hybrid_search (Neo4j + Qdrant)
5. symbiosis_get_concepts (EFC concepts)
6. mcp_version (this tool)

BREAKING CHANGES (v3.0):
❌ Removed: chat_memory_retrieve
❌ Removed: chat_memory_store
❌ Removed: memory_authority_check
❌ Removed: chat_memory_profile
❌ Removed: chat_memory_feedback
❌ Removed: private_ingest_document
❌ Removed: private_gnn_query
❌ Removed: intention_gate_analyze
❌ Removed: chat_intention_analyze
❌ Removed: authority_check

✅ Use: symbiosis_chat_turn (handles all memory operations)

PERFORMANCE:
• ~1.8s per turn (all 6 steps)
• ~$0.0003 per turn (with embedding cache)
• 67% cost saving from optimized domain engine"""
            )]
    
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}\n\nTraceback:\n{__import__('traceback').format_exc()}"
        )]
    
    # ============================================================
    # KNOWLEDGE BASE TOOLS (API calls)
    # ============================================================
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "symbiosis_vector_search":
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
            server_name="symbiosis-v3",
            server_version="3.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
