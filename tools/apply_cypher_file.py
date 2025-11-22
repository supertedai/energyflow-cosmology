#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        database=NEO4J_DATABASE,
    )


def main():
    cypher_path = Path("cypher/seed.cypher")
    if not cypher_path.exists():
        print(f"[apply] Ingen fil: {cypher_path}")
        return

    query = cypher_path.read_text(encoding="utf-8")

    driver = get_driver()
    with driver.session() as session:
        print("[apply] Kjører seed…")
        session.run(query)

    print("[apply] Ferdig.")


if __name__ == "__main__":
    main()
