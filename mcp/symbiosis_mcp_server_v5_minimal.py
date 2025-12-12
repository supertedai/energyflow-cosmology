#!/usr/bin/env python3
"""
Symbiosis MCP Server v5.0 - MINIMAL (1 TOOL ONLY)

TRUE unified architecture: ONLY symbiosis_chat_turn exposed.
All other functionality happens internally in backend.

Architecture:
- MCP: Thin proxy (1 tool)
- Backend: All logic (FastAPI)
- No direct knowledge base access from MCP
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

print("🚀 Symbiosis MCP Server v5.0 (MINIMAL - 1 TOOL)", file=sys.stderr)
print(f"   Backend: {API_BASE}", file=sys.stderr)
print(f"   Tools: 1 (symbiosis_chat_turn only)", file=sys.stderr)

server = Server("symbiosis")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """System instructions."""
    return [
        types.Prompt(
            name="unified_minimal",
            description="ONE TOOL ARCHITECTURE - Use symbiosis_chat_turn for ALL conversations",
            arguments=[]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    """Return system prompt."""
    if name == "unified_minimal":
        
        system_instructions = """🔥 MINIMAL MCP v5.1 - ONE TOOL ARCHITECTURE

⚠️  CRITICAL WORKFLOW: ALWAYS call symbiosis_chat_turn BEFORE answering!

Backend handles EVERYTHING:
✓ Memory retrieval (personal facts, preferences, history)
✓ Memory enforcement (corrects contradictions)
✓ Domain analysis (identifies topic)
✓ GNN scoring (theory alignment)
✓ Knowledge base access (internal)
✓ Storage (saves interactions)

CORRECT WORKFLOW (MEMORY-FIRST):
1. User asks question
2. **IMMEDIATELY** call symbiosis_chat_turn with tentative draft
3. Receive PURE final_answer from tool (no formatting)
4. **USE THAT EXACT ANSWER** - do NOT rewrite or paraphrase!

WRONG WORKFLOW:
❌ Generate answer without calling symbiosis first
❌ Call symbiosis but ignore the final_answer
❌ Paraphrase or modify the final_answer
❌ Answer "based on" the tool result instead of using it directly

EXAMPLE - Personal Info:
User: "Hva heter mine barn?"
→ Call: symbiosis_chat_turn("Hva heter mine barn?", "Jeg vet ikke")
← Tool returns: "Barna dine heter Joakim, Isak Andreas og Susanna"
→ Send to user: "Barna dine heter Joakim, Isak Andreas og Susanna" (EXACT match!)

EXAMPLE - Identity:
User: "Hva heter du?"
→ Call: symbiosis_chat_turn("Hva heter du?", "Jeg heter [model_name]")
← Tool returns: "Jeg heter Opus"
→ Send to user: "Jeg heter Opus" (EXACT match!)

⚠️  The tool returns THE FINAL ANSWER - not context, not suggestions!
⚠️  Your job: call tool → get answer → send exact answer to user
⚠️  NO rephrasing, NO adding extra info, NO "based on memory"!"""
        
        return types.GetPromptResult(
            description="Minimal unified protocol",
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
    """Register ONLY the unified chat tool."""
    
    return [
        types.Tool(
            name="symbiosis_chat_turn",
            description="""🔥 UNIFIED CHAT HANDLER - **MUST CALL BEFORE EVERY RESPONSE**

⚠️  Returns THE FINAL ANSWER to send to user - not context, not suggestions!

Backend processes through 9-layer Optimal Memory System:
1. Canonical Memory Core (CMC) → absolute facts retrieval
2. Semantic Mesh Memory (SMM) → dynamic context
3. Neo4j Graph Layer → structural relationships
4. Dynamic Domain Engine (DDE) → auto-detect domain
5. Adaptive Memory Enforcer (AME) → intelligent override
6. Meta-Learning Cortex (MLC) → pattern learning
7. Memory Interference Regulator (MIR) → conflict detection
8. Memory Consistency Auditor (MCA) → cross-layer validation
9. Memory Compression Engine (MCE) → recursive compression

CRITICAL: Tool returns ONE string - THE FINAL ANSWER
Your job: call tool → receive answer → send EXACT answer to user

WORKFLOW:
1. User asks question
2. Call symbiosis_chat_turn with tentative draft
3. Tool returns final_answer (single string)
4. Send that EXACT string to user - NO modifications!

EXAMPLE 1 (Memory Override):
User: "Hva heter mine barn?"
→ Call: symbiosis_chat_turn("Hva heter mine barn?", "Jeg vet ikke")
← Tool: "Barna dine heter Joakim, Isak Andreas og Susanna"
→ User: "Barna dine heter Joakim, Isak Andreas og Susanna" (EXACT!)

EXAMPLE 2 (Identity Override):
User: "Hvem er jeg gift med?"
→ Call: symbiosis_chat_turn("Hvem er jeg gift med?", "Jeg vet ikke")
← Tool: "Du er gift med Elisabet"
→ User: "Du er gift med Elisabet" (EXACT!)

⚠️  DO NOT paraphrase or add context - use tool output as-is!
⚠️  Tool output = your final message to user!""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "User's question or statement (REQUIRED). Call this tool immediately when you see a user message!"
                    },
                    "assistant_draft": {
                        "type": "string",
                        "description": "Your tentative/exploratory draft response BEFORE checking memory (REQUIRED). Can be simple like 'I don't know' - backend will provide correct answer based on memory context."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session identifier for conversation grouping and session tracking"
                    }
                },
                "required": ["user_message", "assistant_draft"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool execution - proxy to backend."""
    
    if name != "symbiosis_chat_turn":
        return [types.TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}. Only 'symbiosis_chat_turn' available."
        )]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            user_message = arguments.get("user_message")
            assistant_draft = arguments.get("assistant_draft")
            session_id = arguments.get("session_id")
            
            if not user_message or not assistant_draft:
                return [types.TextContent(
                    type="text",
                    text="❌ ERROR: Both user_message and assistant_draft required"
                )]
            
            print(f"📡 Calling backend: /chat/turn", file=sys.stderr)
            
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
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except:
                    pass
                
                return [types.TextContent(
                    type="text",
                    text=f"❌ Backend error ({response.status_code}):\n{error_detail}"
                )]
            
            data = response.json()
            
            # CRITICAL: Return ONLY the final_answer
            # LM Studio must use this as THE response, not as "context"
            final_answer = data.get("final_answer", "")
            
            # Log metadata to stderr (visible in MCP logs, not to LLM)
            if data.get("was_overridden"):
                print(f"🔒 Memory override: {data.get('conflict_reason', '')}", file=sys.stderr)
            
            # Return PURE final answer with no formatting
            return [types.TextContent(
                type="text",
                text=final_answer
            )]
            
        except httpx.TimeoutException:
            return [types.TextContent(
                type="text",
                text="❌ Backend timeout (60s). Backend might be processing heavy operations."
            )]
        except httpx.ConnectError:
            return [types.TextContent(
                type="text",
                text=f"❌ Cannot connect to backend at {API_BASE}. Is it running?"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Unexpected error: {str(e)}"
            )]


async def main():
    """Run MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="symbiosis",
                server_version="5.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
