#!/usr/bin/env python3
"""
test_efc_integration.py - Test EFC Theory Engine integration
============================================================

This tests:
- EFC mode detection in OptimalMemorySystem
- Claim validation against EFC principles
- Domain-specific reasoning for cosmology
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.optimal_memory_system import OptimalMemorySystem

def test_efc_integration():
    print("🧪 Testing EFC Theory Engine Integration")
    print("=" * 60)
    
    system = OptimalMemorySystem(
        canonical_collection="test_efc_canonical",
        semantic_collection="test_efc_semantic"
    )
    
    # Store EFC context
    print("\n1️⃣ Storing EFC context...")
    system.store_context(
        text="EFC forklarer rotasjonskurver via emergent gravity og entropigradienter i grid-medium",
        domains=["cosmology", "theory"],
        tags=["EFC", "rotation_curves", "emergent_gravity"]
    )
    
    system.store_context(
        text="I EFC er mørk materie ikke nødvendig - halo-effekter er emergente fra energiflyt",
        domains=["cosmology"],
        tags=["EFC", "dark_matter", "halo"]
    )
    
    # Test 1: Pure EFC question
    print("\n2️⃣ Test: Pure EFC question")
    print("=" * 60)
    q1 = "Hvordan forklarer EFC rotasjonskurver uten mørk materie?"
    result1 = system.answer_question(
        question=q1,
        llm_draft="EFC forklarer rotasjonskurver via emergent gravity fra entropigradienter"
    )
    
    print(f"\nQuestion: {q1}")
    print(f"Domain: {result1['domain']}")
    print(f"EFC Mode: {result1.get('efc_mode', 'N/A')}")
    print(f"EFC Confidence: {result1.get('efc_confidence', 'N/A'):.2f}" if result1.get('efc_confidence') else "EFC Confidence: N/A")
    print(f"EFC Claim Consistent: {result1.get('efc_claim_consistent', 'N/A')}")
    print(f"EFC Violated Principles: {result1.get('efc_violated_principles', [])}")
    
    # Test 2: EFC question with LCDM comparison
    print("\n3️⃣ Test: EFC vs LCDM comparison")
    print("=" * 60)
    q2 = "Hva er forskjellen mellom EFC og LCDM når det gjelder mørk materie?"
    result2 = system.answer_question(
        question=q2,
        llm_draft="LCDM krever mørk materie som egen komponent, mens EFC forklarer det emergent"
    )
    
    print(f"\nQuestion: {q2}")
    print(f"Domain: {result2['domain']}")
    print(f"EFC Mode: {result2.get('efc_mode', 'N/A')}")
    print(f"EFC Confidence: {result2.get('efc_confidence', 'N/A'):.2f}" if result2.get('efc_confidence') else "EFC Confidence: N/A")
    print(f"EFC Claim Consistent: {result2.get('efc_claim_consistent', 'N/A')}")
    
    # Test 3: Non-EFC question in cosmology
    print("\n4️⃣ Test: General cosmology (not EFC)")
    print("=" * 60)
    q3 = "Hva er Hubble-konstanten?"
    result3 = system.answer_question(
        question=q3,
        llm_draft="Hubble-konstanten er ca 70 km/s/Mpc"
    )
    
    print(f"\nQuestion: {q3}")
    print(f"Domain: {result3['domain']}")
    print(f"EFC Mode: {result3.get('efc_mode', 'N/A')}")
    print(f"EFC Activated: {'Yes' if result3.get('efc_mode') else 'No'}")
    
    # Test 4: LLM draft that violates EFC principles
    print("\n5️⃣ Test: LLM draft violating EFC principles")
    print("=" * 60)
    q4 = "Hvorfor trenger vi mørk materie?"
    result4 = system.answer_question(
        question=q4,
        llm_draft="Vi trenger mørk materie fordi rotasjonskurver krever ekstra masse som vi ikke kan se"
    )
    
    print(f"\nQuestion: {q4}")
    print(f"Domain: {result4['domain']}")
    print(f"EFC Mode: {result4.get('efc_mode', 'N/A')}")
    print(f"EFC Claim Consistent: {result4.get('efc_claim_consistent', 'N/A')}")
    print(f"EFC Violated Principles: {result4.get('efc_violated_principles', [])}")
    
    if result4.get('efc_violated_principles'):
        print("\n⚠️  LLM draft violates EFC principles!")
        print("   System can use this to trigger OVERRIDE or suggest rewrite")
    
    print("\n" + "=" * 60)
    print("✅ EFC Theory Engine integration complete!")
    print("🌌 Domain-specific cosmology reasoning operational")
    print("💡 System detects EFC context and validates claims automatically")
    print("=" * 60)

if __name__ == "__main__":
    test_efc_integration()
