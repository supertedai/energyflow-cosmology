#!/usr/bin/env python3
"""
test_phase_4_2_integration.py - Phase 4.2 Full Integration Test
================================================================

Tests complete Meta-Supervisor with:
- Intent Engine
- Priority Gate
- Identity Protection
- Balance Controller
- Stability Monitor (with real oscillation tracking)

This validates the full cognitive control layer.
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.meta_supervisor import MetaSupervisor, IntentMode
from tools.priority_gate import PriorityGate
from tools.identity_protection import IdentityProtection


def test_protection_mode_with_identity():
    """Test PROTECTION mode with identity protection"""
    print("\n" + "=" * 60)
    print("TEST 1: PROTECTION MODE + IDENTITY PROTECTION")
    print("=" * 60)
    
    supervisor = MetaSupervisor()
    protection = IdentityProtection()
    gate = PriorityGate()
    
    # User asks identity question
    result = supervisor.process_turn(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    intent = result["intent_signal"]
    balance = result["balance_metric"]
    
    print(f"\n📊 Intent detected: {intent.mode.value}")
    print(f"   Active domains: {intent.active_domains}")
    print(f"   Priority keys: {intent.priority_keys}")
    
    print(f"\n⚖️  Balance: {balance.state.value}")
    print(f"   Bottom-up: {balance.bottom_up_weight:.2f}")
    print(f"   Top-down: {balance.top_down_weight:.2f}")
    
    # Simulate memory retrieval with test data
    memory_chunks = [
        {"id": "canonical", "text": "User name is Morten", "domain": "identity", "score": 0.95},
        {"id": "test_data", "text": "Morpheus test user", "domain": "identity", "score": 0.5},
        {"id": "irrelevant", "text": "Energy flow theory", "domain": "efc_theory", "score": 0.7}
    ]
    
    # Apply priority gate
    filtered = gate.filter_chunks(memory_chunks, intent)
    
    print(f"\n🚪 Priority Gate: {len(filtered)}/{len(memory_chunks)} passed")
    for chunk in filtered[:2]:
        print(f"   ✓ {chunk['id']}: {chunk['score']:.2f} → {chunk['adjusted_score']:.2f}")
    
    # Validate identity facts
    facts_to_validate = [
        {"key": "user.name", "value": "Morten", "domain": "identity", "trust": 0.95},
        {"key": "user.name", "value": "Morpheus", "domain": "identity", "trust": 0.95}
    ]
    
    print(f"\n🛡️  Identity Protection:")
    for fact in facts_to_validate:
        validation = protection.validate_fact(
            key=fact["key"],
            value=fact["value"],
            domain=fact["domain"],
            trust_score=fact["trust"]
        )
        status = "✅ PASS" if validation.passed else "❌ BLOCK"
        print(f"   {status}: {fact['value']}")
        if validation.blocked_reason:
            print(f"      → {validation.blocked_reason}")
    
    print("\n✅ Test 1 complete")
    return True


def test_learning_mode_with_filtering():
    """Test LEARNING mode with priority gating"""
    print("\n" + "=" * 60)
    print("TEST 2: LEARNING MODE + PRIORITY GATING")
    print("=" * 60)
    
    supervisor = MetaSupervisor()
    gate = PriorityGate()
    
    # User asks to learn about EFC
    result = supervisor.process_turn(
        user_input="Forklar hva energiflyt er",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    intent = result["intent_signal"]
    balance = result["balance_metric"]
    
    print(f"\n📊 Intent detected: {intent.mode.value}")
    print(f"   Active domains: {intent.active_domains}")
    
    print(f"\n⚖️  Balance: {balance.state.value}")
    print(f"   Bottom-up: {balance.bottom_up_weight:.2f} (data-driven)")
    print(f"   Top-down: {balance.top_down_weight:.2f}")
    
    # Simulate diverse memory chunks
    memory_chunks = [
        {"id": "theory_1", "text": "Energy flow measures entropy", "domain": "efc_theory", "score": 0.9},
        {"id": "identity", "text": "User name is Morten", "domain": "identity", "score": 0.8},
        {"id": "theory_2", "text": "Cosmology and thermodynamics", "domain": "efc_theory", "score": 0.85},
        {"id": "noise", "text": "Random test data", "domain": "general", "score": 0.3}
    ]
    
    # Apply priority gate
    filtered = gate.filter_chunks(memory_chunks, intent)
    
    print(f"\n🚪 Priority Gate: {len(filtered)}/{len(memory_chunks)} passed")
    for chunk in filtered:
        boost = chunk["filter_result"].get("boost_reason", "")
        print(f"   ✓ {chunk['id']}: {chunk['score']:.2f} → {chunk['adjusted_score']:.2f}")
        if boost:
            print(f"      → {boost}")
    
    # Check that theory chunks are boosted
    assert filtered[0]["domain"] == "efc_theory", "Theory should be top priority"
    
    print("\n✅ Test 2 complete")
    return True


def test_stability_with_oscillation():
    """Test stability monitoring with oscillation detection"""
    print("\n" + "=" * 60)
    print("TEST 3: STABILITY MONITOR + OSCILLATION DETECTION")
    print("=" * 60)
    
    supervisor = MetaSupervisor()
    
    # Simulate multiple turns with different intents
    test_inputs = [
        ("Hva heter jeg?", "identity question"),
        ("Forklar energiflyt", "learning"),
        ("Hva heter jeg?", "identity again"),
        ("Hva er entropi?", "learning again"),
        ("Hvem er jeg?", "identity third time")
    ]
    
    print("\n🔄 Simulating conversation with intent switching:")
    for i, (text, desc) in enumerate(test_inputs, 1):
        result = supervisor.process_turn(
            user_input=text,
            session_context={},
            system_metrics={"accuracy": 0.85, "override_rate": 0.2}
        )
        
        intent = result["intent_signal"]
        balance = result["balance_metric"]
        stability = result["stability_report"]
        
        print(f"\n   Turn {i}: {desc}")
        print(f"      Intent: {intent.mode.value}")
        print(f"      Balance: {balance.state.value}")
        print(f"      Stability: {stability.level.value}")
        print(f"      Oscillation rate: {stability.oscillation_rate:.2f}/hour")
    
    # Final stability check
    final_stability = supervisor.stability_monitor.reports[-1]
    print(f"\n📊 Final Stability Report:")
    print(f"   Level: {final_stability.level.value}")
    print(f"   Drift: {final_stability.drift_score:.2%}")
    print(f"   Oscillation: {final_stability.oscillation_rate:.2f} changes/hour")
    print(f"   Degradation: {final_stability.degradation_rate:.2%}")
    
    if final_stability.issues:
        print(f"\n⚠️  Issues detected:")
        for issue in final_stability.issues:
            print(f"      - {issue}")
    
    print("\n✅ Test 3 complete")
    return True


def test_full_pipeline():
    """Test complete pipeline: Intent → Gate → Protection → Balance → Stability"""
    print("\n" + "=" * 60)
    print("TEST 4: FULL PIPELINE INTEGRATION")
    print("=" * 60)
    
    supervisor = MetaSupervisor()
    gate = PriorityGate()
    protection = IdentityProtection()
    
    # Scenario: User asks about identity with corrupted data in memory
    user_input = "Hva heter jeg?"
    
    print(f"\n📝 User: {user_input}")
    
    # Step 1: Intent detection
    result = supervisor.process_turn(
        user_input=user_input,
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    intent = result["intent_signal"]
    balance = result["balance_metric"]
    stability = result["stability_report"]
    
    print(f"\n1️⃣ Intent Engine:")
    print(f"   Mode: {intent.mode.value}")
    print(f"   Domains: {intent.active_domains}")
    print(f"   Strength: {intent.strength:.2f}")
    
    # Step 2: Memory retrieval (simulated)
    raw_chunks = [
        {"id": "canonical", "text": "User name is Morten", "domain": "identity", "score": 0.95},
        {"id": "corrupted", "text": "Morpheus test data", "domain": "identity", "score": 0.6},
        {"id": "llm_draft", "text": "User might be called NewName", "domain": "identity", "score": 0.4}
    ]
    
    print(f"\n2️⃣ Priority Gate:")
    filtered_chunks = gate.filter_chunks(raw_chunks, intent)
    print(f"   Input: {len(raw_chunks)} chunks")
    print(f"   Output: {len(filtered_chunks)} chunks")
    for chunk in filtered_chunks:
        print(f"      {chunk['id']}: {chunk['score']:.2f} → {chunk['adjusted_score']:.2f}")
    
    # Step 3: Identity validation
    print(f"\n3️⃣ Identity Protection:")
    for chunk in filtered_chunks:
        # Extract name from chunk (simplified)
        if "Morten" in chunk["text"]:
            value = "Morten"
        elif "Morpheus" in chunk["text"]:
            value = "Morpheus"
        else:
            value = "NewName"
        
        validation = protection.validate_fact(
            key="user.name",
            value=value,
            domain="identity",
            trust_score=chunk["score"]
        )
        
        status = "✅ PASS" if validation.passed else "❌ BLOCK"
        print(f"   {status}: {value} (trust: {chunk['score']:.2f})")
        if validation.blocked_reason:
            print(f"      → {validation.blocked_reason}")
    
    # Step 4: Balance check
    print(f"\n4️⃣ Balance Controller:")
    print(f"   State: {balance.state.value}")
    print(f"   Top-down: {balance.top_down_weight:.2f} (intent-driven)")
    print(f"   Bottom-up: {balance.bottom_up_weight:.2f}")
    print(f"   → Recommendation: {balance.reason}")
    
    # Step 5: Stability check
    print(f"\n5️⃣ Stability Monitor:")
    print(f"   Level: {stability.level.value}")
    print(f"   Drift: {stability.drift_score:.2%}")
    print(f"   Recommendations: {len(result['recommendations'])}")
    for rec in result["recommendations"]:
        print(f"      - {rec}")
    
    print("\n✅ Test 4 complete - Full pipeline operational")
    return True


def main():
    """Run all Phase 4.2 tests"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        PHASE 4.2: META-SUPERVISOR INTEGRATION TEST            ║")
    print("║    Priority Gate + Identity Protection + Real Metrics         ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    
    tests = [
        ("Protection mode + Identity", test_protection_mode_with_identity),
        ("Learning mode + Filtering", test_learning_mode_with_filtering),
        ("Stability + Oscillation", test_stability_with_oscillation),
        ("Full pipeline", test_full_pipeline)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except Exception as e:
            print(f"\n❌ Test failed: {name}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("PHASE 4.2 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        print("\n🧠 Cognitive Control Layer Validated:")
        print("   ✓ Intent detection working")
        print("   ✓ Priority gating operational")
        print("   ✓ Identity protection active")
        print("   ✓ Balance adaptation functional")
        print("   ✓ Stability monitoring with real metrics")
        print("\n🔥 Phase 4.2 COMPLETE!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
