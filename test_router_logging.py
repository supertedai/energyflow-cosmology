#!/usr/bin/env python3
"""Test router decision logging."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.symbiosis_router_v4 import handle_chat_turn

print("🧪 Testing Router Decision Logging")
print("=" * 60)

# Test 1: Simple query
print("\n1️⃣ Test query: 'Hva heter du?'")
result = handle_chat_turn(
    user_message="Hva heter du?",
    assistant_draft="Jeg heter Claude",
    session_id="test_logging_session"
)

print(f"   Final answer: {result['final_answer'][:50]}...")
print(f"   Override: {result['was_overridden']}")

# Check if routing log exists
if "_routing_log" in result:
    log = result["_routing_log"]
    print(f"\n   📋 Routing Log:")
    print(f"   - Activated layers: {log['activated_layers']}")
    print(f"   - Layer timings: {', '.join([f'{k}:{v:.1f}ms' for k, v in log['layer_timings'].items()])}")
    print(f"   - Contradiction: {log['contradiction_detected']}")
    print(f"   - Override: {log['override_triggered']}")
    print(f"   - Total time: {log['total_time_ms']:.1f}ms")

# Test 2: Check JSONL file
log_file = "logs/router_decisions.jsonl"
if os.path.exists(log_file):
    print(f"\n2️⃣ Reading log file: {log_file}")
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    print(f"   Total log entries: {len(lines)}")
    
    if lines:
        print(f"\n   Last entry:")
        last_entry = json.loads(lines[-1])
        print(f"   - Timestamp: {last_entry['timestamp']}")
        print(f"   - Session: {last_entry['session_id']}")
        print(f"   - Turn: {last_entry['turn_number']}")
        print(f"   - Activated layers: {last_entry['activated_layers']}")
        print(f"   - Total time: {last_entry['total_time_ms']:.1f}ms")
else:
    print(f"\n⚠️  Log file not found: {log_file}")

print("\n" + "=" * 60)
print("✅ Router logging test complete!")
