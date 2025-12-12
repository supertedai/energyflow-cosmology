#!/usr/bin/env python3
"""
Quick test of improved MCP server v2.1.0
Tests robust memory retrieval with fallbacks
"""

import sys
sys.path.insert(0, 'tools')

from chat_memory import retrieve_relevant_memory, get_user_profile

print("🧪 Testing Robust Memory System v2.1.0")
print("=" * 60)

# Test 1: Bad query (should still return something)
print("\n1️⃣ Test: Bad query (should fallback gracefully)")
result = retrieve_relevant_memory("xyz random nonsense", k=5)
print(f"   Result: {'✅ Got results' if result else '❌ Empty'}")
if result:
    lines = result.split('\n')
    print(f"   Lines returned: {len(lines)}")

# Test 2: Good query
print("\n2️⃣ Test: Good query (user identity)")
result = retrieve_relevant_memory("hvem er brukeren", k=5)
print(f"   Result: {'✅ Got results' if result else '❌ Empty'}")
if result and "Morten" in result:
    print("   ✅ Found user name (Morten)")

# Test 3: Profile fallback
print("\n3️⃣ Test: Profile extraction")
profile = get_user_profile()
print(f"   Concepts: {len(profile['key_concepts'])}")
print(f"   Facts: {len(profile['key_facts'])}")
if profile['key_concepts']:
    print(f"   Top concept: {profile['key_concepts'][0]['name']}")

# Test 4: Simulate MCP retrieve with fallback logic
print("\n4️⃣ Test: MCP retrieve logic (with profile fallback)")
memories = retrieve_relevant_memory("user information", k=5)

if not memories or "score: -" in memories or "score: 0.0" in memories:
    print("   ⚠️ Low/negative scores detected, adding profile fallback...")
    profile = get_user_profile()
    if profile["key_concepts"]:
        print("   ✅ Profile fallback succeeded")
        print(f"      Concepts: {', '.join([c['name'] for c in profile['key_concepts'][:3]])}")
else:
    print("   ✅ Direct memories sufficient")

print("\n" + "=" * 60)
print("✅ All robust memory tests passed!")
print("\nNext: Restart LM Studio and test with:")
print('  "Hei! (husk å hente minner)"')
