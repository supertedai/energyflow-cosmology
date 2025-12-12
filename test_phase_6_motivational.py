#!/usr/bin/env python3
"""
test_phase_6_motivational.py - Integration test for Phase 6
===========================================================

Tests Motivational Dynamics integration with full cognitive stack:
1. Goal activation (protect_identity when identity threatened)
2. Persistence enforcement (PERMANENT keys cannot change)
3. Preference bias (strong canonical preference)
4. Self-regulation (balance between protection/exploration)
5. Full stack integration (intent + value + motivation)
"""

from tools.meta_supervisor import MetaSupervisor
from tools.motivational_dynamics import MotivationalDynamics, GoalType, PersistenceLevel


def test_goal_activation():
    """Test 1: Goal activation when identity threatened"""
    print("\n" + "=" * 60)
    print("TEST 1: Goal Activation (Identity Threat)")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Scenario: Identity corruption detected
    signal = dynamics.generate_signal(context={
        "intent_mode": "protection",
        "value_level": "critical",
        "harm_signals": [{"harm_type": "identity_corruption", "severity": 1.0}]
    })
    
    print(f"Context: identity_corruption harm detected")
    print(f"Active goals: {len(signal.active_goals)}")
    print(f"Top 3 goals:")
    for goal in signal.active_goals[:3]:
        print(f"  • {goal.goal_type.value} (priority: {goal.priority})")
    
    print(f"\nMotivation strength: {signal.motivation_strength:.2f}")
    print(f"Directional bias:")
    for domain, bias in list(signal.directional_bias.items())[:3]:
        print(f"  {domain}: {bias:.2f}")
    
    # Assertions
    assert len(signal.active_goals) >= 2, "Should have multiple active goals"
    assert signal.active_goals[0].goal_type == GoalType.PROTECT_IDENTITY, "Top goal should be PROTECT_IDENTITY"
    assert signal.motivation_strength > 0.8, "Motivation should be high for identity threat"
    assert signal.directional_bias["identity"] > 0.7, "Identity bias should be strong"
    
    print("\n✅ Test 1 PASSED: Goals correctly activated for identity threat")


def test_persistence_enforcement():
    """Test 2: Persistence enforcement for PERMANENT keys"""
    print("\n" + "=" * 60)
    print("TEST 2: Persistence Enforcement (PERMANENT Keys)")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Test PERMANENT key (user.name)
    allowed_permanent, reason_permanent = dynamics.can_change_key("user.name", "NewName")
    print(f"Can change 'user.name'? {allowed_permanent}")
    print(f"Reason: {reason_permanent}")
    
    # Test STABLE key (canonical fact - should be allowed after time)
    allowed_stable, reason_stable = dynamics.can_change_key("canonical.fact", "NewValue")
    print(f"\nCan change 'canonical.fact'? {allowed_stable}")
    print(f"Reason: {reason_stable}")
    
    # Test FLEXIBLE/EPHEMERAL (no restriction)
    allowed_flex, reason_flex = dynamics.can_change_key("temp.data", "NewValue")
    print(f"\nCan change 'temp.data'? {allowed_flex}")
    print(f"Reason: {reason_flex}")
    
    # Assertions
    assert allowed_permanent == False, "PERMANENT keys should not change"
    assert "PERMANENT" in reason_permanent, "Reason should mention PERMANENT"
    assert allowed_flex == True, "Unrestricted keys should be allowed"
    
    print("\n✅ Test 2 PASSED: Persistence correctly enforced")


def test_preference_bias():
    """Test 3: Preference bias for different domains"""
    print("\n" + "=" * 60)
    print("TEST 3: Preference Bias (Domain-specific)")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Test biases for different domains
    domains = ["identity", "canonical_memory", "system_stability", "learning"]
    biases = {}
    
    for domain in domains:
        bias = dynamics.get_preference_bias(domain)
        biases[domain] = bias
        print(f"{domain:20s}: {bias:.2f} {'(STRONG)' if bias > 0.75 else '(MODERATE)' if bias > 0.6 else ''}")
    
    # Assertions
    assert biases["identity"] > 0.75, "Identity bias should be STRONG"
    assert biases["canonical_memory"] > 0.75, "Canonical bias should be STRONG"
    assert biases["system_stability"] > 0.6, "System stability bias should be at least MODERATE"
    
    print("\n✅ Test 3 PASSED: Preference biases correctly applied")


def test_self_regulation():
    """Test 4: Self-regulation balances extremes"""
    print("\n" + "=" * 60)
    print("TEST 4: Self-Regulation (Balance Extremes)")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Simulate multiple turns in protection mode
    for i in range(10):
        dynamics.meta_stability_loop.history.append({
            "timestamp": datetime.now(),
            "state": {"intent_mode": "protection"}
        })
    
    # Self-regulate
    adjustments = dynamics.self_regulate(context={"intent_mode": "protection"})
    
    print(f"After 10 turns in PROTECTION mode:")
    print(f"Regulation adjustments: {adjustments}")
    
    # Assertions
    assert len(adjustments) > 0, "Should have regulation adjustments"
    # Should suggest allowing some exploration when too much protection
    assert any("allow" in key or "reduce" in key for key in adjustments.keys()), "Should suggest balancing"
    
    print("\n✅ Test 4 PASSED: Self-regulation working")


