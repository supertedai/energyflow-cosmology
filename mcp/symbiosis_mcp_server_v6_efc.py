#!/usr/bin/env python3
"""
Symbiosis MCP Server v6.0 - EFC META-LEARNING INTEGRATION

Extends v5 minimal with EFC pattern learning and Msty AI context.

Architecture:
- MCP: Thin proxy + EFC tools
- Backend: All logic (FastAPI)
- Layer 9: Cross-domain validation mesh exposed
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

print("🚀 Symbiosis MCP Server v6.0 (EFC + Layer 9)", file=sys.stderr)
print(f"   Backend: {API_BASE}", file=sys.stderr)
print(f"   Features: Chat, EFC Learning, Msty Context", file=sys.stderr)

server = Server("symbiosis-efc")


@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """System instructions."""
    return [
        types.Prompt(
            name="unified_efc",
            description="EFC-augmented chat with cross-domain learning",
            arguments=[]
        )
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    """Return system prompt."""
    if name == "unified_efc":
        
        system_instructions = """🔥 MCP v6.0 - EFC META-LEARNING ARCHITECTURE

⚠️  CRITICAL: ALWAYS call symbiosis_chat_turn FIRST!

NEW CAPABILITIES (Layer 9):
✓ EFC pattern detection (adaptive learning)
✓ Cross-domain validation mesh
✓ Universal pattern discovery (≥3 domains)
✓ Automatic activation in new domains

WORKFLOW:
1. User asks question
2. Call symbiosis_chat_turn (gets memory + EFC context)
3. Use final_answer from backend (may include EFC augmentation)
4. Optionally: Check EFC patterns for deeper analysis

EXAMPLE - EFC Augmentation:
User: "Hvorfor stabiliserer galakser seg?"
→ symbiosis_chat_turn("Hvorfor stabiliserer galakser seg?", "Draft...")
← Backend: {efc_score: 6.5, efc_reasoning: "...", final_answer: "..."}
→ EFC was detected and used to augment answer

EXAMPLE - Cross-Domain Learning:
User provides feedback: "That was helpful!"
→ efc_record_feedback(question, domain, was_helpful=true)
← System learns pattern, may generalize to other domains

⚠️  Call symbiosis_chat_turn FIRST, always!"""
        
        return types.GetPromptResult(
            description="EFC-augmented unified protocol",
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
    """Register unified chat + EFC tools."""
    
    return [
        types.Tool(
            name="symbiosis_chat_turn",
            description="""🔥 UNIFIED CHAT HANDLER - **ALWAYS CALL THIS FIRST**

Processes every interaction through backend pipeline including:
- Memory retrieval (personal facts, history)
- EFC pattern detection (Layer 9 learning)
- Domain analysis
- Knowledge base access
- Storage

WORKFLOW:
1. Receive user question
2. Call symbiosis_chat_turn with tentative draft
3. Get memory context + EFC analysis + final answer
4. Send final_answer to user

Returns:
- final_answer: Corrected response (use this!)
- efc_score: Pattern relevance (0-8+)
- efc_reasoning: Why EFC was used
- memory_used: Context from longterm storage""",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "User's question or statement"
                    },
                    "assistant_draft": {
                        "type": "string",
                        "description": "Your tentative draft (can be simple)"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID"
                    }
                },
                "required": ["user_message", "assistant_draft"]
            }
        ),
        
        types.Tool(
            name="efc_detect_pattern",
            description="""🎯 DETECT EFC PATTERNS IN QUESTION

Analyzes question for EFC relevance using Layer 9 adaptive learning.

Use when:
- Need to check if EFC is relevant before answering
- Want to understand WHY question triggers EFC
- Analyzing domain-specific patterns

Returns:
- score: 0-8+ (higher = more relevant)
- relevance_level: OUT_OF_SCOPE, WEAK_SIGNAL, EFC_RELEVANT, EFC_ENABLED
- detected_patterns: List of patterns found
- reasoning: Explanation of score""",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to analyze"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain context (e.g., 'cosmology', 'biology')"
                    }
                },
                "required": ["question"]
            }
        ),
        
        types.Tool(
            name="efc_record_feedback",
            description="""📊 RECORD USER FEEDBACK (ADAPTIVE LEARNING)

Records whether EFC augmentation was helpful.
Enables Layer 9 cross-domain learning.

Use when:
- User confirms answer was helpful
- User says answer wasn't useful
- After providing EFC-augmented response

