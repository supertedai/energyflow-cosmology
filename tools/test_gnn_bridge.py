#!/usr/bin/env python3
"""
Test node_id Bridge: Neo4j → Qdrant → GNN

Demonstrerer full hybrid scoring når node_id er koblet.
"""

import requests
import json
import os

BASE_URL = "http://localhost:8000"

# Test document with node_id
TEST_DOC = {
    "text": "Energy Flow Cosmology describes how energy patterns create structure across scales, from quantum to cosmic domains.",
    "source": "test/gnn-bridge-demo.md",
    "layer": "theory",
    "title": "GNN Bridge Test Document",
    "source_type": "test",
    "node_id": "4:0510400c-73e2-41ce-8a81-28016a9739c2:0"  # Real node from GNN mapping
}


def test_ingest_with_node_id():
    """Ingest document WITH node_id mapping."""
    print("🔗 Testing Ingest WITH node_id Bridge...")
    
    response = requests.post(
        f"{BASE_URL}/ingest/text",
        json=TEST_DOC
    )
    
    result = response.json()
    print(f"✅ Ingest: {result.get('status')}")
    print(f"   Chunks: {result.get('chunks_ingested')}")
    print()


def test_hybrid_search_with_bridge():
    """Test hybrid search – should now have structural_score."""
    print("🧠 Testing Hybrid Search WITH Bridge...")
    
    response = requests.get(
        f"{BASE_URL}/graph-rag/search",
        params={
            "query": "energy flow cosmology structure",
            "limit": 3,
            "use_gnn": True,
            "alpha": 0.6  # 60% semantic, 40% structural
        }
    )
    
    data = response.json()
    results = data.get("qdrant", {}).get("results", [])
    
    print(f"📊 Results: {len(results)}")
    print(f"🧠 GNN enabled: {data.get('qdrant', {}).get('gnn_enabled')}")
    print(f"⚖️  Hybrid alpha: {data.get('qdrant', {}).get('hybrid_alpha')}")
    
    print("\n🎯 Top Results:")
    for i, hit in enumerate(results[:3], 1):
        semantic = hit.get("score", 0)
        structural = hit.get("structural_score")
        hybrid = hit.get("hybrid_score", 0)
        node_id = hit.get("payload", {}).get("node_id")
        source = hit.get("source", "unknown")
        
        print(f"\n  {i}. [{hybrid:.3f}] {source}")
        print(f"     Semantic:    {semantic:.3f}")
        
        if structural is not None:
            print(f"     Structural:  {structural:.3f} ✅")
            print(f"     Hybrid:      {hybrid:.3f}")
            print(f"     Node ID:     {node_id}")
            
            # Show GNN neighbors
            neighbors = hit.get("gnn_neighbors", [])
            if neighbors:
                print(f"     GNN Neighbors:")
                for n in neighbors[:2]:
                    print(f"       - {n['node_id'][:30]}... ({n['similarity']:.3f})")
        else:
            status = hit.get("gnn_status", "unknown")
            print(f"     GNN Status:  {status} ⚠️")
    
    print()
    
    # Check if our test doc got boosted
    test_hit = next((h for h in results if "gnn-bridge-demo" in h.get("source", "")), None)
    if test_hit:
        print("✅ Test document found in results!")
        structural = test_hit.get("structural_score")
        if structural is not None:
            print(f"   🧠 Structural score: {structural:.3f}")
            print(f"   ✅ GNN BRIDGE ACTIVE!")
        else:
            print("   ⚠️  No structural score (bridge not active)")
    else:
        print("⚠️  Test document not in top results")
    
    print()


def compare_alpha_values():
    """Compare different alpha weightings."""
    print("⚖️  ALPHA COMPARISON: Structural Weight Impact\n")
    
    queries = ["energy flow", "quantum structure"]
    alphas = [1.0, 0.7, 0.5, 0.3]  # 100% semantic → 70% structural
    
    for query in queries:
        print(f"Query: '{query}'")
        for alpha in alphas:
            response = requests.get(
                f"{BASE_URL}/graph-rag/search",
                params={"query": query, "limit": 1, "use_gnn": True, "alpha": alpha}
            )
            
            data = response.json()
            results = data.get("qdrant", {}).get("results", [])
            
            if results:
                hit = results[0]
                hybrid = hit.get("hybrid_score", 0)
                source = hit.get("source", "")[:40]
                print(f"  α={alpha:.1f}: [{hybrid:.3f}] {source}")
        print()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔗 GNN BRIDGE TEST: Neo4j → Qdrant → GNN")
    print("="*60 + "\n")
    
    # 1. Ingest test document WITH node_id
    test_ingest_with_node_id()
    
    # 2. Search with hybrid scoring
    test_hybrid_search_with_bridge()
    
    # 3. Compare alpha values
    compare_alpha_values()
    
    print("✅ Bridge test complete!\n")
    print("💡 If structural_score appears, GNN bridge is ACTIVE ✅")
    print("   If 'no_node_id_mapping', re-ingest with node_id ⚠️")
