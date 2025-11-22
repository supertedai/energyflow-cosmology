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

    queries = {
        "nodes": "MATCH (n) RETURN count(n) AS c",
        "relationships": "MATCH ()-[r]->() RETURN count(r) AS c",
        "papers": "MATCH (p:EFCPaper) RETURN count(p) AS c",
        "metanodes": "MATCH (m:MetaNode) RETURN count(m) AS c"
    }

    with driver.session() as session:
        for label, q in queries.items():
            res = session.run(q).data()[0]["c"]
            print(f"{label}: {res}")


if __name__ == "__main__":
    main()
