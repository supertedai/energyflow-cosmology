#!/usr/bin/env python3
"""
Bygger relasjoner:
(:EFCPaper)-[:ADDRESSES]->(:MetaNode)

Mapping hentes fra paper_meta_map.json.
"""

import os
import json
from pathlib import Path
from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / "paper_meta_map.json"

def get_driver():
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))

def main():
    if not MAP_PATH.exists():
        print("[PaperRelations] Fant ikke paper_meta_map.json")
        return

    mapping = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    driver = get_driver()
    with driver.session() as session:
        for paper_slug, meta_list in mapping.items():
            p_id = paper_slug.lower()

            for meta_label in meta_list:
                m_id = meta_label.lower()

                session.run(
                    """
                    MATCH (p:EFCPaper {id: $pid})
                    MATCH (m:MetaNode {id: $mid})
                    MERGE (p)-[:ADDRESSES]->(m)
                    """,
                    pid=p_id,
                    mid=m_id
                )

    print("[PaperRelations] FULLFØRT: Paper → MetaNode-relasjoner")

if __name__ == "__main__":
    main()
