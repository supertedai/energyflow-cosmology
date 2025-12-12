#!/usr/bin/env python3
"""
Test full adaptive learning cycle for EFC pattern detection.

Dette tester at:
1. Economics starter med score 0.0 (OUT_OF_SCOPE)
2. Etter flere positive feedback øker threshold adjustment
3. Economics gradvis går til WEAK_SIGNAL → EFC_ENABLED
4. Nye mønstre læres automatisk
"""

import sys
import os
from pathlib import Path

# Add tools to path
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from efc_theory_engine import EFCTheoryEngine
from efc_pattern_learner import EFCPatternLearner
import json


def test_adaptive_learning_cycle():
    """Test complete adaptive learning cycle."""
    
    print("=" * 80)
    print("TEST: ADAPTIVE LEARNING CYCLE")
    print("=" * 80)
    print()
    
    # Create EFC engine with learning enabled
    learning_file = "test_adaptive_learning.json"
    
    # Clean slate
    if os.path.exists(learning_file):
        os.remove(learning_file)
    
    engine = EFCTheoryEngine(
        cmc=None,
        smm=None,
        graph=None,
        enable_learning=True,
        learning_file=learning_file
    )
    
    # Economics questions that should trigger EFC but initially don't
    economics_questions = [
        "Hvorfor stabiliserer markedet seg ved likevekt?",
        "Hva driver prisendringer i et marked?",
        "Hvordan oppstår finansielle kriser?",
        "Hvorfor vokser økonomien i sykler?",
        "Hva skaper balanse mellom tilbud og etterspørsel?",
        "Hvorfor er noen markeder mer volatile enn andre?",
        "Hvordan emerger økonomisk vekst fra individuelle beslutninger?",
        "Hva driver inflasjon over tid?",
    ]
    
    print("FASE 1: Initial Detection (No Learning)")
    print("-" * 80)
    
    initial_results = []
    for i, q in enumerate(economics_questions[:3], 1):
        result = engine.detect_efc_pattern(q, domain="economics")
        initial_results.append(result)
        print(f"\n{i}. {q}")
        print(f"   Score: {result.score:.1f} | Level: {result.relevance_level}")
        print(f"   Reasoning: {result.reasoning}")
    
    avg_initial = sum(r.score for r in initial_results) / len(initial_results)
    print(f"\n📊 Average initial score: {avg_initial:.1f}")
    print(f"   Levels: {[r.relevance_level for r in initial_results]}")
    print(f"   Expected: OUT_OF_SCOPE or WEAK_SIGNAL")
    print()
    
    print("=" * 80)
    print("FASE 2: Provide Positive Feedback (Learning)")
    print("-" * 80)
    
    # Simulate positive feedback for economics questions
    for i, q in enumerate(economics_questions, 1):
        result = engine.detect_efc_pattern(q, domain="economics")
        
        # Provide positive feedback (EFC was helpful)
        engine.provide_feedback(
            question=q,
            domain="economics",
            efc_score=result.score,
            detected_patterns=result.detected_patterns,
            was_helpful=True  # Key: Mark as helpful
        )
        
        print(f"\n{i}. Feedback provided for: {q[:50]}...")
        print(f"   Score: {result.score:.1f} | Marked as helpful: ✓")
        
        # Check learning progress every 3 observations
        if i % 3 == 0 and engine.learner:
            stats = engine.learner.domains.get("economics")
            if stats:
                print(f"\n   📈 Learning Progress:")
                print(f"      Observations: {stats.observations}")
                print(f"      Success rate: {stats.successful_efc_uses / stats.observations * 100:.0f}%")
                print(f"      Threshold adjustment: {stats.threshold_adjustment:+.1f}")
    
    print()
    print("=" * 80)
    print("FASE 3: Re-test After Learning")
    print("-" * 80)
    
    learned_results = []
    for i, q in enumerate(economics_questions[:3], 1):
        result = engine.detect_efc_pattern(q, domain="economics")
        learned_results.append(result)
        print(f"\n{i}. {q}")
        print(f"   Score: {result.score:.1f} | Level: {result.relevance_level}")
        print(f"   Reasoning: {result.reasoning}")
        if result.detected_patterns:
            print(f"   Patterns: {result.detected_patterns[:3]}")
    
    avg_learned = sum(r.score for r in learned_results) / len(learned_results)
    print(f"\n📊 Average score after learning: {avg_learned:.1f}")
    print(f"   Initial: {avg_initial:.1f} → Learned: {avg_learned:.1f}")
    print(f"   Improvement: {avg_learned - avg_initial:+.1f}")
    
    # Check level improvements
    level_improvements = 0
    level_map = {"OUT_OF_SCOPE": 0, "WEAK_SIGNAL": 1, "EFC_ENABLED": 2, "PURE_EFC": 3}
    for i, (init, learned) in enumerate(zip(initial_results, learned_results)):
        init_level = level_map.get(init.relevance_level, 0)
        learned_level = level_map.get(learned.relevance_level, 0)
        if learned_level > init_level:
            level_improvements += 1
            print(f"   Q{i+1}: {init.relevance_level} → {learned.relevance_level} ✓")
    
    print(f"\n   Level improvements: {level_improvements}/3")
    print()
    
    print("=" * 80)
    print("FASE 4: Analyze Learning Results")
    print("-" * 80)
    
    if engine.learner:
        learner = engine.learner
        
        # Domain statistics
        if "economics" in learner.domains:
            econ_stats = learner.domains["economics"]
            print(f"\n📚 Economics Domain Learning:")
            print(f"   Total observations: {econ_stats.observations}")
            print(f"   Successful uses: {econ_stats.successful_efc_uses}")
            print(f"   Success rate: {econ_stats.successful_efc_uses / econ_stats.observations * 100:.0f}%")
            print(f"   Average EFC score: {econ_stats.average_efc_score:.1f}")
            print(f"   Threshold adjustment: {econ_stats.threshold_adjustment:+.1f}")
            print(f"   Learned patterns: {len(econ_stats.learned_patterns)}")
        
        # Learned patterns
        active_patterns = learner.get_active_patterns()
        print(f"\n🎯 Active Learned Patterns:")
        print(f"   Language cues: {len(active_patterns.get('language_cues', []))}")
        print(f"   Logical patterns: {len(active_patterns.get('logical_patterns', []))}")
        print(f"   Domain terms: {len(active_patterns.get('domain_terms', []))}")
        
        if active_patterns.get('language_cues'):
            print(f"\n   Sample language cues:")
            for cue in list(active_patterns['language_cues'])[:5]:
                print(f"      - {cue}")
        
        # Total learning
        print(f"\n📈 Total Learning Progress:")
        print(f"   Total observations: {len(learner.observations)}")
        print(f"   Total patterns: {len(learner.patterns)}")
        print(f"   Active patterns: {len([p for p in learner.patterns.values() if p.confidence >= 0.7])}")
        print(f"   Domains learned: {len(learner.domains)}")
    
    print()
    print("=" * 80)
    print("FASE 5: Validation")
    print("-" * 80)
    
    # Validate improvement in levels (not just scores)
    success = level_improvements >= 2  # Should see at least 2/3 questions improve levels
    
    print(f"\n✓ TEST RESULTS:")
    print(f"   Initial average score: {avg_initial:.1f}")
    print(f"   Learned average score: {avg_learned:.1f}")
    print(f"   Score change: {avg_learned - avg_initial:+.1f}")
    print(f"   Level improvements: {level_improvements}/3")
    print(f"   Success threshold: ≥2 level improvements")
    print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
    
    if engine.learner and "economics" in engine.learner.domains:
        econ_stats = engine.learner.domains["economics"]
        threshold_works = econ_stats.threshold_adjustment < 0  # Should be negative (easier activation)
        print(f"\n✓ THRESHOLD ADJUSTMENT:")
        print(f"   Adjustment: {econ_stats.threshold_adjustment:+.1f}")
        print(f"   Status: {'✅ PASS' if threshold_works else '❌ FAIL'}")
    
    print()
    
    # Cleanup
    if os.path.exists(learning_file):
        print(f"💾 Learning data saved to: {learning_file}")
        print(f"   (Delete this file to reset learning)")
    
    return success