System learns:
- Which patterns work in which domains
- When to activate EFC automatically
- Universal patterns (validated in ≥3 domains)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Original question"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain where pattern was used"
                    },
                    "was_helpful": {
                        "type": "boolean",
                        "description": "Whether EFC augmentation helped"
                    }
                },
                "required": ["question", "domain", "was_helpful"]
            }
        ),
        
        types.Tool(
            name="efc_get_universal_patterns",
            description="""🌍 GET UNIVERSAL EFC PATTERNS

Returns patterns validated in multiple domains (≥3).
These are EFC principles discovered through cross-domain learning.

Use when:
- Want to see what the system has learned
- Checking if a pattern is universal
- Understanding system's knowledge state

Returns:
- List of patterns with domains, confidence, success rate""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        
        types.Tool(
            name="msty_get_context",
            description="""🎯 GET LIVE CONTEXT FOR MSTY AI

Retrieves comprehensive context for current conversation:
- Semantic memory (relevant past interactions)
- EFC pattern detection
- Related concepts from knowledge graph
- Conversation-aware recommendations

Use in Msty AI for:
- Understanding conversation context
- Getting relevant background
- EFC augmentation decisions

Returns complete context package.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Current query"
                    },
                    "conversation_history": {
                        "type": "array",
                        "description": "Recent conversation turns",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain context"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool execution - proxy to backend."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Route to appropriate backend endpoint
            if name == "symbiosis_chat_turn":
                response = await client.post(
                    f"{API_BASE}/chat/turn",
                    json=arguments
                )
            
            elif name == "efc_detect_pattern":
                response = await client.post(
                    f"{API_BASE}/efc/detect-pattern",
                    json=arguments
                )
            
            elif name == "efc_record_feedback":
                response = await client.post(
                    f"{API_BASE}/efc/feedback",
                    json=arguments
                )
            
            elif name == "efc_get_universal_patterns":
                response = await client.get(
                    f"{API_BASE}/efc/universal-patterns"
                )
            
            elif name == "msty_get_context":
                response = await client.post(
                    f"{API_BASE}/msty/context",
                    json=arguments
                )
            
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]
            
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
            
            # Format response based on tool
            if name == "symbiosis_chat_turn":
                return format_chat_response(data)
            elif name == "efc_detect_pattern":
                return format_pattern_response(data)
            elif name == "efc_record_feedback":
                return [types.TextContent(type="text", text="✅ Feedback recorded")]
            elif name == "efc_get_universal_patterns":
                return format_universal_patterns(data)
            elif name == "msty_get_context":
                return format_msty_context(data)
            
        except httpx.TimeoutException:
            return [types.TextContent(
                type="text",
                text="❌ Backend timeout - request took too long"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )]


def format_chat_response(data: dict) -> list[types.TextContent]:
    """
    Format chat turn response.
    
    CRITICAL: Return ONLY the final_answer - no formatting!
    LM Studio must use this as THE response, not as context.
    """
    final_answer = data.get("final_answer", "")
    
    # Log metadata to stderr (visible in logs, not to LLM)
    if data.get("was_overridden"):
        print(f"🔒 Memory override: {data.get('conflict_reason', '')}", file=sys.stderr)
    if data.get("efc_score", 0) > 0:
        print(f"⚡ EFC score: {data.get('efc_score', 0):.1f}", file=sys.stderr)
    
    # Return PURE final answer with no formatting
    return [types.TextContent(type="text", text=final_answer)]


def format_pattern_response(data: dict) -> list[types.TextContent]:
    """Format EFC pattern detection response."""
    parts = [
        f"🎯 EFC Pattern Detection",
        f"Score: {data.get('score', 0):.1f}/8",
        f"Level: {data.get('relevance_level', 'N/A')}",
        "",
        f"Detected Patterns: {', '.join(data.get('detected_patterns', []))}",
        "",
        f"Reasoning: {data.get('reasoning', 'N/A')}",
        "",
        f"Should Augment: {'✅ Yes' if data.get('should_augment') else '❌ No'}",
        f"Should Override: {'✅ Yes' if data.get('should_override') else '❌ No'}"
    ]
    
    return [types.TextContent(type="text", text="\n".join(parts))]


def format_universal_patterns(patterns: list) -> list[types.TextContent]:
    """Format universal patterns response."""
    if not patterns:
        return [types.TextContent(type="text", text="No universal patterns discovered yet.")]
    
    parts = [f"🌍 Universal EFC Patterns ({len(patterns)} found)", ""]
    
    for p in patterns:
        parts.extend([
            f"Pattern: {p['pattern']}",
            f"  Domains: {', '.join(p['domains'])}",
            f"  Occurrences: {p['total_occurrences']}",
            f"  Success Rate: {p['success_rate']*100:.1f}%",
            f"  Confidence: {p['confidence']:.2f}",
            ""
        ])
    
    return [types.TextContent(type="text", text="\n".join(parts))]


def format_msty_context(data: dict) -> list[types.TextContent]:
    """Format Msty context response."""
    parts = [
        "🎯 Live Context for Msty AI",
        "",
        f"Query: {data.get('query', 'N/A')}",
        f"EFC Detected: {'✅ Yes' if data.get('efc_pattern_detected') else '❌ No'}",
        f"EFC Score: {data.get('efc_score', 0):.1f}",
        f"Should Use EFC: {'✅ Yes' if data.get('should_use_efc') else '❌ No'}",
        "",
        "Related Concepts:",
        *[f"  - {c}" for c in data.get('related_concepts', [])[:5]],
        "",
        f"Reasoning: {data.get('efc_reasoning', 'N/A')}"
    ]
    
    return [types.TextContent(type="text", text="\n".join(parts))]


async def main():
    """Run MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="symbiosis-efc",
            server_version="6.0.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )
        
        await server.run(
            read_stream,
            write_stream,
            init_options
        )


if __name__ == "__main__":
    asyncio.run(main())
