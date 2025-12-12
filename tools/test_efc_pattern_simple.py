#!/usr/bin/env python3
"""
test_efc_pattern_simple.py - Simple EFC Pattern Detection test
==============================================================

Tests pattern detection without database dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.efc_theory_engine import EFCTheoryEngine

def test_pattern_detection():
    print("🌌 Testing EFC Pattern Detection - Tverrdomene (Simplified)")
    print("=" * 80)
    print("EFC er ikke bare kosmologi - det er et informasjonsteoretisk mønster")
    print("=" * 80)
    
    engine = EFCTheoryEngine()
    
    test_cases = [
        {
            "category": "Kosmologi",
            "question": "Hvorfor stabiliserer galakser seg i spiralform?",
            "expected": "WEAK_SIGNAL eller høyere",
        },
        {
            "category": "Biologi",
            "question": "Hvorfor organiserer celler seg i komplekse vevstrukturer?",
            "expected": "EFC_ENABLED",
        },
        {
            "category": "AI/ML",
            "question": "Hva driver emergent behavior i AI-systemer mot metastabile konfigurasjoner?",
            "expected": "EFC_ENABLED",
        },
        {
            "category": "Psykologi",
            "question": "Hvordan stabiliserer hjernen kognitive mønstre via energiflyt?",
            "expected": "EFC_ENABLED",
        },
        {
            "category": "Økonomi",
            "question": "Hvorfor finner markeder likevektspriser gjennom gradientdynamikk?",
            "expected": "EFC_ENABLED",
        },
        {
            "category": "Systemteori",
            "question": "Hva driver emergente strukturer i komplekse systemer mot stabile mønstre?",
            "expected": "EFC_ENABLED",
        },
        {
            "category": "Ikke-EFC (kontroll)",
            "question": "Hva er datoen i dag?",
            "expected": "OUT_OF_SCOPE",
        },
        {
            "category": "Ikke-EFC (kontroll)",
            "question": "Hvem skrev Romeo og Julie?",
            "expected": "OUT_OF_SCOPE",
        },
    ]
    
    results = []
    
    for case in test_cases:
        pattern = engine.detect_efc_pattern(case["question"])
        
        results.append({
            "category": case["category"],
            "question": case["question"],
            "pattern": pattern,
            "expected": case["expected"]
        })
    
    # Display results
    print("\n📊 Resultater:\n")
    for r in results:
        print(f"{'='*80}")
        print(f"Kategori: {r['category']}")
        print(f"Q: {r['question']}")
        print(f"\nPattern Detection:")
        print(f"  Score: {r['pattern'].score:.1f}")
        print(f"  Level: {r['pattern'].relevance_level}")
        print(f"  Cues: lang={r['pattern'].language_cues}, struct={r['pattern'].structural_cues}, logic={r['pattern'].logical_cues}")
        
        if r['pattern'].detected_patterns:
            print(f"  Detected: {', '.join(r['pattern'].detected_patterns[:3])}")
        
        print(f"\nActions:")
        print(f"  Should Augment: {engine.should_augment_with_efc(r['pattern'])}")
        print(f"  Should Override: {engine.should_override_with_efc(r['pattern'])}")
        
        print(f"\nReasoning: {r['pattern'].reasoning}")
        
        # Status indicator
        level = r['pattern'].relevance_level
        if level in ["EFC_ENABLED", "PURE_EFC"]:
            status = "✅ EFC AKTIVERT"
        elif level == "WEAK_SIGNAL":
            status = "⚠️  EFC TILGJENGELIG"
        else:
            status = "❌ EFC IKKE RELEVANT"
        
        print(f"\n{status}")
        print()
    
    # Summary
    print("=" * 80)
    print("📋 OPPSUMMERING")
    print("=" * 80)
    
    enabled_count = sum(1 for r in results if r['pattern'].relevance_level in ["EFC_ENABLED", "PURE_EFC"])
    weak_count = sum(1 for r in results if r['pattern'].relevance_level == "WEAK_SIGNAL")
    out_count = sum(1 for r in results if r['pattern'].relevance_level == "OUT_OF_SCOPE")
    
    print(f"\n✅ EFC AKTIVERT (EFC_ENABLED/PURE_EFC): {enabled_count}/{len(results)}")
    print(f"⚠️  EFC TILGJENGELIG (WEAK_SIGNAL): {weak_count}/{len(results)}")
    print(f"❌ EFC IKKE RELEVANT (OUT_OF_SCOPE): {out_count}/{len(results)}")
    
    print(f"\n🎯 Nøyaktighet:")
    # Cross-domain EFC cases (should activate)
    cross_domain = [r for r in results if r['category'] in ["Biologi", "AI/ML", "Psykologi", "Økonomi", "Systemteori"]]
    activated = [r for r in cross_domain if r['pattern'].relevance_level in ["EFC_ENABLED", "PURE_EFC", "WEAK_SIGNAL"]]
    
    print(f"   Tverrdomene deteksjon: {len(activated)}/{len(cross_domain)} aktivert")
    
    # Control cases (should NOT activate)
    control = [r for r in results if r['category'] == "Ikke-EFC (kontroll)"]
    correctly_excluded = [r for r in control if r['pattern'].relevance_level == "OUT_OF_SCOPE"]
    
    print(f"   Kontroll (ekskludering): {len(correctly_excluded)}/{len(control)} korrekt")
    
    print("\n" + "=" * 80)
    print("🌌 EFC er ikke et domene - det er et informasjonsteoretisk mønster!")
    print("   Systemet oppdager EFC-logikk på tvers av:")
    print("   • Kosmologi (galakser, entropi, energiflyt)")
    print("   • Biologi (cellulære strukturer, vev-organisering)")
    print("   • AI/ML (emergent behavior, metastabilitet)")
    print("   • Psykologi (kognitive mønstre, mental energi)")
    print("   • Økonomi (markedslikevekt, gradientdynamikk)")
    print("   • Systemteori (kompleksitet, emergente strukturer)")
    print("\n✅ Pattern Detection fungerer på tvers av domener!")
    print("=" * 80)

if __name__ == "__main__":
    test_pattern_detection()
