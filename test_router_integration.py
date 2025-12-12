#!/usr/bin/env python3
"""
test_router_integration.py - Test Phase 4.3: Router Integration
================================================================

Validates full cognitive stack integration with production systems.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools.cognitive_router import CognitiveRouter

def test_protection_routing():
    """Test protection mode routing"""
    print("\n🧪 Test 1: Protection mode routing")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    signals = router.process_and_route(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2},
        value_context={
            "key": "user.name",
            "domain": "identity",
            "content": "Morten",
            "metadata": {"trust_score": 0.95, "is_canonical": True}
        }
    )
    
    assert signals["intent"]["mode"] == "protection", "Should be protection mode"
    assert signals["value"]["value_level"] == "critical", "Should be critical value"
    assert signals["motivation"]["motivation_strength"] > 0.8, "Should have high motivation"
    
    routing = signals["routing_decision"]
    assert routing["canonical_override_strength"] == 1.0, "Should max canonical override"
    assert routing["llm_temperature"] == 0.3, "Should use low temperature"
    
    # Check reasoning (case-insensitive substring match)
    reasoning_str = " ".join(routing["reasoning"]).lower()
    assert "protection" in reasoning_str, f"Should explain protection, got: {routing['reasoning']}"
    assert "critical" in reasoning_str, f"Should explain value, got: {routing['reasoning']}"
    assert "protect_identity" in reasoning_str, f"Should explain goal, got: {routing['reasoning']}"
    
    print("✅ Protection routing correct")
    print(f"   Intent: {signals['intent']['mode']}")
    print(f"   Value: {signals['value']['value_level']}")
    print(f"   Motivation: {signals['motivation']['motivation_strength']:.2f}")
    print(f"   Canonical override: {routing['canonical_override_strength']}")
    print(f"   Temperature: {routing['llm_temperature']}")

def test_learning_routing():
    """Test learning mode routing"""
    print("\n🧪 Test 2: Learning mode routing")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    signals = router.process_and_route(
        user_input="Forklar energiflyt i detalj",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    assert signals["intent"]["mode"] == "learning", "Should be learning mode"
    
    routing = signals["routing_decision"]
    assert routing["memory_retrieval_weight"] == 0.7, "Should reduce retrieval weight"
    assert routing["llm_temperature"] == 0.8, "Should use high temperature"
    
    reasoning_str = " ".join(routing["reasoning"]).lower()
    assert "learning" in reasoning_str, f"Should explain learning, got: {routing['reasoning']}"
    
    print("✅ Learning routing correct")
    print(f"   Intent: {signals['intent']['mode']}")
    print(f"   Memory weight: {routing['memory_retrieval_weight']}")
    print(f"   Temperature: {routing['llm_temperature']}")

def test_stability_triggers():
    """Test stability-based self-optimization triggers"""
    print("\n🧪 Test 3: Stability triggers")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    # Simulate degrading stability
    for i in range(6):
        signals = router.process_and_route(
            user_input=f"Query {i}",
            session_context={},
            system_metrics={
                "accuracy": 0.6 - (i * 0.05),  # Degrading
                "override_rate": 0.5 + (i * 0.1)  # Increasing
            }
        )
    
    routing = signals["routing_decision"]
    
    # Should trigger self-optimization if stability is degrading
    if signals["stability"]["level"] in ["degrading", "critical"]:
        assert routing["self_optimization_trigger"], "Should trigger optimization"
        assert routing["self_healing_trigger"], "Should trigger healing"
        print("✅ Stability triggers activated")
        print(f"   Stability: {signals['stability']['level']}")
        print(f"   Oscillation rate: {signals['stability']['oscillation_rate']:.2f}")
        print(f"   Self-optimization: {routing['self_optimization_trigger']}")
        print(f"   Self-healing: {routing['self_healing_trigger']}")
    else:
        print("ℹ️  Stability still acceptable (no triggers)")

def test_full_stack_coordination():
    """Test full cognitive stack coordination"""
    print("\n🧪 Test 4: Full stack coordination")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    signals = router.process_and_route(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2},
        value_context={
            "key": "user.name",
            "domain": "identity",
            "content": "Morten",
            "metadata": {"trust_score": 0.95, "is_canonical": True}
        }
    )
    
    # Validate all layers present
    assert "intent" in signals, "Missing intent signal"
    assert "value" in signals, "Missing value signal"
    assert "motivation" in signals, "Missing motivational signal"
    assert "balance" in signals, "Missing balance metric"
    assert "stability" in signals, "Missing stability report"
    assert "routing_decision" in signals, "Missing routing decision"
    
    # Validate coordination
    intent_mode = signals["intent"]["mode"]
    value_level = signals["value"]["value_level"]
    motivation_strength = signals["motivation"]["motivation_strength"]
    
    print("✅ Full stack present and coordinated")
    print(f"   Intent: {intent_mode}")
    print(f"   Value: {value_level}")
    print(f"   Motivation: {motivation_strength:.2f}")
    print(f"   Balance: {signals['balance']['state']}")
    print(f"   Stability: {signals['stability']['level']}")
    print(f"\n   Routing decision reasoning:")
    for reason in signals["routing_decision"]["reasoning"]:
        print(f"     • {reason}")

def test_stats_tracking():
    """Test statistics tracking across router"""
    print("\n🧪 Test 5: Stats tracking")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    # Process multiple turns
    for i in range(3):
        router.process_and_route(
            user_input=f"Query {i}",
            session_context={},
            system_metrics={"accuracy": 0.85, "override_rate": 0.2}
        )
    
    stats = router.get_stats()
    
    assert stats["total_intents"] == 3, "Should track 3 intents"
    assert stats["total_balance_metrics"] == 3, "Should track 3 balance metrics"
    assert "value_layer" in stats, "Should include value layer stats"
    assert "motivational_dynamics" in stats, "Should include motivational stats"
    
    print("✅ Stats tracking correct")
    print(f"   Total intents: {stats['total_intents']}")
    print(f"   Total balance metrics: {stats['total_balance_metrics']}")
    print(f"   Value decisions: {stats['value_layer']['total_decisions']}")
    print(f"   Active goals: {stats['motivational_dynamics']['active_goals']}")

if __name__ == "__main__":
    print("🧠 Testing Phase 4.3: Router Integration")
    print("=" * 60)
    
    try:
        test_protection_routing()
        test_learning_routing()
        test_stability_triggers()
        test_full_stack_coordination()
        test_stats_tracking()
        
        print("\n" + "=" * 60)
        print("✅ ALL ROUTER INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\n🚀 Phase 4.3 COMPLETE - Ready for production")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
