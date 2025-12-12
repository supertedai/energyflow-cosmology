#!/usr/bin/env python3
"""
Test MCP server with chat_turn tool
"""
import asyncio
import json

async def test_mcp_chat():
    # Simulate MCP client calling symbiosis_chat_turn
    import sys
    sys.path.insert(0, '/Users/morpheus/energyflow-cosmology')
    
    from tools.symbiosis_router_v4 import handle_chat_turn
    
    print("🧪 Testing MCP chat_turn integration")
    print("=" * 60)
    
    # Test 1: Identity with override
    print("\n1️⃣ Test identity (should override)")
    result = handle_chat_turn(
        user_message="Hva heter jeg?",
        assistant_draft="Du heter Anders",
        session_id="mcp_test"
    )
    
    print(f"Final: {result['final_answer']}")
    print(f"Override: {result['was_overridden']}")
    print(f"Reason: {result['conflict_reason']}")
    print(f"Domain: {result['domain']}")
    print(f"Memory: {result['memory']}")
    
    # Test 2: Non-identity (should trust LLM)
    print("\n2️⃣ Test cosmology (should trust LLM)")
    result = handle_chat_turn(
        user_message="Hva er EFC?",
        assistant_draft="EFC står for Energy Flow Cosmology",
        session_id="mcp_test"
    )
    
    print(f"Final: {result['final_answer'][:100]}...")
    print(f"Override: {result['was_overridden']}")
    print(f"Domain: {result['domain']}")

asyncio.run(test_mcp_chat())
