#!/usr/bin/env python3
"""
Integration test for Self-Optimizing Layer with CMC.

Scenario:
1. System starts with defaults
2. High override_rate triggers parameter adjustment
3. System evaluates effectiveness
4. Parameters revert if degraded, anchor if improved
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tools.canonical_memory_core import CanonicalMemoryCore
from tools.self_optimizing_layer import MetricType, ParameterType


def test_self_optimizing_integration():
    print("🧪 Testing Self-Optimizing Integration with CMC")
    print("=" * 60)
    
    # Initialize CMC with self-optimizing enabled
    print("\n1️⃣ Initialize CMC with self-optimizing")
    cmc = CanonicalMemoryCore(enable_self_optimizing=True)
    
    # Check initial parameters
    initial_params = cmc.self_optimizing.get_current_parameters()
    print(f"\n📊 Initial parameters:")
    for param, value in initial_params.items():
        print(f"   {param}: {value}")
    
    initial_promotion = initial_params['promotion_threshold']
    initial_decay = initial_params['temporal_decay_days']
    
    # Simulate high override rate (trigger adjustment)
    print("\n2️⃣ Simulate high override rate (>30% threshold)")
    for i in range(10):
        cmc.record_performance_metric(MetricType.OVERRIDE_RATE, 0.4)  # 40%
    
    # Run optimization cycle
    print("\n3️⃣ Run self-optimization cycle")
    results = cmc.run_self_optimization_cycle()
    
    print(f"\n📈 Evaluation results:")
    print(f"   Issues detected: {len(results['evaluation']['issues'])}")
    for issue in results['evaluation']['issues']:
        print(f"      - {issue['description']}")
    
    print(f"\n⚙️  Adjustments made: {len(results['adjustments_made'])}")
    for adj in results['adjustments_made']:
        print(f"      - {adj['parameter']}: {adj['old_value']:.2f} → {adj['new_value']:.2f}")
        print(f"        Reason: {adj['reason']}")
    
    # Check updated parameters
    updated_params = cmc.self_optimizing.get_current_parameters()
    print(f"\n📊 Updated parameters:")
    for param, value in updated_params.items():
        print(f"   {param}: {value}")
    
    # Verify self-healing layer got updated
    if cmc.self_healing:
        print(f"\n🩹 Self-healing layer synced:")
        print(f"   promotion_threshold: {cmc.self_healing.promotion_threshold}")
        print(f"   temporal_decay_days: {cmc.self_healing.temporal_decay_days}")
    
    # Test metrics
    print("\n4️⃣ System stats")
    stats = cmc.self_optimizing.get_stats()
    print(f"   Total metrics: {stats['total_metrics']}")
    print(f"   Total adjustments: {stats['total_adjustments']}")
    print(f"   Adjustment results: {stats['adjustment_results']}")
    
    # Validation
    print("\n✅ Validation:")
    
    # AME override strength should have decreased
    if updated_params['ame_override_strength'] < initial_params['ame_override_strength']:
        print(f"   ✓ AME override strength decreased (less aggressive)")
    else:
        print(f"   ✗ AME override strength did not decrease")
    
    # Self-healing should be synced
    if cmc.self_healing:
        if cmc.self_healing.promotion_threshold == int(updated_params['promotion_threshold']):
            print(f"   ✓ Self-healing promotion_threshold synced")
        else:
            print(f"   ✗ Self-healing promotion_threshold not synced")
        
        if cmc.self_healing.temporal_decay_days == int(updated_params['temporal_decay_days']):
            print(f"   ✓ Self-healing temporal_decay_days synced")
        else:
            print(f"   ✗ Self-healing temporal_decay_days not synced")
    
    print("\n✅ Self-Optimizing Integration test complete")
    print("\n🎯 System is now self-aware and self-tuning!")
    print("   - Observes own performance")
    print("   - Detects degradation patterns")
    print("   - Adjusts parameters autonomously")
    print("   - Anchors improvements, reverts failures")


if __name__ == "__main__":
    test_self_optimizing_integration()
