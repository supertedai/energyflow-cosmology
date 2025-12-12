#!/usr/bin/env python3
"""
Validator - Sync validation between Qdrant + Neo4j + GNN
=========================================================

Implements the 4 critical tests:
1. Semantic roundtrip (Qdrant → Neo4j consistency)
2. Graph → Vector mirror (Neo4j → Qdrant consistency)
3. Drift over time (growth rate analysis)
4. Human checkpoint (manual verification helpers)

Usage:
    python tools/validator.py --test semantic-roundtrip
    python tools/validator.py --test graph-mirror
    python tools/validator.py --test drift
    python tools/validator.py --test all
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

load_dotenv()

# Config
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# ============================================================
# TEST 1: SEMANTIC ROUNDTRIP
# ============================================================

def test_semantic_roundtrip(query: str = "entropy", limit: int = 5) -> Dict:
    """
    Test: Qdrant → Neo4j consistency
    
    Steps:
    1. Search Qdrant for query
    2. For each result, check if it exists in Neo4j
    3. Verify metadata matches
    
    Returns:
        {
            "passed": bool,
            "total_checked": int,
            "found_in_neo4j": int,
            "mismatches": List[Dict]
        }
    """
    print(f"\n🔍 Test 1: Semantic Roundtrip")
    print(f"   Query: '{query}', Limit: {limit}")
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Step 1: Search Qdrant
    # Use Qdrant's text search instead of vector search for simplicity
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from apis.unified_api.clients.embed_client import embed_text
    query_vector = embed_text(query)
    
    results = qdrant_client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )
    
    print(f"   ✅ Found {len(results)} results in Qdrant")
    
    # Step 2: Check each in Neo4j
    found_in_neo4j = 0
    mismatches = []
    
    with neo4j_driver.session() as session:
        for hit in results:
            chunk_id = str(hit.id)
            payload = hit.payload or {}
            
            # Look up in Neo4j (use elementId from node_id)
            # node_id format: "4:fe48cce7-a82b-4cdd-a7d3-73c60da2df6d:9263"
            neo4j_node_id = payload.get("node_id")
            
            if not neo4j_node_id:
                mismatches.append({
                    "chunk_id": chunk_id,
                    "issue": "no_node_id_in_qdrant"
                })
                continue
            
            result = session.run("""
                MATCH (c:Chunk)
                WHERE elementId(c) = $neo4j_node_id
                RETURN c.text AS text,
                       c.source AS source
            """, neo4j_node_id=neo4j_node_id)
            
            record = result.single()
            
            if record:
                found_in_neo4j += 1
                
                # Verify metadata match
                neo4j_text = record["text"] or ""
                qdrant_text = payload.get("text", "")[:500]
                
                if neo4j_text != qdrant_text:
                    mismatches.append({
                        "chunk_id": chunk_id,
                        "issue": "text_mismatch",
                        "qdrant_text_len": len(qdrant_text),
                        "neo4j_text_len": len(neo4j_text)
                    })
            else:
                mismatches.append({
                    "chunk_id": chunk_id,
                    "issue": "not_found_in_neo4j"
                })
    
    neo4j_driver.close()
    
    passed = found_in_neo4j == len(results) and len(mismatches) == 0
    
    result = {
        "test": "semantic_roundtrip",
        "passed": passed,
        "total_checked": len(results),
        "found_in_neo4j": found_in_neo4j,
        "mismatches": mismatches
    }
    
    print(f"   {'✅ PASSED' if passed else '❌ FAILED'}")
    print(f"   Found in Neo4j: {found_in_neo4j}/{len(results)}")
    if mismatches:
        print(f"   ⚠️  Mismatches: {len(mismatches)}")
    
    return result

# ============================================================
# TEST 2: GRAPH → VECTOR MIRROR
# ============================================================

def test_graph_mirror(concept_name: str = "Entropy → Clarity Model") -> Dict:
    """
    Test: Neo4j → Qdrant consistency
    
    Steps:
    1. Find concept in Neo4j
    2. Get all chunks mentioning it
    3. Verify chunks exist in Qdrant
    
    Returns:
        {
            "passed": bool,
            "concept": str,
            "chunks_in_neo4j": int,
            "chunks_in_qdrant": int,
            "missing_in_qdrant": List[str]
        }
    """
    print(f"\n🔍 Test 2: Graph → Vector Mirror")
    print(f"   Concept: '{concept_name}'")
    
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    with neo4j_driver.session() as session:
        # Find concept and its chunks (use RELATED_TO since that's the actual relation)
        result = session.run("""
            MATCH (concept:Concept {name: $concept_name})
            OPTIONAL MATCH (chunk:Chunk)-[:RELATED_TO]->(concept)
            RETURN concept.name AS concept,
                   [c IN collect(chunk) | elementId(c)] AS chunk_ids
        """, concept_name=concept_name)
        
        record = result.single()
        
        if not record:
            print(f"   ❌ Concept not found in Neo4j")
            return {
                "test": "graph_mirror",
                "passed": False,
                "concept": concept_name,
                "error": "concept_not_found"
            }
        
        chunk_ids = record["chunk_ids"]
        print(f"   ✅ Found {len(chunk_ids)} chunks in Neo4j")
    
    neo4j_driver.close()
    
    # Check each in Qdrant
    missing_in_qdrant = []
    found_in_qdrant = 0
    
    for chunk_id in chunk_ids:
        try:
            points = qdrant_client.retrieve(
                collection_name=QDRANT_COLLECTION,
                ids=[chunk_id]
            )
            if points:
                found_in_qdrant += 1
            else:
                missing_in_qdrant.append(chunk_id)
        except:
            missing_in_qdrant.append(chunk_id)
    
    passed = len(missing_in_qdrant) == 0
    
    result = {
        "test": "graph_mirror",
        "passed": passed,
        "concept": concept_name,
        "chunks_in_neo4j": len(chunk_ids),
        "chunks_in_qdrant": found_in_qdrant,
        "missing_in_qdrant": missing_in_qdrant
    }
    
    print(f"   {'✅ PASSED' if passed else '❌ FAILED'}")
    print(f"   Chunks in Qdrant: {found_in_qdrant}/{len(chunk_ids)}")
    if missing_in_qdrant:
        print(f"   ⚠️  Missing: {len(missing_in_qdrant)}")
    
    return result

# ============================================================
# TEST 3: DRIFT OVER TIME
# ============================================================

def test_drift_analysis(days: int = 7) -> Dict:
    """
    Test: Growth rate analysis
    
    Checks:
    - Node growth rate (should flatten)
    - Relation growth rate (should grow slower than nodes)
    - Chunk count stability
    
    Returns:
        {
            "passed": bool,
            "analysis": {
                "nodes_per_day": float,
                "relations_per_day": float,
                "chunks_per_day": float,
                "growth_trend": "stable" | "explosive" | "declining"
            }
        }
    """
    print(f"\n🔍 Test 3: Drift Analysis (last {days} days)")
    
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    with neo4j_driver.session() as session:
        # Count nodes
        result = session.run("MATCH (n) RETURN count(n) AS total_nodes")
        total_nodes = result.single()["total_nodes"]
        
        # Count relations
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS total_relations")
        total_relations = result.single()["total_relations"]
        
        # Count concepts
        result = session.run("MATCH (c:Concept) RETURN count(c) AS total_concepts")
        total_concepts = result.single()["total_concepts"]
    
    neo4j_driver.close()
    
    # Count Qdrant points
    collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
    total_chunks = collection_info.points_count
    
    # Calculate per-day rates (rough estimate)
    nodes_per_day = total_nodes / days
    relations_per_day = total_relations / days
    chunks_per_day = total_chunks / days
    
    # Determine trend
    relation_node_ratio = total_relations / max(total_nodes, 1)
    
    if relation_node_ratio > 3.0:
        trend = "explosive"  # Too many relations
        passed = False
    elif relation_node_ratio < 0.5:
        trend = "sparse"  # Too few relations
        passed = False
    else:
        trend = "stable"
        passed = True
    
    result = {
        "test": "drift_analysis",
        "passed": passed,
        "totals": {
            "nodes": total_nodes,
            "relations": total_relations,
            "concepts": total_concepts,
            "chunks": total_chunks
        },
        "rates": {
            "nodes_per_day": round(nodes_per_day, 2),
            "relations_per_day": round(relations_per_day, 2),
            "chunks_per_day": round(chunks_per_day, 2)
        },
        "analysis": {
            "relation_node_ratio": round(relation_node_ratio, 2),
            "growth_trend": trend
        }
    }
    
    print(f"   {'✅ PASSED' if passed else '❌ FAILED'}")
    print(f"   Nodes: {total_nodes}, Relations: {total_relations}, Chunks: {total_chunks}")
    print(f"   Relation/Node ratio: {relation_node_ratio:.2f} ({trend})")
    
    return result

# ============================================================
# TEST 4: HUMAN CHECKPOINT
# ============================================================

def test_human_checkpoint(sample_size: int = 5) -> Dict:
    """
    Test: Manual verification helpers
    
    Provides random samples for human review:
    - Random Qdrant chunks
    - Random Neo4j concepts
    - Random relations
    
    Returns:
        {
            "samples": {
                "qdrant_chunks": List[Dict],
                "neo4j_concepts": List[Dict],
                "relations": List[Dict]
            }
        }
    """
    print(f"\n🔍 Test 4: Human Checkpoint (sample={sample_size})")
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Sample Qdrant chunks
    points, _ = qdrant_client.scroll(
        collection_name=QDRANT_COLLECTION,
        limit=sample_size,
        with_payload=True,
        with_vectors=False
    )
    
    qdrant_samples = []
    for p in points:
        qdrant_samples.append({
            "id": str(p.id),
            "text": p.payload.get("text", "")[:100] + "...",
            "source": p.payload.get("source", "unknown")
        })
    
    # Sample Neo4j concepts
    with neo4j_driver.session() as session:
        result = session.run(f"""
            MATCH (c:Concept)
            OPTIONAL MATCH (c)<-[r:RELATED_TO]-(:Chunk)
            WITH c, count(r) AS mention_count
            RETURN c.name AS name, 
                   c.type AS type,
                   mention_count
            ORDER BY rand()
            LIMIT {sample_size}
        """)
        
        concept_samples = []
        for record in result:
            concept_samples.append({
                "name": record["name"],
                "type": record["type"],
                "mentions": record["mention_count"]
            })
        
        # Sample relations
        result = session.run(f"""
            MATCH (a)-[r:RELATED_TO]->(b)
            RETURN labels(a)[0] AS from_type,
                   COALESCE(a.id, a.name, elementId(a)) AS from_id,
                   type(r) AS rel_type,
                   COALESCE(b.name, b.id, elementId(b)) AS to_name
            ORDER BY rand()
            LIMIT {sample_size}
        """)
        
        relation_samples = []
        for record in result:
            relation_samples.append({
                "from": f"{record['from_type']}:{record['from_id'][:20]}...",
                "relation": record["rel_type"],
                "to": record["to_name"]
            })
    
    neo4j_driver.close()
    
    result = {
        "test": "human_checkpoint",
        "samples": {
            "qdrant_chunks": qdrant_samples,
            "neo4j_concepts": concept_samples,
            "relations": relation_samples
        }
    }
    
    print(f"   ✅ Samples ready for human review")
    print(f"\n   📋 Qdrant chunks:")
    for s in qdrant_samples:
        print(f"      - {s['source']}: {s['text'][:60]}...")
    
    print(f"\n   📋 Neo4j concepts:")
    for s in concept_samples:
        print(f"      - {s['name']} ({s['type']}) - {s['mentions']} mentions")
    
    print(f"\n   📋 Relations:")
    for s in relation_samples:
        print(f"      - {s['from']} -[{s['relation']}]-> {s['to']}")
    
    return result

# ============================================================
# MAIN
# ============================================================

def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("🧪 VALIDATOR - Full Sync Validation")
    print("="*60)
    
    results = []
    
    # Test 1: Semantic Roundtrip
    results.append(test_semantic_roundtrip())
    
    # Test 2: Graph Mirror
    results.append(test_graph_mirror())
    
    # Test 3: Drift Analysis
    results.append(test_drift_analysis())
    
    # Test 4: Human Checkpoint
    results.append(test_human_checkpoint())
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len([r for r in results if "passed" in r])
    
    for result in results:
        test_name = result["test"]
        passed = result.get("passed", "N/A")
        status = "✅ PASSED" if passed is True else "❌ FAILED" if passed is False else "ℹ️  INFO"
        print(f"   {status} - {test_name}")
    
    print(f"\n   Overall: {passed_count}/{total_count} tests passed")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validator - Sync validation")
    parser.add_argument("--test", choices=["semantic-roundtrip", "graph-mirror", "drift", "human", "all"], default="all")
    
    args = parser.parse_args()
    
    if args.test == "all":
        run_all_tests()
    elif args.test == "semantic-roundtrip":
        result = test_semantic_roundtrip()
        print(json.dumps(result, indent=2))
    elif args.test == "graph-mirror":
        result = test_graph_mirror()
        print(json.dumps(result, indent=2))
    elif args.test == "drift":
        result = test_drift_analysis()
        print(json.dumps(result, indent=2))
    elif args.test == "human":
        result = test_human_checkpoint()
        print(json.dumps(result, indent=2))
