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


def flatten_nested_props(meta: dict) -> dict:
    """
    Neo4j kan kun lagre primitive typer:
    - string
    - number
    - boolean
    - list av disse

    Denne funksjonen:
      * finner alle nested dicts
      * serialiserer dem til JSON-string
      * lager nye felt: "<key>_json"
      * fjerner originalen
    """
    flat = meta.copy()

    for key, value in list(flat.items()):
        if isinstance(value, dict):
            flat[f"{key}_json"] = json.dumps(value)
            del flat[key]

    return flat


def main():
    driver = get_driver()
    entries = PAPER_DIR.glob("*/metadata.json")

    with driver.session() as session:
        for meta_file in entries:
            raw = json.loads(meta_file.read_text())
            props = flatten_nested_props(raw)

            session.run(
                """
                MERGE (p:EFCPaper {slug: $slug})
                SET p += $props
                """,
                slug=raw["slug"],
                props=props,
            )

            print(f"[paper] {meta_file} importert.")


if __name__ == "__main__":
    main()
