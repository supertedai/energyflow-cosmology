#!/usr/bin/env python3
"""
test_self_healing_integration.py - Test Self-Healing Layer Integration
========================================================================

Tests the integration of SelfHealingCanonical in CanonicalMemoryCore.

Scenarios:
1. CLI test data should NOT pollute canonical truth
2. Multiple consistent user statements should create canonical truth
3. Conflicts should be resolved by authority weighting
4. Test + user data → user wins
"""

import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from tools.canonical_memory_core import CanonicalMemoryCore

print("🧪 Testing Self-Healing Integration")
print("=" * 60)

# Initialize CMC with self-healing
cmc = CanonicalMemoryCore(enable_self_healing=True)

# Test 1: CLI test data
print("\n1️⃣ Store CLI test data (should be isolated)")
try:
    fact1 = cmc.store_fact(
        key="user_name",
        value="Morpheus",
        domain="identity",
        fact_type="name",
        authority="SHORT_TERM",
        source="cli_test"
    )
    print(f"   Stored: {fact1.value}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: User says name multiple times
print("\n2️⃣ User says name 3 times")
for i in range(3):
    try:
        fact2 = cmc.store_fact(
            key="user_name",
            value="Morten",
            domain="identity",
            fact_type="name",
            authority="SHORT_TERM",
            source="user"
        )
        print(f"   Stored: {fact2.value}")
    except Exception as e:
        print(f"   Error: {e}")

# Test 3: Query canonical truth
print("\n3️⃣ Query canonical truth")
if cmc.self_healing:
    canonical = cmc.self_healing.get_canonical_truth("identity", "user_name")
    print(f"   Canonical name: {canonical}")
    print(f"   Expected: Morten (user wins over cli_test)")
    
    # Stats
    stats = cmc.self_healing.get_stats()
    print(f"\n📊 System stats:")
    print(f"   Observations: {stats['total_observations']}")
    print(f"   Facts: {stats['total_facts']}")
    print(f"   Conflicts: {stats['unresolved_conflicts']}")

print("\n✅ Self-Healing Integration test complete")
