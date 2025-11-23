#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from neo4j import GraphDatabase
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "semantic-index.json"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def push_item(tx, item):
    tx.run(
        """
        MERGE (n:EFCDoc {slug: $slug})
        SET n.title = $title,
            n.description = $description,
            n.file = $file,
            n.updated = timestamp()
        """,
        slug=item["slug"],
        title=item["title"],
        description=item["description"],
        file=item["file"],
    )


def main():
    items = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

    with driver.session(database=NEO4J_DATABASE) as session:
        for item in items:
            session.execute_write(push_item, item)

    print(f"[neo4j] Pushed {len(items)} documents to Neo4j")


if __name__ == "__main__":
    main()
