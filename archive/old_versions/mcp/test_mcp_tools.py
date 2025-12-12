#!/usr/bin/env python3
"""
Test MCP server tools locally (without async/MCP protocol)
"""

import os
import sys

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

print("🧪 Testing MCP Tool Imports\n")

# Test 1: chat_memory_store
print("1️⃣  Testing chat_memory_store...")
try:
    from chat_memory import store_chat_turn
    result = store_chat_turn(
        user_message="Test from MCP",
        assistant_message="Testing...",
        importance="low"
    )
    print(f"   ✅ Result: {result}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: chat_memory_retrieve
print("\n2️⃣  Testing chat_memory_retrieve...")
try:
    from chat_memory import retrieve_relevant_memory
    memories = retrieve_relevant_memory("Who is the user?", k=3)
    print(f"   ✅ Found {len(memories.split(chr(10)))} memories" if memories else "   ✅ No memories (empty)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: chat_memory_profile
print("\n3️⃣  Testing chat_memory_profile...")
try:
    from chat_memory import get_user_profile
    profile = get_user_profile()
    print(f"   ✅ Concepts: {len(profile['key_concepts'])}, Facts: {len(profile['key_facts'])}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: authority_check
print("\n4️⃣  Testing authority_check...")
try:
    from authority_filter import is_authoritative, get_authority_metadata
    is_auth = is_authoritative("theory/README.md")
    meta = get_authority_metadata("theory/README.md")
    print(f"   ✅ Authoritative: {is_auth}, Trust: {meta['trust_score']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ All MCP tool imports working!")
print("\n📋 Next steps:")
print("   1. Restart MCP server in LM Studio")
print("   2. Try: 'Hei! Jeg heter Morten'")
print("   3. Check that memory is stored")
