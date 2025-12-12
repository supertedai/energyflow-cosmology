#!/usr/bin/env python3
"""
test_phase_5_value_layer.py - Integration test for Phase 5
==========================================================

Tests Value Layer integration with Meta-Supervisor:
1. Critical value detection (identity)
2. Harm detection (identity corruption)
3. Value-based decision making (intent + value)
4. Full pipeline (intent → value → decision)
"""

from tools.meta_supervisor import MetaSupervisor
from tools.value_layer import ValueLayer, ValueLevel, HarmType


def test_critical_value_detection():
    """Test 1: Critical value detection for identity"""
    print("\n" + "=" * 60)
    print("TEST 1: Critical Value Detection (Identity)")
    print("=" * 60)
    
    value_layer = ValueLayer()
    
    # Classify identity fact
    value_signal = value_layer.classify_value(
        key="user.name",
        domain="identity",
        content="Morten",
        metadata={"trust_score": 0.95, "is_canonical": True}
    )
    
    print(f"Key: user.name")
    print(f"Value level: {value_signal.value_level.value}")
    print(f"Reasoning: {value_signal.reasoning}")
    print(f"Override intent: {value_signal.override_intent}")
    
    # Assertions
    assert value_signal.value_level == ValueLevel.CRITICAL, "Identity should be CRITICAL"
    assert value_signal.override_intent == True, "CRITICAL should override intent"
    assert "identity" in value_signal.domains, "Domain should include identity"
    
    print("\n✅ Test 1 PASSED: Identity correctly classified as CRITICAL")


def test_harm_detection():
    """Test 2: Harm detection for identity corruption"""
    print("\n" + "=" * 60)
    print("TEST 2: Harm Detection (Identity Corruption)")
    print("=" * 60)
    
    value_layer = ValueLayer()
    
    # Test identity corruption: "Morpheus" when canonical is "Morten"
    harm_signals = value_layer.detect_harm(
        key="user.name",
        proposed_value="Morpheus",
        canonical_value="Morten",
        trust_score=0.5
    )
    
    print(f"Proposed: Morpheus (blocked pattern)")
    print(f"Canonical: Morten")
    print(f"Trust: 0.5")
    print(f"Harms detected: {len(harm_signals)}")
    
    for i, harm in enumerate(harm_signals, 1):
        print(f"\n  Harm {i}:")
        print(f"    Type: {harm.harm_type.value}")
        print(f"    Severity: {harm.severity}")
        print(f"    Action: {harm.recommended_action}")
        print(f"    Evidence: {harm.evidence}")
    
    # Assertions
    assert len(harm_signals) > 0, "Should detect harm"
    assert any(h.harm_type == HarmType.IDENTITY_CORRUPTION for h in harm_signals), "Should detect identity corruption"
    assert any(h.severity >= 0.8 for h in harm_signals), "Should be high severity"
    assert any("BLOCK" in h.recommended_action for h in harm_signals), "Should recommend blocking"
    
    print("\n✅ Test 2 PASSED: Identity corruption correctly detected and blocked")


def test_value_based_decision():
    """Test 3: Value-based decision making (intent + value)"""
    print("\n" + "=" * 60)
    print("TEST 3: Value-based Decision (PROTECTION + CRITICAL)")
    print("=" * 60)
    
    value_layer = ValueLayer()
    
    # Scenario: Protection intent + Critical value
    decision = value_layer.make_decision(
        intent_signal={"mode": "protection"},
        key="user.name",
        domain="identity",
        content="Morten",
        metadata={"trust_score": 0.95, "is_canonical": True}
    )
    
    print(f"Intent mode: {decision.intent_mode}")
    print(f"Value level: {decision.value_level.value}")
    print(f"Final priority: {decision.final_priority:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Harm detected: {decision.harm_detected}")
    
    # Assertions
    assert decision.intent_mode == "protection", "Should be protection mode"
    assert decision.value_level == ValueLevel.CRITICAL, "Should be CRITICAL value"
    assert decision.final_priority == 1.0, "CRITICAL + PROTECTION should be max priority"
    assert "CRITICAL_VALUE_OVERRIDE" in decision.reasoning, "Should indicate override"
    
    print("\n✅ Test 3 PASSED: Value-based decision correctly prioritizes CRITICAL + PROTECTION")


