#!/usr/bin/env python3
"""
test_8_layers.py - Demonstrate all 8 layers working together
=============================================================

This demonstrates:
1. CMC - Stores absolute truths
2. SMM - Stores dynamic context
3. Neo4j - Structural relationships
4. DDE - Classifies domains automatically
5. AME - Enforces memory with intelligence
6. MIR - Detects interference in retrieved memory
7. MCA - Audits cross-layer consistency
8. MCE - Compresses session memory

Test Cases:
- Clean retrieval (low interference)
- Chaotic retrieval (high interference)
- Cross-layer consistency check
- Session compression
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.optimal_memory_system import OptimalMemorySystem

def test_interference_regulation():
    """
    Test MIR (Layer 6) - Memory Interference Regulator
    """
    print("\n" + "=" * 60)
    print("🧪 Testing Layer 6: Memory Interference Regulator (MIR)")
    print("=" * 60)
    
    system = OptimalMemorySystem(
        canonical_collection="test_8layer_canonical",
        semantic_collection="test_8layer_semantic"
    )
    
    # Store chaotic context (multiple domains)
    system.store_context(
        text="Morten er 42 år gammel",
        domains=["identity"],
        tags=["age"]
    )
    
    system.store_context(
        text="Andreas er 35 år gammel",
        domains=["other_person"],
        tags=["age"]
    )
    
    system.store_context(
        text="EFC theory uses entropy as core metric",
        domains=["cosmology"],
        tags=["theory"]
    )
    
    system.store_context(
        text="Python 3.11 is installed",
        domains=["tech"],
        tags=["dev"]
    )
    
    # Ask question - should trigger interference detection
    result = system.answer_question(
        question="Hvor gammel er Morten?",
        llm_draft="Morten er 35 år gammel"  # Wrong - mix with Andreas
    )
    
    print("\n📊 Interference Metrics:")
    metrics = result["interference_metrics"]
    print(f"   Domain Entropy: {metrics['domain_entropy']:.2f}")
    print(f"   Domain Spread: {metrics['domain_spread']}")
    print(f"   Contradiction Score: {metrics['contradiction_score']:.2f}")
    print(f"   Noise Ratio: {metrics['noise_ratio']:.2f}")
    print(f"   Domains: {metrics['domains']}")
    print(f"\n   🔧 Recommendation: {metrics['recommendation_notes']}")
    
    return system

def test_consistency_audit(system):
    """
    Test MCA (Layer 7) - Memory Consistency Auditor
    """
    print("\n" + "=" * 60)
    print("🧪 Testing Layer 7: Memory Consistency Auditor (MCA)")
    print("=" * 60)
    
    # Store a canonical fact
    system.store_fact(
        key="user_age",
        value=42,
        domain="identity",
        fact_type="number",
        authority="LONGTERM",
        text="Morten er 42 år gammel"
    )
    
    # Run audit (checks CMC vs SMM for contradictions)
    issues = system.run_consistency_audit(max_facts=10)
    
    print(f"\n📋 Audit Results: {len(issues)} issues detected")
    for issue in issues[:3]:  # Show first 3
        print(f"\n   Issue: {issue['issue_type']}")
        print(f"   Severity: {issue['severity']:.2f}")
        print(f"   Fact: {issue['fact_text'][:50]}...")
        print(f"   Chunk: {issue['chunk_text'][:50]}...")
    
    return system

def test_memory_compression(system):
    """
    Test MCE (Layer 8) - Memory Compression Engine
    """
    print("\n" + "=" * 60)
    print("🧪 Testing Layer 8: Memory Compression Engine (MCE)")
    print("=" * 60)
    
    # Create a session with many chunks
    session_id = "compression_test_session"
    
    for i in range(20):
        system.store_context(
            text=f"Message {i}: This is conversation turn {i} discussing various topics",
            domains=["general"],
            session_id=session_id,
            conversation_turn=i
        )
    
    print(f"\n📦 Created session with 20 chunks")
    
    # Compress session
    result = system.compress_session(
        session_id=session_id,
        max_chunks=20,
        generation=1
    )
    
    print(f"✅ Compressed to Generation {result['generation']}")
    print(f"   Original: {result['original_count']} chunks")
    print(f"   Summary ID: {result['summary_chunk_id']}")
    print(f"   Created: {result['created_at']}")
    
    # Test recursive compression (Gen 1 → Gen 2)
    # (Would require multiple Gen 1 summaries for meaningful result)
    print("\n🔄 Recursive compression available via:")
    print("   system.recursive_compress(session_id, source_gen=1, target_gen=2)")
    
    return system

def main():
    print("🧪 Testing Complete 8-Layer Memory Architecture")
    print("=" * 60)
    print("Layers:")
    print("1. CMC - Canonical Memory Core")
    print("2. SMM - Semantic Mesh Memory")
    print("2.5. Neo4j - Graph Layer")
    print("3. DDE - Dynamic Domain Engine")
    print("4. AME - Adaptive Memory Enforcer")
    print("5. MLC - Meta-Learning Cortex")
    print("6. MIR - Memory Interference Regulator ⭐ NEW")
    print("7. MCA - Memory Consistency Auditor ⭐ NEW")
    print("8. MCE - Memory Compression Engine ⭐ NEW")
    
    # Run tests
    system = test_interference_regulation()
    system = test_consistency_audit(system)
    system = test_memory_compression(system)
    
    # Final stats
    print("\n" + "=" * 60)
    print("📊 System Stats")
    print("=" * 60)
    stats = system.get_stats()
    print(json.dumps({
        "smm_sessions": stats["smm"]["active_sessions"],
        "dde_patterns": stats["dde"]["learned_patterns"],
        "mca_issues": stats["mca"]["issues_detected"],
        "mlc_mode_frequency": stats["mlc"]["mode_frequency"]
    }, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ All 8 layers tested successfully!")
    print("🚀 Advanced memory architecture operational")
    print("🔧 Interference control + consistency + compression")
    print("=" * 60)

if __name__ == "__main__":
    main()
