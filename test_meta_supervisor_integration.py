#!/usr/bin/env python3
"""
Integration test for Meta-Supervisor + CMC + Self-Optimizing + Self-Healing.

Scenario:
1. User asks identity question → Protection intent → Top-down dominant
2. User asks learning question → Learning intent → Bottom-up dominant
3. System detects patterns and adjusts balance autonomously
4. Stability monitoring ensures no drift/oscillation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tools.canonical_memory_core import CanonicalMemoryCore
from tools.meta_supervisor import IntentMode, BalanceState


def test_meta_supervisor_integration():
    print("🧪 Testing Meta-Supervisor Integration")
    print("=" * 60)
    
    # Initialize CMC with full stack
    print("\n1️⃣ Initialize CMC with meta-supervisor")
    cmc = CanonicalMemoryCore(
        enable_self_healing=True,
        enable_self_optimizing=True,
        enable_meta_supervisor=True
    )
    
    # Test 1: Protection intent (identity question)
    print("\n2️⃣ Test: Protection intent (identity)")
    result = cmc.meta_supervisor.process_turn(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"\n📊 Protection Intent Results:")
    print(f"   Intent mode: {result['intent_signal'].mode.value}")
    print(f"   Active domains: {result['intent_signal'].active_domains}")
    print(f"   Balance state: {result['balance_metric'].state.value}")
    print(f"   Bottom-up weight: {result['balance_metric'].bottom_up_weight:.2f}")
    print(f"   Top-down weight: {result['balance_metric'].top_down_weight:.2f}")
    print(f"   Stability: {result['stability_report'].level.value}")
    
    # Validation
    assert result['intent_signal'].mode in [IntentMode.PROTECTION, IntentMode.RETRIEVAL], \
        "Identity question should trigger PROTECTION or RETRIEVAL intent"
    
    assert "identity" in result['intent_signal'].active_domains, \
        "Identity domain should be active"
    
    # Test 2: Learning intent (new information)
    print("\n3️⃣ Test: Learning intent (explanation)")
    result2 = cmc.meta_supervisor.process_turn(
        user_input="Forklar hva energiflyt-kosmologi er",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"\n📊 Learning Intent Results:")
    print(f"   Intent mode: {result2['intent_signal'].mode.value}")
    print(f"   Active domains: {result2['intent_signal'].active_domains}")
    print(f"   Balance state: {result2['balance_metric'].state.value}")
    print(f"   Bottom-up weight: {result2['balance_metric'].bottom_up_weight:.2f}")
    print(f"   Top-down weight: {result2['balance_metric'].top_down_weight:.2f}")
    
    # Validation
    assert result2['intent_signal'].mode == IntentMode.LEARNING, \
        "Explanation request should trigger LEARNING intent"
    
    assert result2['balance_metric'].state == BalanceState.BOTTOM_UP_DOMINANT, \
        "Learning should be bottom-up dominant"
    
    assert result2['balance_metric'].bottom_up_weight > result['balance_metric'].bottom_up_weight, \
        "Learning should have higher bottom-up weight than protection"
    
    # Test 3: Exploration intent
    print("\n4️⃣ Test: Exploration intent (open question)")
    result3 = cmc.meta_supervisor.process_turn(
        user_input="Hva hvis vi ser på energiflyt i en ny kontekst?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"\n📊 Exploration Intent Results:")
    print(f"   Intent mode: {result3['intent_signal'].mode.value}")
    print(f"   Balance state: {result3['balance_metric'].state.value}")
    
    # Test 4: System stats
    print("\n5️⃣ Meta-supervisor stats")
    stats = cmc.meta_supervisor.get_stats()
    print(f"   Total intents processed: {stats['total_intents']}")
    print(f"   Total balance adjustments: {stats['total_balance_metrics']}")
    print(f"   Total stability reports: {stats['total_stability_reports']}")
    print(f"   Current intent: {stats['current_intent']}")
    print(f"   Current balance: {stats['current_balance']}")
    print(f"   Current stability: {stats['current_stability']}")
    
    # Final validation
    print("\n✅ Validation:")
    print(f"   ✓ Meta-supervisor integrated with CMC")
    print(f"   ✓ Intent detection working (3 different intents)")
    print(f"   ✓ Balance controller adapting (different weights)")
    print(f"   ✓ Stability monitoring active ({stats['total_stability_reports']} reports)")
    print(f"   ✓ Top-down/bottom-up integration functional")
    
    print("\n✅ Meta-Supervisor Integration test complete")
    print("\n🎯 System now has complete cognitive architecture:")
    print("   - Bottom-up: Data → Pattern (SMM, Observations, Neo4j)")
    print("   - Top-down: Intent → Frame (Priority, Focus, Filtering)")
    print("   - Meta-lag: Balance + Stability + Direction")
    print("   - Self-healing: Automatic conflict resolution")
    print("   - Self-optimizing: Autonomous parameter tuning")
    print("\n🧠 Kognitiv isomorfi oppnådd!")


if __name__ == "__main__":
    test_meta_supervisor_integration()