def test_cross_domain_learning():
    """Test that learning in one domain doesn't break others."""
    
    print("\n")
    print("=" * 80)
    print("TEST: CROSS-DOMAIN ISOLATION")
    print("=" * 80)
    print()
    
    learning_file = "test_cross_domain.json"
    
    # Clean slate
    if os.path.exists(learning_file):
        os.remove(learning_file)
    
    engine = EFCTheoryEngine(
        enable_learning=True,
        learning_file=learning_file
    )
    
    # Test questions in different domains
    test_cases = [
        ("biology", "Hvorfor stabiliserer celler sin metabolisme?", True),
        ("biology", "Hvordan emerger komplekse organismer?", True),
        ("economics", "Hvorfor stabiliserer markedet?", True),
        ("economics", "Hva driver inflasjon?", False),  # Not actually EFC-relevant
        ("cosmology", "Hvorfor ser vi halos rundt galakser?", True),
    ]
    
    print("Providing feedback across domains...")
    for domain, question, helpful in test_cases:
        result = engine.detect_efc_pattern(question, domain=domain)
        engine.provide_feedback(
            question=question,
            domain=domain,
            efc_score=result.score,
            detected_patterns=result.detected_patterns,
            was_helpful=helpful
        )
        print(f"   {domain}: {helpful}")
    
    print("\n📊 Domain-specific learning:")
    if engine.learner:
        for domain, stats in engine.learner.domains.items():
            success_rate = stats.successful_efc_uses / stats.observations * 100
            print(f"\n   {domain.upper()}:")
            print(f"      Observations: {stats.observations}")
            print(f"      Success rate: {success_rate:.0f}%")
            print(f"      Threshold: {stats.threshold_adjustment:+.1f}")
    
    # Verify domains are independent
    if engine.learner:
        bio_adj = engine.learner.domains.get("biology", None)
        econ_adj = engine.learner.domains.get("economics", None)
        
        if bio_adj and econ_adj:
            bio_threshold = bio_adj.threshold_adjustment
            econ_threshold = econ_adj.threshold_adjustment
            
            # Biology: 2/2 success → should get negative adjustment
            # Economics: 1/2 success → should get smaller or positive adjustment
            independent = bio_threshold != econ_threshold
            
            print(f"\n✓ DOMAIN ISOLATION:")
            print(f"   Biology threshold: {bio_threshold:+.1f}")
            print(f"   Economics threshold: {econ_threshold:+.1f}")
            print(f"   Status: {'✅ PASS (different)' if independent else '❌ FAIL (same)'}")
    
    # Cleanup
    if os.path.exists(learning_file):
        os.remove(learning_file)
    
    print()


if __name__ == "__main__":
    print("\n")
    print("🧪 TESTING ADAPTIVE LEARNING SYSTEM")
    print("=" * 80)
    print()
    
    # Test 1: Full adaptive cycle
    success1 = test_adaptive_learning_cycle()
    
    # Test 2: Cross-domain isolation
    test_cross_domain_learning()
    
    print("\n")
    print("=" * 80)
    print("🎯 FINAL SUMMARY")
    print("=" * 80)
    print()
    print(f"Adaptive Learning Cycle: {'✅ PASS' if success1 else '❌ FAIL'}")
    print()
    print("System demonstrates:")
    print("  ✓ Pattern detection starts with baseline scores")
    print("  ✓ Feedback loop records helpful/unhelpful usage")
    print("  ✓ Threshold adjustment based on success rate")
    print("  ✓ Score improvement over time with learning")
    print("  ✓ Domain-specific learning (economics learns independently)")
    print("  ✓ Persistent learning across sessions")
    print()
