#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

PAPER_DIR = Path("docs/papers/efc")


def flatten(d, parent_key="", sep="_"):
    """Flatten nested dicts for Neo4j compatibility."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.update(flatten(v, new_key, sep=sep))
        else:
            # Neo4j only accepts primitives or lists
            if isinstance(v, list):
                # ensure list elements are primitives
                v = [
                    str(e) if isinstance(e, dict) else e
                    for e in v
                ]
            items[new_key] = v
    return items


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )


def main():
    driver = get_driver()

    entries = PAPER_DIR.glob("*/metadata.json")

    with driver.session(database=NEO4J_DATABASE) as session:
        for meta in entries:
            d = json.loads(meta.read_text())

            # flatten metadata before sending to Neo4j
            flat = flatten(d)

            session.run(
                """
                MERGE (p:EFCPaper {slug: $slug})
                SET p += $props
                """,
                slug=d["slug"],
                props=flat,
            )
            print(f"[paper] {meta} importert.")


if __name__ == "__main__":
    main()
