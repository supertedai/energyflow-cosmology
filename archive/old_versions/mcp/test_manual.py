#!/usr/bin/env python3
"""
Quick test: Start MCP server manually and send a test request
"""
import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_chat_memory():
    """Test chat_memory_store directly"""
    print("🧪 Testing chat_memory_store import...\n")
    
    try:
        # Try to import the way MCP server does
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
        from chat_memory import store_chat_turn
        
        print("✅ Import successful!\n")
        
        # Test call
        print("Testing store_chat_turn...")
        result = store_chat_turn(
            user_message="Test MCP manual",
            assistant_message="Testing...",
            importance="medium"
        )
        
        print(f"\n✅ Result: {result}")
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        print(f"\nTraceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_chat_memory())
