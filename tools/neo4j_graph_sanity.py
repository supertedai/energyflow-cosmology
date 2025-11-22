#!/usr/bin/env python3
from neo4j import GraphDatabase
import os, sys

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def q(tx, s):
    return [r.data() for r in tx.run(s)]


def check(label, rel):
    with driver.session() as s:
        # Nodetell
        n = s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]

        # Orphans? (noder uten inn/ut-rel)
        o = s.run(f"""
            MATCH (n:{label})
            WHERE NOT (n)--()
            RETURN count(n) AS c
        """).single()["c"]

        # Relasjonsintegritet
        r = s.run(f"""
            MATCH (:{label})-[x:{rel}]->()
            RETURN count(x) AS c
        """).single()["c"]

    return {
        "label": label,
        "nodes": n,
        "orphans": o,
        "relations": r,
    }


def main():
    checks = [
        ("EnergyFlow", "creates_gradient"),
        ("EntropyGradient", "drives"),
        ("CosmicDynamics", "forms"),
        ("Observation", "measures"),
        ("Insight", "influences"),
        ("MetaPattern", "shapes"),
        ("CognitiveMechanism", "drives"),
        ("ResearchStep", "produces")
    ]

    results = [check(l, r) for l, r in checks]
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
