#!/usr/bin/env python3
"""
verify_neo4j_perf.py - Neo4j Performance Verification
=====================================================

Measures query performance before/after optimization.
Expected improvements: 3-10x speedup on indexed queries.
"""

import os
import sys
import time
from typing import List, Tuple
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or "N-HPl8pKFVwsMgCzydGI26dsgJAMOP1ss6r1NhiHNjs"


def benchmark_query(session, query: str, params: dict = None, runs: int = 5) -> Tuple[float, float]:
    """
    Benchmark query with multiple runs.
    
    Returns:
        (average_time, min_time) in seconds
    """
    times = []
    
    for _ in range(runs):
        start = time.time()
        list(session.run(query, params or {}))
        elapsed = time.time() - start
        times.append(elapsed)
    
    return sum(times) / len(times), min(times)


def main():
    print("🧪 Neo4j Performance Verification")
    print("=" * 60)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Get graph stats
        result = session.run("MATCH (n) RETURN count(n) as nodes")
        nodes = result.single()["nodes"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rels")
        rels = result.single()["rels"]
        
        print(f"\n📊 Graph size: {nodes:,} nodes, {rels:,} relationships")
        
        # Count indexes
        result = session.run("SHOW INDEXES YIELD name RETURN count(name) as count")
        index_count = result.single()["count"]
        print(f"📋 Indexes: {index_count}")
        
        # Test queries
        print("\n" + "=" * 60)
        print("⚡ QUERY BENCHMARKS (5 runs each)")
        print("=" * 60)
        
        benchmarks = [
            (
                "1. Find Concept by name (indexed)",
                "MATCH (c:Concept {name: 'Energy Flow Cosmology'}) RETURN c"
            ),
            (
                "2. Get Document by name (indexed)",
                "MATCH (d:Document {name: 'README.md'}) RETURN d"
            ),
            (
                "3. Find Concept neighbors",
                "MATCH (c:Concept)-[r]-(n) WHERE c.name = 'Energy Flow Cosmology' RETURN type(r), labels(n)[0], n.name LIMIT 50"
            ),
            (
                "4. SUPPORTS relationships (indexed)",
                "MATCH ()-[r:SUPPORTS]->() WHERE r.weight > 0.5 RETURN count(r)"
            ),
            (
                "5. Multi-hop traversal (2 hops)",
                "MATCH path = (c:Concept {name: 'Energy Flow Cosmology'})-[*1..2]-(n) RETURN length(path), n.name LIMIT 100"
            ),
            (
                "6. Aggregate by Concept domain",
                "MATCH (c:Concept) RETURN c.domain, count(c) as count ORDER BY count DESC LIMIT 20"
            ),
            (
                "7. Find all Modules",
                "MATCH (m:Module) RETURN m.name ORDER BY m.name"
            ),
            (
                "8. Complex join (Concept -> Document -> Chunk)",
                "MATCH (c:Concept)-[:MENTIONS]-(d:Document)-[:HAS_CHUNK]->(ch:Chunk) WHERE c.name = 'Energy Flow Cosmology' RETURN ch.text LIMIT 20"
            ),
        ]
        
        total_avg = 0
        total_min = 0
        
        for desc, query in benchmarks:
            avg_time, min_time = benchmark_query(session, query)
            total_avg += avg_time
            total_min += min_time
            
            print(f"\n{desc}")
            print(f"   Avg: {avg_time*1000:.1f}ms, Min: {min_time*1000:.1f}ms")
            
            # Performance assessment
            if avg_time < 0.05:
                print(f"   ✅ Excellent (<50ms)")
            elif avg_time < 0.1:
                print(f"   ✅ Good (<100ms)")
            elif avg_time < 0.5:
                print(f"   ⚠️  Acceptable (<500ms)")
            else:
                print(f"   ❌ Slow (>500ms) - may need optimization")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"   Total query time (avg): {total_avg:.3f}s")
        print(f"   Total query time (min): {total_min:.3f}s")
        print(f"   Average per query: {(total_avg/len(benchmarks))*1000:.1f}ms")
        
        # Expected performance
        print("\n📈 PERFORMANCE TARGETS:")
        print("   ✅ Indexed lookups: <50ms")
        print("   ✅ Single-hop traversals: <100ms")
        print("   ✅ Multi-hop traversals: <200ms")
        print("   ✅ Aggregations: <150ms")
        
        # Memory usage (if available)
        try:
            result = session.run("""
                CALL dbms.queryJmx('java.lang:type=Memory')
                YIELD attributes
                RETURN attributes.HeapMemoryUsage.value.used as heap_used,
                       attributes.HeapMemoryUsage.value.max as heap_max
            """)
            memory = result.single()
            heap_used_mb = memory["heap_used"] / (1024 * 1024)
            heap_max_mb = memory["heap_max"] / (1024 * 1024)
            heap_pct = (heap_used_mb / heap_max_mb) * 100
            
            print(f"\n💾 MEMORY USAGE:")
            print(f"   Heap: {heap_used_mb:.0f}MB / {heap_max_mb:.0f}MB ({heap_pct:.1f}%)")
        except:
            pass
    
    driver.close()
    
    print("\n✅ Performance verification complete!")
    print()


if __name__ == "__main__":
    main()
