#!/usr/bin/env python3
"""
Simple debug test for adaptive learning.
"""

import sys
from pathlib import Path

# Add tools to path
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from efc_theory_engine import EFCTheoryEngine, LEARNER_AVAILABLE, EFCPatternLearner
import os

print(f"LEARNER_AVAILABLE: {LEARNER_AVAILABLE}")
print(f"EFCPatternLearner: {EFCPatternLearner}")
print()

# Clean slate
learning_file = "test_debug_learning.json"
if os.path.exists(learning_file):
    os.remove(learning_file)

# Create engine
engine = EFCTheoryEngine(
    enable_learning=True,
    learning_file=learning_file
)

print("🔍 DEBUGGING ADAPTIVE LEARNING")
print("=" * 80)
print()

# Test 1: Detect pattern
q1 = "Hvorfor stabiliserer markedet seg ved likevekt?"
result1 = engine.detect_efc_pattern(q1, domain="economics")

print(f"Q: {q1}")
print(f"Score: {result1.score}")
print(f"Level: {result1.relevance_level}")
print(f"Patterns detected: {result1.detected_patterns}")
print()

# Test 2: Provide feedback
print("Providing feedback...")
engine.provide_feedback(
    question=q1,
    domain="economics",
    efc_score=result1.score,
    detected_patterns=result1.detected_patterns,
    was_helpful=True
)
print("✓ Feedback provided")
print()

# Check learner state
if engine.learner:
    print(f"Learner observations: {len(engine.learner.observations)}")
    print(f"Learner domains: {list(engine.learner.domains.keys())}")
    print(f"Learner patterns: {len(engine.learner.patterns)}")
    
    if "economics" in engine.learner.domains:
        econ = engine.learner.domains["economics"]
        print(f"\nEconomics domain:")
        print(f"  Observations: {econ.observations}")
        print(f"  Successful: {econ.successful_efc_uses}")
        print(f"  Threshold: {econ.threshold_adjustment}")
    
    # Try to save
    print("\nSaving learning...")
    engine.learner.save_learning()
    print(f"✓ Saved to: {learning_file}")
    
    if os.path.exists(learning_file):
        import json
        with open(learning_file) as f:
            data = json.load(f)
        print(f"File contains {len(data.get('domains', {}))} domains")
        print(f"File contains {len(data.get('patterns', {}))} patterns")
else:
    print("❌ No learner!")

print()
print("=" * 80)
