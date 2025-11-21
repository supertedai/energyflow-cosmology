#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEO4J DOI SYNC — EFCPaper
=========================

Leser alle docs/papers/efc/<slug>/metadata.json
og oppdaterer (:EFCPaper {slug}) med .doi.

Bruk:
- NEO4J_URI
- NEO4J_USER eller NEO4J_USERNAME
- NEO4J_PASSWORD
- NEO4J_DATABASE (default "neo4j")
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = ROOT / "docs" / "papers" / "efc"


def log(msg: str) -> None:
    print(f"[neo4j-doi-sync] {msg}", flush=True)


def get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME") or os.environ.get("NEO4J_USER")
    pwd = os.environ.get("NEO4J_PASSWORD")
    db = os.environ.get("NEO4J_DATABASE", "neo4j")

    if not uri:
        raise RuntimeError("NEO4J_URI mangler")
    if not user:
        raise RuntimeError("NEO4J_USERNAME/NEO4J_USER mangler")
    if not pwd:
        raise RuntimeError("NEO4J_PASSWORD mangler")

    log(f"Kobler til Neo4j @ {uri} (db={db})")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    with driver.session(database=db) as session:
        ok = session.run("RETURN 1 AS ok").single()["ok"]
        if ok != 1:
            raise RuntimeError("Neo4j test-tilkobling feilet")

    log("Neo4j-tilkobling OK.")
    return driver, db


def load_metadata() -> List[Dict[str, Any]]:
    if not PAPERS_ROOT.exists():
        log(f"Fant ikke {PAPERS_ROOT}")
        return []

    rows: List[Dict[str, Any]] = []
    for paper_dir in sorted(p for p in PAPERS_ROOT.iterdir() if p.is_dir()):
        slug = paper_dir.name
        meta_path = paper_dir / "metadata.json"
        if not meta_path.exists():
            log(f"[{slug}] Ingen metadata.json – hopper.")
            continue
        try:
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as e:
            log(f"[{slug}] Kunne ikke lese metadata.json: {e}")
            continue

        doi = meta.get("doi")
        title = meta.get("title")
        if not doi:
            log(f"[{slug}] Ingen DOI i metadata, hopper.")
            continue

        rows.append({"slug": slug, "doi": doi, "title": title})

    log(f"Fant {len(rows)} papere med DOI i metadata.")
    return rows


def sync_to_neo4j(driver, db: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        log("Ingen rader å sync’e.")
        return

    def _tx(tx, batch):
        tx.run(
            """
            UNWIND $rows AS row
            MERGE (p:EFCPaper {slug: row.slug})
              ON CREATE SET
                p.title = coalesce(row.title, p.title),
                p.doi   = row.doi
              ON MATCH SET
                p.doi   = row.doi
            """,
            rows=batch,
        )

    batch_size = 100
    total = len(rows)

    with driver.session(database=db) as session:
        for i in range(0, total, batch_size):
            batch = rows[i : i + batch_size]
            session.execute_write(_tx, batch=batch)
            log(f"Synced {min(i + batch_size, total)} / {total} EFCPaper-DOIs.")

    log("EFCPaper DOI-sync ferdig.")


def main() -> None:
    log("Starter Neo4j DOI-sync (EFCPaper)...")
    rows = load_metadata()
    driver, db = get_neo4j_driver()
    sync_to_neo4j(driver, db, rows)
    log("Neo4j DOI-sync fullført.")


if __name__ == "__main__":
    main()
