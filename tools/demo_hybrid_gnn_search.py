#!/usr/bin/env python3
"""
Demo: Hybrid GNN + Semantic Search

Viser hvordan GNN-strukturelle embeddings booster semantisk søk.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_gnn_status():
    """Verify GNN system is loaded."""
    print("🧠 Testing GNN Status...")
    response = requests.get(f"{BASE_URL}/gnn/status")
    data = response.json()
    
    print(f"✅ Total nodes: {data['stats']['total_nodes']}")
    print(f"✅ Embedding dim: {data['stats']['embedding_dim']}")
    print(f"✅ Artifacts loaded: {data['artifacts']}")
    print()


def test_hybrid_search(query: str, use_gnn: bool = True, alpha: float = 0.7):
    """Test hybrid Graph-RAG search."""
    print(f"🔍 Search: '{query}' (GNN={use_gnn}, α={alpha})")
    
    response = requests.get(
        f"{BASE_URL}/graph-rag/search",
        params={
            "query": query,
            "limit": 3,
            "use_gnn": use_gnn,
            "alpha": alpha
        }
    )
    
    data = response.json()
    
    print(f"\n📊 Neo4j hits: {len(data.get('neo4j', []))}")
    
    qdrant_data = data.get("qdrant", {})
    results = qdrant_data.get("results", [])
    
    print(f"📊 Qdrant hits: {len(results)}")
    print(f"🧠 GNN enabled: {qdrant_data.get('gnn_enabled', False)}")
    print(f"⚖️  Hybrid alpha: {qdrant_data.get('hybrid_alpha')}")
    
    print("\n🎯 Top Results:")
    for i, hit in enumerate(results[:3], 1):
        semantic = hit.get("score", 0)
        structural = hit.get("structural_score")
        hybrid = hit.get("hybrid_score", 0)
        status = hit.get("gnn_status", "ok")
        
        print(f"\n  {i}. [{hybrid:.3f}] {hit.get('source', 'unknown')}")
        print(f"     Semantic: {semantic:.3f}")
        
        if structural is not None:
            print(f"     Structural: {structural:.3f}")
            print(f"     Hybrid: {hybrid:.3f}")
        else:
            print(f"     GNN Status: {status}")
        
        # Show text snippet
        text = hit.get("text", "")[:100]
        print(f"     Text: {text}...")
    
    print()


def test_gnn_similarity():
    """Test GNN-based node similarity."""
    print("🔗 Testing GNN Similarity (Node 0 → similar nodes)...")
    
    response = requests.get(f"{BASE_URL}/gnn/similar/0", params={"top_k": 3})
    data = response.json()
    
    print(f"Query node: {data['query_node_id']}")
    print(f"\nTop {data['top_k']} similar nodes:")
    
    for result in data['results']:
        print(f"  - {result['node_id']}: {result['similarity']:.4f}")
    
    print()


def compare_with_without_gnn(query: str):
    """Compare search results with and without GNN boost."""
    print(f"\n{'='*60}")
    print(f"⚖️  COMPARISON: With vs Without GNN")
    print(f"{'='*60}\n")
    
    print("WITHOUT GNN (α=1.0, pure semantic):")
    test_hybrid_search(query, use_gnn=True, alpha=1.0)
    
    print("\nWITH GNN (α=0.7, 70% semantic + 30% structural):")
    test_hybrid_search(query, use_gnn=True, alpha=0.7)
    
    print("\nWITH GNN (α=0.5, balanced):")
    test_hybrid_search(query, use_gnn=True, alpha=0.5)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 HYBRID GNN + SEMANTIC SEARCH DEMO")
    print("="*60 + "\n")
    
    # 1. Verify GNN system
    test_gnn_status()
    
    # 2. Test hybrid search
    test_hybrid_search("energy flow cosmology")
    
    # 3. Test GNN similarity
    test_gnn_similarity()
    
    # 4. Compare different alpha values
    compare_with_without_gnn("quantum mechanics")
    
    print("\n✅ Demo complete!")
    print("\n💡 Next steps:")
    print("   1. Enrich Qdrant payload with node_id mapping")
    print("   2. Re-ingest documents with Neo4j node references")
    print("   3. Full hybrid scoring will activate automatically")