def test_full_stack_integration():
    """Test 5: Full stack integration (intent + value + motivation)"""
    print("\n" + "=" * 60)
    print("TEST 5: Full Stack Integration")
    print("=" * 60)
    
    supervisor = MetaSupervisor(enable_value_layer=True, enable_motivational_dynamics=True)
    
    # Scenario: "Hva heter jeg?" with full stack
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
    
    print(f"User input: 'Hva heter jeg?'\n")
    print(f"Intent: {result['intent_signal'].mode.value}")
    print(f"Balance: {result['balance_metric'].state.value}")
    print(f"  Top-down: {result['balance_metric'].top_down_weight:.2f}")
    print(f"Stability: {result['stability_report'].level.value}")
    
    if "value_decision" in result:
        vd = result["value_decision"]
        print(f"\nValue decision:")
        print(f"  Level: {vd.value_level.value}")
        print(f"  Priority: {vd.final_priority:.2f}")
    
    if "motivational_signal" in result:
        ms = result["motivational_signal"]
        print(f"\nMotivational signal:")
        print(f"  Active goals: {len(ms.active_goals)}")
        print(f"  Top goal: {ms.active_goals[0].goal_type.value if ms.active_goals else 'none'}")
        print(f"  Motivation strength: {ms.motivation_strength:.2f}")
        print(f"  Identity bias: {ms.directional_bias.get('identity', 0):.2f}")
    
    print(f"\nRecommendations:")
    for rec in result["recommendations"][:5]:
        print(f"  • {rec}")
    
    # Assertions
    assert result["intent_signal"].mode.value == "protection", "Should detect protection intent"
    assert "value_decision" in result, "Should have value decision"
    assert "motivational_signal" in result, "Should have motivational signal"
    assert result["value_decision"].value_level.value == "critical", "Should be CRITICAL value"
    assert len(result["motivational_signal"].active_goals) > 0, "Should have active goals"
    assert result["motivational_signal"].active_goals[0].goal_type == GoalType.PROTECT_IDENTITY, "Top goal should be PROTECT_IDENTITY"
    
    print("\n✅ Test 5 PASSED: Full stack integration working")


def test_learning_vs_protection():
    """Test 6: Different behavior for learning vs protection"""
    print("\n" + "=" * 60)
    print("TEST 6: Learning vs Protection Modes")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Protection mode
    signal_protection = dynamics.generate_signal(context={
        "intent_mode": "protection",
        "value_level": "critical"
    })
    
    # Learning mode
    signal_learning = dynamics.generate_signal(context={
        "intent_mode": "learning",
        "value_level": "medium"
    })
    
    print("PROTECTION mode:")
    print(f"  Active goals: {[g.goal_type.value for g in signal_protection.active_goals[:2]]}")
    print(f"  Motivation: {signal_protection.motivation_strength:.2f}")
    print(f"  Identity bias: {signal_protection.directional_bias['identity']:.2f}")
    
    print("\nLEARNING mode:")
    print(f"  Active goals: {[g.goal_type.value for g in signal_learning.active_goals[:2]]}")
    print(f"  Motivation: {signal_learning.motivation_strength:.2f}")
    print(f"  Learning bias: {signal_learning.directional_bias['learning']:.2f}")
    
    # Assertions
    assert GoalType.PROTECT_IDENTITY in [g.goal_type for g in signal_protection.active_goals], "Protection should activate PROTECT_IDENTITY"
    assert GoalType.OPTIMIZE_LEARNING in [g.goal_type for g in signal_learning.active_goals], "Learning should activate OPTIMIZE_LEARNING"
    
    print("\n✅ Test 6 PASSED: Different behaviors for different modes")


if __name__ == "__main__":
    print("\n🧪 PHASE 6: MOTIVATIONAL DYNAMICS INTEGRATION TEST")
    print("=" * 60)
    print("Testing Motivational Dynamics + Full Cognitive Stack")
    print("=" * 60)
    
    from datetime import datetime
    
    try:
        test_goal_activation()
        test_persistence_enforcement()
        test_preference_bias()
        test_self_regulation()
        test_full_stack_integration()
        test_learning_vs_protection()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Phase 6 Complete")
        print("=" * 60)
        print("\nMotivational Dynamics now provides:")
        print("  ✓ Internal goals (protect, maintain, optimize, ensure, minimize)")
        print("  ✓ Directional preferences (canonical, high-trust, stability)")
        print("  ✓ Temporal persistence (PERMANENT, STABLE, FLEXIBLE, EPHEMERAL)")
        print("  ✓ Self-regulation (balance protection/exploration)")
        print("\nFull cognitive architecture:")
        print("  Intent (what user wants)")
        print("  + Value (what is important)")
        print("  + Motivation (what system wants)")
        print("  = AGI-LIKE AGENCY")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
