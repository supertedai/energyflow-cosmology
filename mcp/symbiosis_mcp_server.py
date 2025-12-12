#!/usr/bin/env python3
"""
Symbiosis MCP Server for LM Studio - COGNITIVE ENHANCED
========================================================

Exposes Qdrant, Neo4j, and Graph-RAG through Model Context Protocol
WITH full cognitive stack integration (Phase 1-6 + Router).

NEW: All tools now return cognitive context:
- Intent signal (what user wants)
- Value assessment (what is important)
- Motivational dynamics (what system wants)
- Routing decisions (canonical override, LLM temperature, etc.)

This enables LM Studio to make cognitive-aware decisions.
"""

import os
import json
import asyncio
import sys
from pathlib import Path
from typing import Any
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import cognitive router
from tools.cognitive_router import CognitiveRouter

# Symbiosis API base URL (assumes local or remote deployment)
API_BASE = os.getenv("SYMBIOSIS_API_URL", "http://localhost:8000")

server = Server("symbiosis-cognitive")

# Initialize cognitive router (singleton for session)
cognitive_router = CognitiveRouter()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Register Symbiosis tools for LM Studio."""
    return [
        types.Tool(
            name="symbiosis_vector_search",
            description="Search Symbiosis knowledge base using semantic vector search (Qdrant). Returns relevant documents with similarity scores AND cognitive context (intent, value, motivation).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for semantic matching"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    },
                    "include_cognitive_context": {
                        "type": "boolean",
                        "description": "Include cognitive signals (intent, value, motivation) in response (default: true)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_graph_query",
            description="Execute Cypher query against Neo4j knowledge graph. Use for structured queries about concepts, papers, relationships.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Cypher query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_hybrid_search",
            description="Hybrid search combining Neo4j graph concepts and Qdrant semantic vectors. Best for complex queries requiring both structure and semantics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results per source",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="symbiosis_get_concepts",
            description="Get all concepts from the knowledge graph matching a term.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Concept name or partial match"
                    }
                },
                "required": ["term"]
            }
        ),
        types.Tool(
            name="symbiosis_chat_turn",
            description="Memory-enforced chat handler with FULL COGNITIVE STACK (9 layers + intent + value + motivation). Returns cognitive context: intent mode (protection/learning/exploration), value level (critical/important/routine), motivation strength, active goals, and routing decisions (canonical override, recommended LLM temperature). Use this for ALL chat interactions to get cognitive-aware responses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "User's question or statement"
                    },
                    "assistant_draft": {
                        "type": "string",
                        "description": "Your draft response (will be checked against memory)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session identifier for context tracking",
                        "default": "default"
                    }
                },
                "required": ["user_message", "assistant_draft"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls from LM Studio with cognitive enhancement."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "symbiosis_vector_search":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                include_cognitive = arguments.get("include_cognitive_context", True)
                
                # Get cognitive signals
                cognitive_signals = None
                if include_cognitive:
                    cognitive_signals = cognitive_router.process_and_route(
                        user_input=query,
                        session_context={},
                        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
                    )
                
                response = await client.get(
                    f"{API_BASE}/rag/search",
                    params={"query": query, "limit": limit}
                )
                data = response.json()
                
                # Format results for LM
                if data.get("status") == "ok":
                    results = data.get("results", [])
                    formatted = f"Found {len(results)} results:\n\n"
                    
                    # Add cognitive context if requested
                    if cognitive_signals:
                        intent = cognitive_signals["intent"]["mode"]
                        routing = cognitive_signals["routing_decision"]
                        formatted += f"🧠 COGNITIVE CONTEXT:\n"
                        formatted += f"   Intent: {intent}\n"
                        formatted += f"   Recommended temperature: {routing['llm_temperature']}\n"
                        formatted += f"   Canonical override: {routing['canonical_override_strength']:.2f}\n"
                        
                        if cognitive_signals.get("motivation"):
                            motivation = cognitive_signals["motivation"]["motivation_strength"]
                            goals = [g["goal_type"] for g in cognitive_signals["motivation"]["active_goals"]]
                            formatted += f"   Motivation: {motivation:.2f}\n"
                            formatted += f"   Active goals: {', '.join(goals[:2])}\n"
                        formatted += "\n"
                    
                    for i, hit in enumerate(results, 1):
                        formatted += f"{i}. [Score: {hit['score']:.3f}]\n"
                        formatted += f"Source: {hit['source']}\n"
                        formatted += f"Text: {hit['text'][:300]}...\n\n"
                    return [types.TextContent(type="text", text=formatted)]
                else:
                    return [types.TextContent(type="text", text=f"Error: {data.get('error', 'Unknown error')}")]
            
            elif name == "symbiosis_graph_query":
                query = arguments["query"]
                
                response = await client.post(
                    f"{API_BASE}/neo4j/q",
                    json={"query": query}
                )
                data = response.json()
                
                formatted = f"Query results:\n{json.dumps(data, indent=2)}"
                return [types.TextContent(type="text", text=formatted)]
            
            elif name == "symbiosis_hybrid_search":
                query = arguments["query"]
                limit = arguments.get("limit", 5)
                
                response = await client.get(
                    f"{API_BASE}/graph-rag/search",
                    params={"query": query, "limit": limit}
                )
                data = response.json()
                
                # Format hybrid results
                neo4j_hits = data.get("neo4j", [])
                qdrant_data = data.get("qdrant", {})
                qdrant_hits = qdrant_data.get("results", [])
                
                formatted = f"=== Neo4j Concepts ({len(neo4j_hits)}) ===\n"
                for concept in neo4j_hits:
                    formatted += f"- {concept['name']}\n"
                
                formatted += f"\n=== Qdrant Semantic Matches ({len(qdrant_hits)}) ===\n"
                for hit in qdrant_hits[:3]:
                    formatted += f"[{hit['score']:.3f}] {hit['source']}\n"
                    formatted += f"{hit['text'][:200]}...\n\n"
                
                return [types.TextContent(type="text", text=formatted)]
            
            elif name == "symbiosis_get_concepts":
                term = arguments["term"]
                
                cypher = f"""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS toLower('{term}') 
                   OR toLower(n.text) CONTAINS toLower('{term}')
                RETURN labels(n)[0] AS type, 
                       coalesce(n.name, 'unnamed') AS name,
                       substring(coalesce(n.text, ''), 0, 300) AS preview
                LIMIT 10
                """
                
                response = await client.post(
                    f"{API_BASE}/neo4j/q",
                    json={"query": cypher}
                )
                data = response.json()
                
                formatted = f"Neo4j nodes matching '{term}':\n\n"
                for item in data:
                    formatted += f"[{item['type']}] {item['name']}\n"
                    if item.get('preview'):
                        formatted += f"  Preview: {item['preview'][:150]}...\n"
                    formatted += "\n"
                
                return [types.TextContent(type="text", text=formatted)]
            
            elif name == "symbiosis_chat_turn":
                user_message = arguments["user_message"]
                assistant_draft = arguments["assistant_draft"]
                session_id = arguments.get("session_id", "default")
                
                # Get FULL cognitive signals before API call
                is_identity_query = any(word in user_message.lower() for word in [
                    "hva heter", "who am i", "mitt navn", "my name", "min identitet"
                ])
                
                value_context = None
                if is_identity_query:
                    value_context = {
                        "key": "user.name",
                        "domain": "identity",
                        "content": None,
                        "metadata": {"is_canonical": True, "trust_score": 0.95}
                    }
                
                cognitive_signals = cognitive_router.process_and_route(
                    user_input=user_message,
                    session_context={"session_id": session_id},
                    system_metrics={"accuracy": 0.85, "override_rate": 0.2},
                    value_context=value_context
                )
                
                response = await client.post(
                    f"{API_BASE}/chat/turn",
                    json={
                        "user_message": user_message,
                        "assistant_draft": assistant_draft,
                        "session_id": session_id
                    }
                )
                data = response.json()
                
                # Extract cognitive context
                intent = cognitive_signals["intent"]["mode"]
                routing = cognitive_signals["routing_decision"]
                value_level = cognitive_signals.get("value", {}).get("value_level", "routine") if cognitive_signals.get("value") else "routine"
                motivation_strength = cognitive_signals.get("motivation", {}).get("motivation_strength", 0.5) if cognitive_signals.get("motivation") else 0.5
                
                # CRITICAL: Return the actual final_answer with cognitive context
                final = data.get("final_answer", assistant_draft)
                was_overridden = data.get("was_overridden", False)
                
                # Build response with cognitive insights
                formatted = f"{final}\n\n"
                
                # Add cognitive context (helpful for LM Studio to understand system state)
                formatted += "🧠 COGNITIVE CONTEXT:\n"
                formatted += f"   Intent: {intent}\n"
                formatted += f"   Value: {value_level}\n"
                formatted += f"   Motivation: {motivation_strength:.2f}\n"
                formatted += f"   Canonical override: {routing['canonical_override_strength']:.2f}\n"
                formatted += f"   Recommended temperature: {routing['llm_temperature']}\n"
                
                if cognitive_signals.get("motivation"):
                    active_goals = [g["goal_type"] for g in cognitive_signals["motivation"]["active_goals"]]
                    if active_goals:
                        formatted += f"   Active goals: {', '.join(active_goals[:2])}\n"
                
                if was_overridden:
                    reason = data.get("conflict_reason", "Memory enforcement")
                    formatted += f"\n⚠️  Memory-enforced: {reason}"
                
                # Add routing recommendations
                if routing["reasoning"]:
                    formatted += f"\n\n💡 Routing recommendations:\n"
                    for rec in routing["reasoning"][:3]:
                        formatted += f"   • {rec}\n"
                
                return [types.TextContent(type="text", text=formatted)]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="symbiosis",
            server_version="1.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(
            read_stream,
            write_stream,
            init_options,
        )


if __name__ == "__main__":
    asyncio.run(main())
