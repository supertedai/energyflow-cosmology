#!/usr/bin/env python3
"""
Test memory with facts - Verify Optimal Memory System works end-to-end
"""

from tools.optimal_memory_system import OptimalMemorySystem

print("🧪 Testing Optimal Memory System with real facts")
print("=" * 60)

# Initialize
memory = OptimalMemorySystem()

# Store a fact
print("\n1️⃣ Storing canonical fact: User name = Morten")
fact = memory.store_fact(
    key="user_name",
    value="Morten",
    domain="identity",
    fact_type="name",
    authority="LONGTERM",
    text="Brukeren heter Morten"
)
print(f"✅ Stored: {fact.id}")

# Query it back
print("\n2️⃣ Querying: Hva heter jeg?")
facts = memory.cmc.query_facts(
    query="Hva heter jeg?",
    domain="identity",
    k=3
)
print(f"Found {len(facts)} facts:")
for f in facts:
    print(f"   • {f.text} (authority: {f.authority}, confidence: {f.confidence})")

# Use full answer system
print("\n3️⃣ Full answer with memory enforcement")
from tools.symbiosis_router_v4 import handle_chat_turn

result = handle_chat_turn(
    user_message="Hva heter jeg?",
    assistant_draft="Du heter Andreas"
)

print(f"\nFinal answer: {result['final_answer']}")
print(f"Was overridden: {result['was_overridden']}")
print(f"Reason: {result['conflict_reason']}")
print(f"Memory used: {result['memory']}")
