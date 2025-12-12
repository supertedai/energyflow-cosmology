#!/usr/bin/env python3
"""Quick test of cognitive router + chat handler"""

import sys
import os

sys.path.insert(0, 'tools')

from cognitive_router import CognitiveRouter

print("Testing cognitive router...")

router = CognitiveRouter()

signals = router.process_and_route(
    user_input="Hva heter jeg?",
    session_context={},
    system_metrics={"accuracy": 0.85},
    value_context={"key": "chat.turn", "domain": "conversation"}
)

print(f"\n✅ Signals generated:")
print(f"   Intent: {signals['intent']['mode']}")
print(f"   Value: {signals.get('value', {}).get('value_level')}")
print(f"   Routing: {signals['routing_decision']['canonical_override_strength']}")

print("\n✅ Cognitive router works fine")
print("\nTesting symbiosis_router_v4...")

from symbiosis_router_v4 import handle_chat_turn

print("Calling handle_chat_turn (this may take time)...")

result = handle_chat_turn(
    user_message="Test",
    assistant_draft="Svar",
    session_id="test_quick"
)

print(f"\n✅ handle_chat_turn completed:")
print(f"   Final answer: {result['final_answer'][:50]}")
print(f"   Was overridden: {result['was_overridden']}")
