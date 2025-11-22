#!/usr/bin/env python3
import json
import os
from neo4j import GraphDatabase
from pathlib import Path

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_URI og NEO4J_PASSWORD må være satt i miljøvariabler")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def load_jsonld(path: Path):
    with path.open() as f:
        return json.load(f)


def upsert_node(tx, label, props):
    rel_keys = {"influences", "shapes", "drives"}
    clean_props = {k: v for k, v in props.items() if k not in rel_keys}

    if "id" not in clean_props:
        return

    fields = ", ".join([f"{k}: ${k}" for k in clean_props if k != "id"])

    if fields:
        q = f"""
            MERGE (n:{label} {{id: $id}})
            SET n += {{{fields}}}
        """
    else:
        q = f"MERGE (n:{label} {{id: $id}})"

    tx.run(q, **clean_props)


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
            s.execute_write(upsert_node, label, props)

        for rel in ["influences", "shapes", "drives"]:
            if rel in entry:
                with driver.session() as s:
                    s.execute_write(
                        upsert_rel,
                        props["id"],
                        rel,
                        entry[rel],
                    )


def main():
    jsonld_path = Path("schema/efc_meta_universe.jsonld")
    if not jsonld_path.exists():
        raise FileNotFoundError(f"Fant ikke {jsonld_path}")

    data = load_jsonld(jsonld_path)
    process_entries(data)
    print("[efc_meta_universe] Importert meta-universlag til Neo4j.")


if __name__ == "__main__":
    main()
