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


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )


def main():
    driver = get_driver()

    entries = PAPER_DIR.glob("*/metadata.json")

    with driver.session() as session:
        for meta in entries:
            d = json.loads(meta.read_text())
            session.run(
                """
                MERGE (p:EFCPaper {slug: $slug})
                SET p += $props
                """,
                slug=d["slug"],
                props=d,
            )
            print(f"[paper] {meta} importert.")


if __name__ == "__main__":
    main()
