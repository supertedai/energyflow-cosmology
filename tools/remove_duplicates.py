#!/usr/bin/env python3
"""
Remove duplicate documents from Neo4j
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

print("🗑️  Removing duplicate documents...")
print()

with driver.session() as session:
    # Keep oldest, delete rest
    result = session.run("""
        MATCH (d:Document)
        WITH d.source as source, collect(d) as docs
        WHERE size(docs) > 1
        WITH source, size(docs) as count, docs[0] as keep, docs[1..] as delete_list
        UNWIND delete_list as to_delete
        OPTIONAL MATCH (to_delete)-[:HAS_CHUNK]->(ch:Chunk)
        DETACH DELETE to_delete, ch
        RETURN source, count, count(DISTINCT to_delete) as deleted
    """)
    
    total_deleted = 0
    for record in result:
        source = record["source"]
        original_count = record["count"]
        deleted = record["deleted"]
        total_deleted += deleted
        print(f"  {source}: {original_count} copies → kept 1, deleted {deleted}")
    
    print()
    print(f"✅ Removed {total_deleted} duplicate documents")
    print()
    
    # Final count
    docs = session.run("MATCH (d:Document) RETURN count(d) as cnt").single()["cnt"]
    chunks = session.run("MATCH (ch:Chunk) RETURN count(ch) as cnt").single()["cnt"]
    
    print(f"Final counts:")
    print(f"  Documents: {docs}")
    print(f"  Chunks: {chunks}")

driver.close()
