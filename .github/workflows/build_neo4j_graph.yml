#!/usr/bin/env python3

import os
from neo4j import GraphDatabase
import json

# Load credentials from environment variables
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USER = os.environ["NEO4J_USER"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def ingest_nodes(tx, nodes):
    for node in nodes:
        tx.run(
            """
            MERGE (n:Node {id: $id})
            SET n += $props
            """,
            id=node["id"],
            props=node
        )

def ingest_edges(tx, edges):
    for edge in edges:
        tx.run(
            """
            MATCH (a:Node {id: $src})
            MATCH (b:Node {id: $dst})
            MERGE (a)-[r:LINK {type: $type}]->(b)
            """,
            src=edge["source"],
            dst=edge["target"],
            type=edge["type"]
        )

def main():
    print("[Neo4j] Loading semantic graph JSON...")
    data = load_json("meta-graph/meta-graph.jsonld")

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    print(f"[Neo4j] Ingesting {len(nodes)} nodes and {len(edges)} edges")

    with driver.session() as session:
        session.execute_write(ingest_nodes, nodes)
        session.execute_write(ingest_edges, edges)

    print("[Neo4j] Ingestion complete.")

if __name__ == "__main__":
    main()
