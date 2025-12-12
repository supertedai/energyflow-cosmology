#!/usr/bin/env python3
"""
Populate canonical facts - Store all important personal information
"""

from tools.optimal_memory_system import OptimalMemorySystem

print("🧠 Populating Canonical Facts")
print("=" * 60)

# Initialize memory
memory = OptimalMemorySystem()

# Store all important facts
facts_to_store = [
    {
        "key": "user_name",
        "value": "Morten",
        "domain": "identity",
        "fact_type": "name",
        "authority": "LONGTERM",
        "text": "Brukeren heter Morten"
    },
    {
        "key": "user_spouse",
        "value": "Elisabet",
        "domain": "family",
        "fact_type": "relationship",
        "authority": "LONGTERM",
        "text": "Morten er gift med Elisabet"
    },
    {
        "key": "user_children_count",
        "value": 3,
        "domain": "family",
        "fact_type": "count",
        "authority": "LONGTERM",
        "text": "Morten har 3 barn"
    },
    {
        "key": "user_child_1",
        "value": "Joakim",
        "domain": "family",
        "fact_type": "name",
        "authority": "LONGTERM",
        "text": "Mortens første barn heter Joakim"
    },
    {
        "key": "user_child_2",
        "value": "Isak Andreas",
        "domain": "family",
        "fact_type": "name",
        "authority": "LONGTERM",
        "text": "Mortens andre barn heter Isak Andreas"
    },
    {
        "key": "user_child_3",
        "value": "Susanna",
        "domain": "family",
        "fact_type": "name",
        "authority": "LONGTERM",
        "text": "Mortens tredje barn heter Susanna"
    },
    {
        "key": "assistant_name",
        "value": "Opus",
        "domain": "identity",
        "fact_type": "name",
        "authority": "LONGTERM",
        "text": "AI-assistenten heter Opus"
    }
]

print(f"\n📝 Storing {len(facts_to_store)} canonical facts...")
print()

for fact_data in facts_to_store:
    fact = memory.store_fact(**fact_data)
    print(f"✅ {fact_data['key']}: {fact_data['value']} ({fact_data['domain']})")

print("\n" + "=" * 60)
print("✅ All facts stored!")
print()

# Verify
print("🔍 Verification - querying facts:")
print()

queries = [
    "Hva heter jeg?",
    "Hvem er jeg gift med?",
    "Hvor mange barn har jeg?",
    "Hva heter barna mine?",
    "Hva heter AI-assistenten?"
]

for query in queries:
    facts = memory.cmc.query_facts(query=query, k=3)
    print(f"Q: {query}")
    if facts:
        for f in facts:
            print(f"  → {f.text}")
    else:
        print("  → No facts found")
    print()
