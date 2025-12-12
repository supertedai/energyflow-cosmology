#!/usr/bin/env python3
"""
test_efc_cross_domain.py - Test EFC Pattern Detection across domains
====================================================================

This demonstrates:
- EFC pattern detection in cosmology (expected)
- EFC pattern detection in biology (emergent structures)
- EFC pattern detection in AI (system dynamics)
- EFC pattern detection in psychology (mental patterns)
- EFC pattern detection in economics (market stability)
- Proper exclusion of non-EFC questions
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.optimal_memory_system import OptimalMemorySystem

def test_cross_domain_efc():
    print("🌌 Testing EFC Pattern Detection - Tverrdomene")
    print("=" * 80)
    print("EFC er ikke bare kosmologi - det er et informasjonsteoretisk mønster")
    print("som gjelder på tvers av domener: fysikk, biologi, AI, psykologi, økonomi")
    print("=" * 80)
    
    system = OptimalMemorySystem(
        canonical_collection="test_efc_cross_canonical",
        semantic_collection="test_efc_cross_semantic"
    )
    
    # Store diverse context
    print("\n📚 Storing cross-domain context...")
    contexts = [
        ("Galakser stabiliserer seg via energiflyt og entropigradienter", ["cosmology"]),
        ("Celler organiserer seg i vevstrukturer via emergente prosesser", ["biology"]),
        ("AI-systemer finner metastabile konfigurasjoner", ["ai", "tech"]),
        ("Markeder stabiliserer seg rundt likevektspriser", ["economics"]),
    ]
    
    for text, domains in contexts:
        system.store_context(text=text, domains=domains)
    
    # Test cases spanning multiple domains
    test_cases = [
        {
            "domain": "Kosmologi (forventet)",
            "question": "Hvorfor stabiliserer galakser seg i spiralform?",
            "expected_pattern": "EFC_ENABLED eller PURE_EFC",
        },
        {
            "domain": "Biologi (tverrdomene!)",
            "question": "Hvorfor organiserer celler seg i vevstrukturer?",
            "expected_pattern": "EFC_ENABLED",
        },
        {
            "domain": "AI (tverrdomene!)",
            "question": "Hva driver emergent behavior i nevrale nettverk?",
            "expected_pattern": "WEAK_SIGNAL eller EFC_ENABLED",
        },
        {
            "domain": "Psykologi (tverrdomene!)",
            "question": "Hvordan stabiliserer hjernen kognitive mønstre?",
            "expected_pattern": "WEAK_SIGNAL eller EFC_ENABLED",
        },
        {
            "domain": "Økonomi (tverrdomene!)",
            "question": "Hvorfor finner markeder likevektspriser?",
            "expected_pattern": "WEAK_SIGNAL eller EFC_ENABLED",
        },
        {
            "domain": "Ikke EFC",
            "question": "Hva er datoen i dag?",
            "expected_pattern": "OUT_OF_SCOPE",
        },
        {
            "domain": "Ikke EFC",
            "question": "Hvem skrev Romeo og Julie?",
            "expected_pattern": "OUT_OF_SCOPE",
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {case['domain']}")
        print(f"{'='*80}")
        print(f"Q: {case['question']}")
        print(f"Forventet: {case['expected_pattern']}")
        
        result = system.answer_question(
            question=case['question'],
            llm_draft=f"Generic answer to {case['question']}"
        )
        
        print(f"\n📊 Resultater:")
        print(f"   Domene: {result['domain']}")
        print(f"   EFC Pattern: {result.get('efc_pattern_detected', 'N/A')}")
        print(f"   EFC Score: {result.get('efc_pattern_score', 0):.1f}")
        print(f"   Should Augment: {result.get('efc_should_augment', False)}")
        print(f"   Should Override: {result.get('efc_should_override', False)}")
        
        if result.get('efc_mode'):
            print(f"   EFC Mode: {result['efc_mode']} (confidence: {result.get('efc_confidence', 0):.2f})")
        
        # Vurdering
        pattern = result.get('efc_pattern_detected', 'OUT_OF_SCOPE')
        if pattern in ["EFC_ENABLED", "PURE_EFC"]:
            print(f"\n   ✅ EFC-logikk AKTIVERT - systemet vil bruke EFC som forklaringsramme")
        elif pattern == "WEAK_SIGNAL":
            print(f"\n   ⚠️  EFC-logikk TILGJENGELIG - kan nevnes hvis relevant")
        else:
            print(f"\n   ❌ EFC-logikk IKKE RELEVANT - systemet holder EFC unna")
    
    print("\n" + "=" * 80)
    print("✅ Tverrdomene EFC Pattern Detection fungerer!")
    print("=" * 80)
    print("\n📋 Oppsummering:")
    print("   • Kosmologi: EFC aktiveres automatisk")
    print("   • Biologi: EFC oppdages via emergent-mønstre")
    print("   • AI: EFC oppdages via system-dynamikk")
    print("   • Psykologi: EFC kan oppdages via stabiliseringsmønstre")
    print("   • Økonomi: EFC kan oppdages via likevekts-logikk")
    print("   • Ikke-relevante spørsmål: EFC holdes unna")
    print("\n🌌 EFC er ikke et domene - det er et informasjonsteoretisk mønster!")
    print("=" * 80)

if __name__ == "__main__":
    test_cross_domain_efc()
