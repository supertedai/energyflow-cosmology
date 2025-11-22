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


def flatten_metadata(meta: dict) -> dict:
    """
    Neo4j kan ikke lagre nested maps.
    Derfor serialiserer vi 'files' til en JSON-string
    og beholder primitive felter slik de er.
    """
    meta = meta.copy()

    # Hvis 'files' finnes → serialiser til string
    if "files" in meta and isinstance(meta["files"], dict):
        meta["files_json"] = json.dumps(meta["files"])
        del meta["files"]  # fjern den gamle (ikke tillatt)

    return meta


def main():
    driver = get_driver()
    entries = PAPER_DIR.glob("*/metadata.json")

    with driver.session() as session:
        for meta_file in entries:
            raw = json.loads(meta_file.read_text())
            props = flatten_metadata(raw)

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