def test_full_pipeline():
    """Test 4: Full pipeline (Meta-Supervisor + Value Layer)"""
    print("\n" + "=" * 60)
    print("TEST 4: Full Pipeline Integration")
    print("=" * 60)
    
    supervisor = MetaSupervisor(enable_value_layer=True)
    
    # Scenario: "Hva heter jeg?" with value context
    result = supervisor.process_turn(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2},
        value_context={
            "key": "user.name",
            "domain": "identity",
            "content": "Morten",
            "metadata": {"trust_score": 0.95, "is_canonical": True},
            "harm_context": {
                "key": "user.name",
                "proposed_value": "Morten",
                "canonical_value": "Morten",
                "trust_score": 0.95
            }
        }
    )
    
    print(f"User input: 'Hva heter jeg?'")
    print(f"\nIntent detected: {result['intent_signal'].mode.value}")
    print(f"Balance state: {result['balance_metric'].state.value}")
    print(f"  Bottom-up: {result['balance_metric'].bottom_up_weight:.2f}")
    print(f"  Top-down: {result['balance_metric'].top_down_weight:.2f}")
    print(f"Stability: {result['stability_report'].level.value}")
    
    if "value_decision" in result:
        vd = result["value_decision"]
        print(f"\nValue decision:")
        print(f"  Value level: {vd.value_level.value}")
        print(f"  Final priority: {vd.final_priority:.2f}")
        print(f"  Reasoning: {vd.reasoning}")
        print(f"  Harm detected: {vd.harm_detected}")
    
    print(f"\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"  • {rec}")
    
    # Assertions
    assert result["intent_signal"].mode.value == "protection", "Should detect protection intent"
    assert "value_decision" in result, "Should include value decision"
    assert result["value_decision"].value_level == ValueLevel.CRITICAL, "Should be CRITICAL value"
    assert result["value_decision"].final_priority == 1.0, "Should be max priority"
    assert result["balance_metric"].state.value == "top_down_dominant", "Protection should be top-down"
    
    print("\n✅ Test 4 PASSED: Full pipeline correctly integrates intent + value + balance")


def test_low_value_learning():
    """Test 5: Low value + learning intent (should allow normal priority)"""
    print("\n" + "=" * 60)
    print("TEST 5: Low Value + Learning Intent")
    print("=" * 60)
    
    value_layer = ValueLayer()
    
    # Scenario: Learning about trivial data
    decision = value_layer.make_decision(
        intent_signal={"mode": "learning"},
        key="temp.note",
        domain="temporary",
        content="Just a test note"
    )
    
    print(f"Intent mode: {decision.intent_mode}")
    print(f"Value level: {decision.value_level.value}")
    print(f"Final priority: {decision.final_priority:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Assertions
    assert decision.intent_mode == "learning", "Should be learning mode"
    assert decision.value_level == ValueLevel.LOW, "Should be LOW value"
    assert decision.final_priority <= 0.3, "Low value should have low priority"
    
    print("\n✅ Test 5 PASSED: Low value + learning correctly deprioritized")


def test_harm_override():
    """Test 6: Harm detection overrides intent"""
    print("\n" + "=" * 60)
    print("TEST 6: Harm Detection Override")
    print("=" * 60)
    
    supervisor = MetaSupervisor(enable_value_layer=True)
    
    # Scenario: Learning intent but critical harm detected
    result = supervisor.process_turn(
        user_input="Store this: user.name = Morpheus",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2},
        value_context={
            "key": "user.name",
            "domain": "identity",
            "content": "Morpheus",
            "harm_context": {
                "key": "user.name",
                "proposed_value": "Morpheus",
                "canonical_value": "Morten",
                "trust_score": 0.5
            }
        }
    )
    
    vd = result.get("value_decision")
    
    print(f"Intent: {result['intent_signal'].mode.value}")
    print(f"Value level: {vd.value_level.value if vd else 'N/A'}")
    print(f"Harm detected: {vd.harm_detected if vd else 'N/A'}")
    print(f"Final priority: {vd.final_priority if vd else 'N/A':.2f}")
    
    print(f"\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"  • {rec}")
    
    # Assertions
    assert vd is not None, "Should have value decision"
    assert vd.harm_detected, "Should detect harm"
    assert vd.final_priority >= 0.8, "Harm should increase priority"
    assert any("HARM" in rec for rec in result["recommendations"]), "Should recommend harm action"
    
    print("\n✅ Test 6 PASSED: Harm detection correctly overrides intent")


if __name__ == "__main__":
    print("\n🧪 PHASE 5: VALUE LAYER INTEGRATION TEST")
    print("=" * 60)
    print("Testing Value Layer + Meta-Supervisor integration")
    print("=" * 60)
    
    try:
        test_critical_value_detection()
        test_harm_detection()
        test_value_based_decision()
        test_full_pipeline()
        test_low_value_learning()
        test_harm_override()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Phase 5 Complete")
        print("=" * 60)
        print("\nValue Layer now provides:")
        print("  ✓ Importance classification (CRITICAL/HIGH/MEDIUM/LOW)")
        print("  ✓ Harm detection (corruption, degradation, instability)")
        print("  ✓ Value-based decisions (intent + value → priority)")
        print("  ✓ Full integration with Meta-Supervisor")
        print("\nCognitive stack complete:")
        print("  Intent (what user wants) + Value (what is important)")
        print("  = AGI-like decision making")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
