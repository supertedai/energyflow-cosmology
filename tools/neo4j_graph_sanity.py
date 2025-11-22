#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )


def main():
    driver = get_driver()
    checks = [
        "MATCH (p:EFCPaper) RETURN p.slug LIMIT 1",
        "MATCH (m:MetaNode) RETURN m.name LIMIT 1",
        "MATCH ()-[r:ADDRESSES]->() RETURN r LIMIT 1",
    ]

    with driver.session() as session:
        for q in checks:
            try:
                session.run(q).data()
                print(f"[OK] {q[:40]}...")
            except Exception as e:
                print(f"[FAIL] {q}\n{e}")


if __name__ == "__main__":
    main()
