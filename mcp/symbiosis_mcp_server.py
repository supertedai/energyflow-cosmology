#!/usr/bin/env python3
"""
Symbiosis MCP Server for LM Studio
Exposes Qdrant, Neo4j, and Graph-RAG through Model Context Protocol
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

# Symbiosis API base URL (assumes local or remote deployment)
API_BASE = os.getenv("SYMBIOSIS_API_URL", "http://localhost:8000")

server = Server("symbiosis")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Register Symbiosis tools for LM Studio."""
    return [
        types.Tool(
            name="symbiosis_vector_search",
            description="Search Symbiosis knowledge base using semantic vector search (Qdrant). Returns relevant documents with similarity scores.",
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
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls from LM Studio."""
    
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
                
                # Format results for LM
                if data.get("status") == "ok":
                    results = data.get("results", [])
                    formatted = f"Found {len(results)} results:\n\n"
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
