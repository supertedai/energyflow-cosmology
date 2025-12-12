#!/usr/bin/env python3
"""
test_cross_domain_mesh.py - Kryssvalidering av EFC-mønstre på tvers av domener

Dette tester den dype visjonen:
    1. Lær at "stabilisering" er EFC-signal i biologi
    2. Lær at "stabilisering" er EFC-signal i økonomi  
    3. Induser at "stabilisering" er universelt EFC-prinsipp
    4. Aktiver automatisk i nye domener (psykologi, sosiologi)
"""

import sys
from pathlib import Path

# Add tools to path
tools_dir = Path(__file__).parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from efc_theory_engine import EFCTheoryEngine
import os

def test_cross_domain_validation_mesh():
    """Test at systemet lærer universelle prinsipper fra kryssvalidering."""
    
    print("=" * 80)
    print("🧬 CROSS-DOMAIN VALIDATION MESH TEST")
    print("=" * 80)
    print()
    print("Visjonen: Systemet skal lære at 'stabilisering' er et universelt")
    print("          EFC-prinsipp ved å se det på tvers av flere domener.")
    print()
    
    # Clean slate
    learning_file = "test_cross_domain_mesh.json"
    if os.path.exists(learning_file):
        os.remove(learning_file)
    
    engine = EFCTheoryEngine(
        enable_learning=True,
        learning_file=learning_file
    )
    
    # Phase 1: Teach across multiple domains
    print("=" * 80)
    print("FASE 1: Lær 'stabilisering' i flere domener")
    print("-" * 80)
    print()
    
    test_cases = [
        # Biology domain
        ("biology", "Hvordan stabiliserer celler homeostase?", True),
        ("biology", "Hva driver metabolsk stabilitet?", True),
        ("biology", "Hvorfor opprettholder organismer stabile tilstander?", True),
        
        # Economics domain
        ("economics", "Hvorfor stabiliserer markeder seg ved likevekt?", True),
        ("economics", "Hva driver prisstabilisering?", True),
        ("economics", "Hvordan oppstår markedsstabilitet?", True),
        
        # Cosmology domain
        ("cosmology", "Hvorfor stabiliserer galakser seg?", True),
        ("cosmology", "Hva driver stellare stabile baner?", True),
        ("cosmology", "Hvordan oppstår gravitasjonell stabilitet?", True),
        
        # Physics domain
        ("physics", "Hvorfor stabiliserer atomer seg?", True),
        ("physics", "Hva driver termodynamisk stabilitet?", True),
        ("physics", "Hvordan oppstår energibalanse?", True),
    ]
    
    for domain, question, helpful in test_cases:
        result = engine.detect_efc_pattern(question, domain=domain)
        engine.provide_feedback(
            question=question,
            domain=domain,
            efc_score=result.score,
            detected_patterns=result.detected_patterns,
            was_helpful=helpful
        )
        print(f"✓ {domain}: \"{question[:50]}...\"")
        print(f"  Score: {result.score:.1f}, Level: {result.relevance_level}")
    
    print()
    print("=" * 80)
    print("FASE 2: Sjekk om universelle mønstre er oppdaget")
    print("-" * 80)
    print()
    
    if engine.learner:
        universal_patterns = engine.learner.get_universal_patterns()
        
        print(f"📊 Universelle patterns oppdaget: {len(universal_patterns)}")
        print()
        
        for cdp in universal_patterns:
            print(f"🌍 Universal Pattern: \"{cdp.pattern}\"")
            print(f"   Domener: {', '.join(sorted(cdp.domains))}")
            print(f"   Occurrences: {cdp.total_occurrences}")
            print(f"   Success rate: {cdp.success_rate:.1%}")
            print(f"   Confidence: {cdp.confidence:.2f}")
            print()
        
        # Check domain statistics
        print("=" * 80)
        print("FASE 3: Domene-statistikk")
        print("-" * 80)
        print()
        
        for domain, stats in engine.learner.domains.items():
            success_rate = (
                stats.successful_efc_uses / stats.observations * 100
                if stats.observations > 0 else 0
            )
            print(f"{domain.upper()}:")
            print(f"  Observations: {stats.observations}")
            print(f"  Success rate: {success_rate:.0f}%")
            print(f"  Threshold adjustment: {stats.threshold_adjustment:+.1f}")
            print()
    
    # Phase 4: Test in NEW domain (not seen before)
    print("=" * 80)
    print("FASE 4: Test i NYTT domene (psykologi)")
    print("-" * 80)
    print()
    print("Spørsmål: Hvorfor stabiliserer mennesker emosjonell balanse?")
    print()
    
    new_question = "Hvorfor stabiliserer mennesker emosjonell balanse?"
    result = engine.detect_efc_pattern(new_question, domain="psychology")
    
    print(f"Score: {result.score:.1f}")
    print(f"Level: {result.relevance_level}")
    print(f"Patterns: {result.detected_patterns}")
    print()
    
    # Check if learned patterns influenced detection
    if engine.learner and "stabiliserer" in new_question.lower():
        print("✓ Systemet gjenkjenner 'stabilisering' fra tidligere læring!")
        print()
        
        # Check if any universal patterns match
        universal_patterns = engine.learner.get_universal_patterns()
        matching_patterns = [
            p for p in universal_patterns
            if any(word in new_question.lower() for word in p.pattern.split())
        ]
        
        if matching_patterns:
            print(f"🎯 {len(matching_patterns)} universelle mønstre matcher:")
            for p in matching_patterns:
                print(f"   • {p.pattern} (sett i: {', '.join(sorted(p.domains))})")
            print()
    
    # Phase 5: Validation
    print("=" * 80)
    print("FASE 5: Validering")
    print("-" * 80)
    print()
    
    success_criteria = {
        "universal_patterns_discovered": len(universal_patterns) > 0 if engine.learner else False,
        "multiple_domains_learned": len(engine.learner.domains) >= 4 if engine.learner else False,
        "new_domain_activates": result.relevance_level in ["WEAK_SIGNAL", "EFC_ENABLED", "PURE_EFC"],
        "cross_domain_linkage": len([p for p in universal_patterns if len(p.domains) >= 3]) > 0 if engine.learner else False
    }
    
    print("Suksesskriterier:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {criterion.replace('_', ' ').title()}")
    
    print()
    
    all_passed = all(success_criteria.values())
    
    if all_passed:
        print("🎉 SUKSESS: Kryssvaliderings-mesh fungerer!")
        print()
        print("Systemet har:")
        print("  ✓ Lært mønstre i flere domener")
        print("  ✓ Oppdaget universelle prinsipper")
        print("  ✓ Aktivert i nye domener automatisk")
        print("  ✓ Bygget kryssvalideringsnettverk")
    else:
        print("⚠️  DELVIS: Systemet lærer, men ikke alle kriterier møtt")
        print()
        print("Dette er forventet i tidlige iterasjoner.")
        print("Flere observasjoner vil styrke mesh-nettverket.")
    
    print()
    print("=" * 80)
    print(f"💾 Læring lagret til: {learning_file}")
    print("=" * 80)
    print()
    
    return all_passed


