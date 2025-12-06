#!/usr/bin/env python3
"""Quick test: Ingest 5 filer med node_id"""

from tools.rag_ingest_repo import *

def main():
    log("🧪 Test-ingest med node_id bridge\n")
    
    # Test paths
    test_files = [
        ROOT / "theory/formal/README.md",
        ROOT / "docs/README.md", 
        ROOT / "meta/README.md",
    ]
    
    client = get_qdrant_client()
    neo4j_driver = get_neo4j_driver()
    
    for path in test_files:
        if path.exists():
            chunks = ingest_file(path, client, QDRANT_COLLECTION, neo4j_driver)
            log(f"  ✅ {chunks} chunks")
    
    if neo4j_driver:
        neo4j_driver.close()
    
    log("\n✅ Test complete")

if __name__ == "__main__":
    main()
