#!/usr/bin/env python3
import os
from neo4j import GraphDatabase
from pathlib import Path

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_URI og NEO4J_PASSWORD må være satt i miljøvariabler")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def run_cypher_file(path: Path):
    text = path.read_text(encoding="utf-8")
    statements = [s.strip() for s in text.split(";") if s.strip()]

    with driver.session() as session:
        for stmt in statements:
            print(f"[apply_cypher_file] Kjører statement:\n{stmt[:120]}...")
            session.run(stmt)

    print(f"[apply_cypher_file] Ferdig: {len(statements)} statements fra {path}")


def main():
    cypher_files = [
        "neo4j/efc_schema.cypher",
        "neo4j/efc_seed_concepts.cypher",
        "neo4j/efc_papers.cypher",
        "neo4j/efc_universe_and_meta.cypher"
    ]

    for file_path in cypher_files:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Cypher-fil mangler: {path}")
        run_cypher_file(path)


if __name__ == "__main__":
    main()
