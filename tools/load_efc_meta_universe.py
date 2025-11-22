#!/usr/bin/env python3
import json
from neo4j import GraphDatabase
from pathlib import Path

URI = "neo4j+s://<your-instance>"
AUTH = ("neo4j", "<password>")

driver = GraphDatabase.driver(URI, auth=AUTH)


def load_jsonld(path):
    with open(path) as f:
        return json.load(f)


def upsert_node(tx, label, props):
    fields = ", ".join([f"{k}: ${k}" for k in props])
    q = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += {{{fields}}}
    """
    tx.run(q, **props)


def upsert_rel(tx, start_id, rel, end_id):
    q = f"""
        MATCH (a {{id:$start}}), (b {{id:$end}})
        MERGE (a)-[:{rel}]->(b)
    """
    tx.run(q, start=start_id, end=end_id)


def process_entries(data):
    entries = data["@graph"]

    for entry in entries:
        label = entry["@type"].split(":")[-1]
        props = {k: v for k, v in entry.items() if not k.startswith("@")}

        with driver.session() as s:
            s.write_transaction(upsert_node, label, props)

        for rel in ["influences", "shapes", "drives"]:
            if rel in entry:
                with driver.session() as s:
                    s.write_transaction(
                        upsert_rel,
                        props["id"],
                        rel,
                        entry[rel],
                    )


if __name__ == "__main__":
    jsonld_path = Path("schema/efc_meta_universe.jsonld")
    data = load_jsonld(jsonld_path)
    process_entries(data)
    print("EFC metalag + universlag importert.")