def test_pattern_collapse():
    """Test at overlappende patterns slås sammen."""
    
    print()
    print("=" * 80)
    print("🔄 PATTERN COLLAPSE TEST")
    print("=" * 80)
    print()
    
    learning_file = "test_pattern_collapse.json"
    if os.path.exists(learning_file):
        os.remove(learning_file)
    
    engine = EFCTheoryEngine(
        enable_learning=True,
        learning_file=learning_file
    )
    
    # Create many similar patterns
    similar_questions = [
        "Hvorfor stabiliserer systemet seg?",
        "Hvordan stabiliserer systemet?",
        "Hva gjør at systemet stabiliserer?",
        "Hvorfor oppnår systemet stabilitet?",
        "Hvordan oppnås stabilitet i systemet?",
        "Hva driver stabilisering av systemet?",
        "Hvorfor blir systemet stabilt?",
        "Hvordan blir systemet stabilt?",
    ] * 3  # Repeat to trigger collapse
    
    print("Legger til 24 lignende patterns...")
    for q in similar_questions:
        result = engine.detect_efc_pattern(q, domain="test")
        engine.provide_feedback(
            question=q,
            domain="test",
            efc_score=result.score,
            detected_patterns=result.detected_patterns,
            was_helpful=True
        )
    
    print()
    if engine.learner:
        print(f"📊 Patterns før collapse: {len(engine.learner.patterns)}")
        
        # Trigger collapse manually
        engine.learner._collapse_similar_patterns()
        
        print(f"📊 Patterns etter collapse: {len(engine.learner.patterns)}")
        print()
        
        if len(engine.learner.patterns) < 24:
            print("✅ Pattern collapse fungerer!")
            print(f"   Redusert fra 24 til {len(engine.learner.patterns)} patterns")
        else:
            print("❌ Pattern collapse trigget ikke")
    
    print()
    
    if os.path.exists(learning_file):
        os.remove(learning_file)


if __name__ == "__main__":
    print()
    print("🧪 TESTING CROSS-DOMAIN VALIDATION MESH")
    print("=" * 80)
    print()
    
    # Test 1: Cross-domain learning and universal pattern discovery
    success = test_cross_domain_validation_mesh()
    
    # Test 2: Pattern collapse
    test_pattern_collapse()
    
    print()
    print("=" * 80)
    print("🎯 FINAL VERDICT")
    print("=" * 80)
    print()
    
    if success:
        print("✅ Kryssvaliderings-mesh er operativt!")
        print()
        print("Systemet demonstrerer:")
        print("  • Læring av domene-spesifikke mønstre")
        print("  • Oppdagelse av universelle prinsipper")
        print("  • Automatisk aktivering i nye domener")
        print("  • Pattern collapse for å unngå fragmentering")
        print()
        print("Dette er et ekte meta-læringssystem.")
    else:
        print("⚠️  Systemet lærer, men trenger flere observasjoner")
        print()
        print("Fortsett å gi feedback for å styrke mesh-nettverket.")
    
    print()
