#!/usr/bin/env python3
"""
Test memory-enhanced response generation in router.
Populates canonical memory, then sends queries that should trigger enhancement.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.optimal_memory_system import OptimalMemorySystem

def populate_test_memory():
    """Populate canonical memory with test facts."""
    print("🧠 Populating canonical memory with test facts...")
    
    memory = OptimalMemorySystem()
    session_id = "test_memory_enhancement"
    
    # Test facts - using CORRECT canonical domains from canonical_memory_schema.json
    test_facts = [
        {
            "key": "name",
            "value": "Morpheus",
            "domain": "identity",  # Correct domain!
            "fact_type": "name",
            "authority": "LONGTERM",
            "text": "User's name is Morpheus"
        },
        {
            "key": "occupation",
            "value": "architect",
            "domain": "identity",
            "fact_type": "general",
            "authority": "LONGTERM",
            "text": "User is the architect of the Energy-Flow Cosmology framework"
        },
        {
            "key": "language",
            "value": "Norwegian_English",
            "domain": "preferences",  # Correct domain!
            "fact_type": "general",
            "authority": "STABLE",
            "text": "User speaks Norwegian and prefers bilingual responses"
        },
        {
            "key": "expertise_1",
            "value": "EFC_architecture",
            "domain": "professional",  # Correct domain!
            "fact_type": "general",
            "authority": "LONGTERM",
            "text": "Expert in EFC architecture using Neo4j and Qdrant"
        },
        {
            "key": "tool_1",
            "value": "orchestrator_v2",
            "domain": "professional",
            "fact_type": "general",
            "authority": "LONGTERM",
            "text": "All data ingestion must use orchestrator_v2.py pipeline"
        }
    ]
    
    for fact in test_facts:
        try:
            memory.store_fact(
                key=fact["key"],
                value=fact["value"],
                domain=fact["domain"],
                fact_type=fact["fact_type"],
                authority=fact["authority"],
                text=fact["text"]
            )
            print(f"  ✅ Added: {fact['text'][:60]}...")
        except Exception as e:
            print(f"  ⚠️  Failed to add fact: {e}")
    
    # Store some semantic context
    test_chunks = [
        "The Energy-Flow Cosmology framework unifies quantum mechanics, general relativity, and thermodynamics through energy flow principles.",
        "Symbiose is the intelligent agent that orchestrates the EFC architecture, providing memory-driven reasoning and context-aware responses.",
        "The canonical memory contains high-authority facts, while semantic mesh provides contextual embeddings for nuanced understanding."
    ]
    
    for chunk in test_chunks:
        try:
            memory.store_context(
                text=chunk,
                domains=["theory"],
                tags=["background_knowledge"],
                source="test_data"
            )
            print(f"  ✅ Stored context: {chunk[:60]}...")
        except Exception as e:
            print(f"  ⚠️  Failed to store context: {e}")
    
    print("\n✅ Memory population complete!")
    return memory, session_id

def test_memory_enhanced_queries(memory, session_id):
    """Test queries that should trigger memory enhancement."""
    print("\n🧪 Testing memory-enhanced queries...\n")
    
    from tools.symbiosis_router_v4 import handle_chat_turn
    
    test_queries = [
        "Who am I?",
        "What is my role in this project?",
        "What databases does EFC use?",
        "How should I ingest new data into the system?",
        "Tell me about the Energy-Flow Cosmology framework",
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}/{len(test_queries)}: {query}")
        print(f"{'='*80}\n")
        
        try:
            result = handle_chat_turn(
                user_message=query,
                assistant_draft=f"[LLM would answer: {query}]",  # Simulated LLM draft
                session_id=session_id,
                enable_domain_analysis=True,
                enable_memory_enforcement=True,
                enable_gnn=False,  # Skip GNN for faster testing
                store_interaction=False  # Don't pollute memory during test
            )
            
            results.append({
                "query": query,
                "was_enhanced": result.get("was_overridden", False),
                "final_answer": result.get("final_answer", ""),
                "memory_stats": result.get("memory", {})
            })
            
            print(f"\n📊 Result:")
            print(f"   Enhanced: {result.get('was_overridden', False)}")
            print(f"   Canonical facts: {result.get('memory', {}).get('canonical_facts_count', 0)}")
            print(f"   Context chunks: {result.get('memory', {}).get('context_chunks_count', 0)}")
            print(f"\n💬 Response:\n{result.get('final_answer', '')[:300]}...")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "query": query,
                "error": str(e)
            })
    
    return results

def main():
    """Main test flow."""
    print("=" * 80)
    print("MEMORY-ENHANCED RESPONSE GENERATION TEST")
    print("=" * 80)
    print()
    
    # Step 1: Populate memory
    memory, session_id = populate_test_memory()
    
    # Step 2: Test queries
    results = test_memory_enhanced_queries(memory, session_id)
    
    # Step 3: Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    enhanced_count = sum(1 for r in results if r.get("was_enhanced", False))
    error_count = sum(1 for r in results if "error" in r)
    
    print(f"\nTotal queries: {len(results)}")
    print(f"Enhanced responses: {enhanced_count}")
    print(f"Raw LLM responses: {len(results) - enhanced_count - error_count}")
    print(f"Errors: {error_count}")
    
    if enhanced_count > 0:
        print(f"\n✅ SUCCESS: Memory enhancement working! ({enhanced_count}/{len(results)} queries enhanced)")
    else:
        print(f"\n⚠️  WARNING: No queries were enhanced. Check memory retrieval.")
    
    # Save results
    results_file = Path(__file__).parent / "test_memory_enhancement_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "test_type": "memory_enhancement",
            "session_id": session_id,
            "results": results,
            "summary": {
                "total": len(results),
                "enhanced": enhanced_count,
                "raw": len(results) - enhanced_count - error_count,
                "errors": error_count
            }
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")

if __name__ == "__main__":
    main()
