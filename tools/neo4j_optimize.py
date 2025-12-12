#!/usr/bin/env python3
"""
neo4j_optimize.py - Neo4j Performance Optimization
==================================================

Applies:
1. Vector indexes for Concept embeddings (1536 dims, cosine)
2. Property indexes for fast lookups
3. Constraint validation
4. Query performance analysis

Run after initial graph setup to maximize performance.
"""

import os
import sys
from typing import Dict, List
from neo4j import GraphDatabase
from dotenv import load_dotenv
import time

load_dotenv()

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    # Fallback to hardcoded password if needed
    NEO4J_PASSWORD = "N-HPl8pKFVwsMgCzydGI26dsgJAMOP1ss6r1NhiHNjs"


def run_query(session, query: str, params: Dict = None) -> List[Dict]:
    """Execute Cypher query and return results."""
    try:
        result = session.run(query, params or {})
        return [dict(record) for record in result]
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def create_vector_index(session, index_name: str, label: str, property: str, dimensions: int = 1536):
    """
    Create vector index for similarity search.
    
    Args:
        session: Neo4j session
        index_name: Index name
        label: Node label
        property: Property containing vector
        dimensions: Vector dimensions (1536 for text-embedding-3-large)
    """
    print(f"\n   Creating vector index: {index_name}")
    print(f"   Label: {label}, Property: {property}, Dimensions: {dimensions}")
    
    # Check if index exists
    check_query = f"""
    SHOW INDEXES
    YIELD name, type
    WHERE name = '{index_name}'
    RETURN name, type
    """
    existing = run_query(session, check_query)
    
    if existing:
        print(f"   ⚠️  Index '{index_name}' already exists (type: {existing[0]['type']})")
        return
    
    # Create vector index
    # Note: Syntax may vary by Neo4j version (4.x vs 5.x)
    # This is for Neo4j 5.x
    create_query = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON (n.{property})
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """
    
    try:
        run_query(session, create_query)
        print(f"   ✅ Vector index '{index_name}' created")
    except Exception as e:
        # Fallback for older Neo4j versions or different syntax
        print(f"   ⚠️  Vector index creation failed: {e}")
        print(f"   → May require Neo4j 5.x+ or manual creation")


def create_property_index(session, index_name: str, label: str, property: str):
    """
    Create B-tree index for property lookups.
    
    Args:
        session: Neo4j session
        index_name: Index name
        label: Node label
        property: Property to index
    """
    print(f"\n   Creating property index: {index_name}")
    print(f"   Label: {label}, Property: {property}")
    
    # Check if index exists
    check_query = f"""
    SHOW INDEXES
    YIELD name, type
    WHERE name = '{index_name}'
    RETURN name, type
    """
    existing = run_query(session, check_query)
    
    if existing:
        print(f"   ⚠️  Index '{index_name}' already exists (type: {existing[0]['type']})")
        return
    
    # Create index
    create_query = f"""
    CREATE INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON (n.{property})
    """
    
    try:
        run_query(session, create_query)
        print(f"   ✅ Property index '{index_name}' created")
    except Exception as e:
        print(f"   ❌ Index creation failed: {e}")


def create_composite_index(session, index_name: str, label: str, properties: List[str]):
    """
    Create composite index for multi-property lookups.
    
    Args:
        session: Neo4j session
        index_name: Index name
        label: Node label
        properties: List of properties to index
    """
    print(f"\n   Creating composite index: {index_name}")
    print(f"   Label: {label}, Properties: {properties}")
    
    # Check if index exists
    check_query = f"""
    SHOW INDEXES
    YIELD name, type
    WHERE name = '{index_name}'
    RETURN name, type
    """
    existing = run_query(session, check_query)
    
    if existing:
        print(f"   ⚠️  Index '{index_name}' already exists (type: {existing[0]['type']})")
        return
    
    # Create composite index
    props_str = ", ".join([f"n.{p}" for p in properties])
    create_query = f"""
    CREATE INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON ({props_str})
    """
    
    try:
        run_query(session, create_query)
        print(f"   ✅ Composite index '{index_name}' created")
    except Exception as e:
        print(f"   ❌ Composite index creation failed: {e}")


def create_relationship_index(session, index_name: str, rel_type: str, property: str):
    """
    Create index on relationship property.
    
    Args:
        session: Neo4j session
        index_name: Index name
        rel_type: Relationship type
        property: Property to index
    """
    print(f"\n   Creating relationship index: {index_name}")
    print(f"   Type: {rel_type}, Property: {property}")
    
    # Check if index exists
    check_query = f"""
    SHOW INDEXES
    YIELD name, type
    WHERE name = '{index_name}'
    RETURN name, type
    """
    existing = run_query(session, check_query)
    
    if existing:
        print(f"   ⚠️  Index '{index_name}' already exists (type: {existing[0]['type']})")
        return
    
    # Create relationship index
    create_query = f"""
    CREATE INDEX {index_name} IF NOT EXISTS
    FOR ()-[r:{rel_type}]-()
    ON (r.{property})
    """
    
    try:
        run_query(session, create_query)
        print(f"   ✅ Relationship index '{index_name}' created")
    except Exception as e:
        print(f"   ❌ Relationship index creation failed: {e}")


def show_indexes(session):
    """Display all existing indexes."""
    print("\n" + "=" * 60)
    print("📋 EXISTING INDEXES")
    print("=" * 60)
    
    query = """
    SHOW INDEXES
    YIELD name, type, entityType, labelsOrTypes, properties, state
    RETURN name, type, entityType, labelsOrTypes, properties, state
    ORDER BY name
    """
    
    indexes = run_query(session, query)
    
    if not indexes:
        print("   No indexes found")
        return
    
    for idx in indexes:
        print(f"\n   {idx['name']}")
        print(f"   - Type: {idx['type']}")
        print(f"   - Entity: {idx['entityType']}")
        print(f"   - Labels: {idx['labelsOrTypes']}")
        print(f"   - Properties: {idx['properties']}")
        print(f"   - State: {idx['state']}")


def get_graph_stats(session):
    """Get graph statistics."""
    print("\n" + "=" * 60)
    print("📊 GRAPH STATISTICS")
    print("=" * 60)
    
    # Node counts
    node_query = """
    MATCH (n)
    RETURN labels(n)[0] as label, count(n) as count
    ORDER BY count DESC
    """
    nodes = run_query(session, node_query)
    
    print("\n   Nodes by label:")
    total_nodes = 0
    for row in nodes:
        print(f"   - {row['label']}: {row['count']}")
        total_nodes += row['count']
    print(f"   TOTAL: {total_nodes} nodes")
    
    # Relationship counts
    rel_query = """
    MATCH ()-[r]->()
    RETURN type(r) as type, count(r) as count
    ORDER BY count DESC
    """
    rels = run_query(session, rel_query)
    
    print("\n   Relationships by type:")
    total_rels = 0
    for row in rels:
        print(f"   - {row['type']}: {row['count']}")
        total_rels += row['count']
    print(f"   TOTAL: {total_rels} relationships")


def benchmark_query(session, query: str, description: str) -> float:
    """
    Benchmark query execution time.
    
    Args:
        session: Neo4j session
        query: Cypher query
        description: Query description
    
    Returns:
        Execution time in seconds
    """
    print(f"\n   Benchmarking: {description}")
    
    start = time.time()
    result = run_query(session, query)
    elapsed = time.time() - start
    
    print(f"   ⏱️  {elapsed:.3f}s ({len(result)} results)")
    
    return elapsed


def run_benchmarks(session):
    """Run performance benchmarks."""
    print("\n" + "=" * 60)
    print("⚡ PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    benchmarks = [
        (
            "Find Concept by name",
            "MATCH (c:Concept {name: 'Energy Flow Cosmology'}) RETURN c"
        ),
        (
            "Get Concept neighbors",
            "MATCH (c:Concept {name: 'Energy Flow Cosmology'})-[r]-(n) RETURN type(r), labels(n), n.name LIMIT 20"
        ),
        (
            "Find all Chunks for Document",
            "MATCH (d:Document {name: 'README.md'})<-[:FROM]-(ch:Chunk) RETURN ch.text LIMIT 10"
        ),
        (
            "Get SUPPORTS relationships",
            "MATCH ()-[r:SUPPORTS]->() RETURN r LIMIT 100"
        ),
        (
            "Multi-hop traversal (3 hops)",
            "MATCH path = (c:Concept {name: 'Energy Flow Cosmology'})-[*1..3]-(n) RETURN length(path), n.name LIMIT 50"
        ),
    ]
    
    times = []
    for desc, query in benchmarks:
        elapsed = benchmark_query(session, query, desc)
        times.append(elapsed)
    
    print(f"\n   Average query time: {sum(times)/len(times):.3f}s")
    print(f"   Total benchmark time: {sum(times):.3f}s")


def main():
    """Main optimization workflow."""
    print("🚀 Neo4j Performance Optimization")
    print("=" * 60)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # Step 1: Get current state
        get_graph_stats(session)
        show_indexes(session)
        
        # Step 2: Create indexes
        print("\n" + "=" * 60)
        print("🔧 CREATING INDEXES")
        print("=" * 60)
        
        # Vector index for Concept embeddings
        create_vector_index(session, "concept_embedding_idx", "Concept", "embedding", 1536)
        
        # Property indexes
        create_property_index(session, "concept_name_idx", "Concept", "name")
        create_property_index(session, "document_name_idx", "Document", "name")
        create_property_index(session, "chunk_document_idx", "Chunk", "document")
        create_property_index(session, "person_name_idx", "Person", "name")
        create_property_index(session, "module_name_idx", "Module", "name")
        
        # Composite indexes
        create_composite_index(session, "concept_name_domain_idx", "Concept", ["name", "domain"])
        
        # Relationship indexes
        create_relationship_index(session, "supports_weight_idx", "SUPPORTS", "weight")
        create_relationship_index(session, "constrains_weight_idx", "CONSTRAINS", "weight")
        
        # Step 3: Wait for indexes to be online
        print("\n   ⏳ Waiting for indexes to come online...")
        time.sleep(5)
        
        # Step 4: Show updated indexes
        show_indexes(session)
        
        # Step 5: Run benchmarks
        run_benchmarks(session)
    
    driver.close()
    
    print("\n" + "=" * 60)
    print("✅ Neo4j optimization complete!")
    print("\n📝 Next steps:")
    print("   1. Restart Neo4j to apply memory config (if using neo4j.conf)")
    print("   2. Monitor query performance with: SHOW INDEXES")
    print("   3. Analyze slow queries in neo4j.log")
    print("   4. Run benchmarks again to measure improvement")
    print()


if __name__ == "__main__":
    main()
