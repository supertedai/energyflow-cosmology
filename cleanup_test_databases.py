#!/usr/bin/env python3
"""
Database Cleanup Script
Removes test collections and validates production data.

SAFE MODE: Only removes collections starting with 'test_'
Production collections preserved: canonical_facts, semantic_mesh, efc
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

load_dotenv()

def cleanup_qdrant():
    """Remove test collections from Qdrant."""
    client = QdrantClient(
        url=os.getenv('QDRANT_URL'),
        api_key=os.getenv('QDRANT_API_KEY')
    )
    
    # Get all collections
    collections = client.get_collections().collections
    
    # Production collections - DO NOT DELETE
    production = {'canonical_facts', 'semantic_mesh', 'efc'}
    
    print("🔍 Qdrant Collections:")
    print("=" * 60)
    
    test_collections = []
    for col in collections:
        info = client.get_collection(col.name)
        is_test = col.name.startswith('test_')
        is_prod = col.name in production
        
        status = "🟢 KEEP (production)" if is_prod else "🔴 DELETE (test)" if is_test else "⚠️  REVIEW (unknown)"
        print(f"{status:30} {col.name:40} {info.points_count:>6} vectors")
        
        if is_test:
            test_collections.append(col.name)
    
    print("\n" + "=" * 60)
    print(f"Found {len(test_collections)} test collections to delete")
    
    if test_collections:
        confirm = input("\n⚠️  Delete test collections? (yes/no): ")
        if confirm.lower() == 'yes':
            for col_name in test_collections:
                client.delete_collection(col_name)
                print(f"✅ Deleted: {col_name}")
            print(f"\n🎉 Cleaned {len(test_collections)} test collections")
        else:
            print("❌ Cancelled")
    else:
        print("✅ No test collections found")

def review_neo4j():
    """Review Neo4j nodes - DO NOT DELETE (just report)."""
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), 'N-HPl8pKFVwsMgCzydGI26dsgJAMOP1ss6r1NhiHNjs')
    )
    
    with driver.session() as session:
        print("\n🔍 Neo4j Node Distribution:")
        print("=" * 60)
        
        # Count by label
        result = session.run('''
            MATCH (n) 
            RETURN labels(n) as labels, count(n) as count 
            ORDER BY count DESC
        ''')
        
        production_count = 0
        private_count = 0
        
        for record in result:
            labels = record['labels']
            count = record['count']
            
            is_private = any('Private' in label for label in labels)
            status = "⚠️  Private" if is_private else "🟢 Production"
            
            print(f"{status:20} {str(labels):50} {count:>6}")
            
            if is_private:
                private_count += count
            else:
                production_count += count
        
        print("=" * 60)
        print(f"Production nodes: {production_count}")
        print(f"Private nodes: {private_count}")
        print(f"TOTAL: {production_count + private_count}")
        
        print("\n⚠️  Neo4j cleanup must be done manually if needed")
        print("   Consider: MATCH (n:PrivateDocument) DETACH DELETE n")
    
    driver.close()

def main():
    """Run cleanup with safety checks."""
    print("🧹 Database Cleanup Script")
    print("=" * 60)
    print("This will:")
    print("  ✓ Delete Qdrant collections starting with 'test_'")
    print("  ✓ Preserve: canonical_facts, semantic_mesh, efc")
    print("  ✓ Review Neo4j (no deletion)")
    print("=" * 60)
    print()
    
    # Qdrant cleanup
    cleanup_qdrant()
    
    # Neo4j review
    review_neo4j()
    
    print("\n" + "=" * 60)
    print("🎉 Cleanup complete!")

if __name__ == "__main__":
    main()
