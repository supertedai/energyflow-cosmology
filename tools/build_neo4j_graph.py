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

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "graph" / "nodes"


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )


def merge_node(tx, label, props):
    fields = ", ".join([f"{k}: ${k}" for k in props.keys()])
    tx.run(f"MERGE (n:{label} {{id: $id}}) SET n += {{{fields}}}", **props)


def main():
    driver = get_driver()
    json_files = list(DATA_DIR.glob("*.json"))

    with driver.session() as session:
        for jf in json_files:
            data = json.loads(jf.read_text())
            merge_node(session, data["label"], data["properties"])
            print(f"[graph] {jf.name} importert.")

    print("[graph] Ferdig.")


if __name__ == "__main__":
    main()
