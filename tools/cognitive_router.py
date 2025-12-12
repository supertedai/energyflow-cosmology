#!/usr/bin/env python3
"""
cognitive_router.py - Phase 4.3: Router Integration
===================================================

Emit cognitive signals to production systems.

This module integrates the full cognitive stack into the routing layer,
making intent, value, and motivational signals available for:
- Memory retrieval weighting
- LLM prompt enhancement  
- Self-optimizing parameter tuning
- Production decision making

SIGNALS EXPORTED:
- Intent signal (what user wants)
- Value decision (what is important)
- Motivational signal (what system wants)
- Balance metric (top-down/bottom-up)
- Stability report (drift/oscillation)

INTEGRATION POINTS:
- chat_intention_bridge.py (override decisions)
- unified_api (routing decisions)
- self_optimizing_layer.py (parameter tuning)
- self_healing_memory.py (conflict resolution)
"""

from typing import Dict, List, Any, Optional
import json
import sys
from pathlib import Path

# Add parent directory to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.meta_supervisor import MetaSupervisor


class CognitiveRouter:
    """
    COGNITIVE ROUTER
    
    Routes cognitive signals from Meta-Supervisor to production systems.
    
    USAGE:
        router = CognitiveRouter()
        
        # Process turn and get all signals
        signals = router.process_and_route(
            user_input="Hva heter jeg?",
            session_context={},
            system_metrics={"accuracy": 0.85},
            value_context={"key": "user.name", "domain": "identity"}
        )
        
        # Use signals in production
        intent_mode = signals["intent"]["mode"]
        value_priority = signals["value"]["final_priority"]
        motivation_strength = signals["motivation"]["motivation_strength"]
    """
    
    def __init__(self):
        self.supervisor = MetaSupervisor(
            enable_value_layer=True,
            enable_motivational_dynamics=True
        )
    
    def process_and_route(
        self,
        user_input: str,
        session_context: Dict[str, Any],
        system_metrics: Dict[str, float],
        value_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process turn through full cognitive stack and route signals.
        
        Args:
            user_input: User's message
            session_context: Session info
            system_metrics: System metrics
            value_context: Value layer context
        
        Returns:
            {
                "intent": {...},
                "balance": {...},
                "stability": {...},
                "value": {...},
                "motivation": {...},
                "routing_decision": {...}
            }
        """
        # Process through meta-supervisor
        result = self.supervisor.process_turn(
            user_input,
            session_context,
            system_metrics,
            value_context
        )
        
        # Extract signals
        intent_signal = result["intent_signal"].to_dict()
        balance_metric = result["balance_metric"].to_dict()
        stability_report = result["stability_report"].to_dict()
        
        value_decision = None
        if "value_decision" in result:
            value_decision = result["value_decision"].to_dict()
        
        motivational_signal = None
        if "motivational_signal" in result:
            motivational_signal = result["motivational_signal"].to_dict()
        
        # Make routing decision
        routing_decision = self._make_routing_decision(
            intent_signal,
            value_decision,
            motivational_signal,
            stability_report
        )
        
        return {
            "intent": intent_signal,
            "balance": balance_metric,
            "stability": stability_report,
            "value": value_decision,
            "motivation": motivational_signal,
            "routing_decision": routing_decision,
            "recommendations": result["recommendations"]
        }
    
    def _make_routing_decision(
        self,
        intent: Dict,
        value: Optional[Dict],
        motivation: Optional[Dict],
        stability: Dict
    ) -> Dict[str, Any]:
        """
        Make routing decision based on cognitive signals.
        
        Returns routing instructions for production systems.
        """
        decision = {
            "memory_retrieval_weight": 1.0,
            "canonical_override_strength": 0.5,
            "llm_temperature": 0.7,
            "self_optimization_trigger": False,
            "self_healing_trigger": False,
            "reasoning": []
        }
        
        # Intent-based routing
        if intent["mode"] == "protection":
            decision["canonical_override_strength"] = 1.0
            decision["llm_temperature"] = 0.3
            decision["reasoning"].append("PROTECTION mode: Max canonical, low temperature")
        
        elif intent["mode"] == "learning":
            decision["memory_retrieval_weight"] = 0.7
            decision["llm_temperature"] = 0.8
            decision["reasoning"].append("LEARNING mode: Allow exploration")
        
        # Value-based routing med driftsprofiler
        if value:
            value_level = value["value_level"]
            
            # CRITICAL: Max protection
            if value_level == "critical":
                decision["canonical_override_strength"] = 1.0
                decision["memory_retrieval_weight"] = 1.0
                decision["llm_temperature"] = 0.25
                decision["reasoning"].append("CRITICAL value: Max canonical, temp=0.25")
            
            # HIGH (EFC, canonical): Sterk beskyttelse
            elif value_level == "high":
                decision["canonical_override_strength"] = 0.8
                decision["memory_retrieval_weight"] = 1.0
                decision["llm_temperature"] = 0.5
                decision["reasoning"].append("HIGH value (EFC): Strong canonical=0.8, temp=0.5")
            
            # MEDIUM: Balansert
            elif value_level == "medium":
                decision["canonical_override_strength"] = 0.6
                decision["memory_retrieval_weight"] = 0.8
                decision["llm_temperature"] = 0.65
                decision["reasoning"].append("MEDIUM value: Balanced canonical=0.6")
            
            # LOW: Mer frihet
            else:  # low
                decision["canonical_override_strength"] = 0.4
                decision["memory_retrieval_weight"] = 0.7
                decision["llm_temperature"] = 0.8
                decision["reasoning"].append("LOW value: Exploration mode, temp=0.8")
            
            if value["harm_detected"]:
                decision["canonical_override_strength"] = 1.0
                decision["llm_temperature"] = 0.2
                decision["self_healing_trigger"] = True
                decision["reasoning"].append("HARM detected: Full lockdown + healing")
        
        # Motivation-based routing
        if motivation:
            if motivation["motivation_strength"] > 0.8:
                decision["memory_retrieval_weight"] *= 1.2
                decision["reasoning"].append("High motivation: Boost retrieval")
            
            # Check for active PROTECT_IDENTITY goal
            active_goals = [g["goal_type"] for g in motivation["active_goals"]]
            if "protect_identity" in active_goals:
                decision["canonical_override_strength"] = 1.0
                decision["reasoning"].append("PROTECT_IDENTITY goal: Max override")
        
        # Stability-based routing
        if stability["level"] in ["degrading", "critical"]:
            decision["self_optimization_trigger"] = True
            decision["self_healing_trigger"] = True
            decision["reasoning"].append("Stability issues: Trigger optimization + healing")
        
        if stability["oscillation_rate"] > 3.0:
            decision["canonical_override_strength"] = 0.9
            decision["llm_temperature"] = 0.4
            decision["reasoning"].append("High oscillation: Stabilize with canonical + low temp")
        
        return decision
    
    def get_stats(self) -> Dict:
        """Get router statistics"""
        return self.supervisor.get_stats()


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Cognitive Router")
    print("=" * 60)
    
    router = CognitiveRouter()
    
    # Test 1: Protection mode routing
    print("\n1️⃣ Test: Protection mode routing")
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
    
    print(f"Intent mode: {signals['intent']['mode']}")
    print(f"Value level: {signals['value']['value_level'] if signals['value'] else 'N/A'}")
    print(f"Motivation strength: {signals['motivation']['motivation_strength'] if signals['motivation'] else 'N/A'}")
    print(f"\nRouting decision:")
    print(f"  Canonical override: {signals['routing_decision']['canonical_override_strength']}")
    print(f"  LLM temperature: {signals['routing_decision']['llm_temperature']}")
    print(f"  Self-healing trigger: {signals['routing_decision']['self_healing_trigger']}")
    print(f"  Reasoning: {signals['routing_decision']['reasoning']}")
    
    # Test 2: Learning mode routing
    print("\n2️⃣ Test: Learning mode routing")
    signals = router.process_and_route(
        user_input="Forklar energiflyt",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"Intent mode: {signals['intent']['mode']}")
    print(f"\nRouting decision:")
    print(f"  Memory retrieval weight: {signals['routing_decision']['memory_retrieval_weight']}")
    print(f"  LLM temperature: {signals['routing_decision']['llm_temperature']}")
    print(f"  Reasoning: {signals['routing_decision']['reasoning']}")
    
    # Test 3: Stats
    print("\n3️⃣ Router stats")
    stats = router.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Cognitive Router test complete")
