#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYNC RAG → NEO4J
================

Leser ALLE Qdrant RAG-chunks og speiler dem inn i Neo4j som:

  (:RAGChunk {id, text, chunk_index, slug, doi, path})
    -[:FROM_PAPER]-> (:EFCPaper {slug})
    -[:HAS_KEYWORD]-> (:Keyword {name})

Bruker bare disse secrets i GitHub:

QDRANT_URL
QDRANT_API_KEY
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
NEO4J_DATABASE
"""

import os
from typing import List, Dict, Any, Tuple
from qdrant_client import QdrantClient
from neo4j import GraphDatabase


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

def log(msg: str):
    print(f"[sync-rag-neo4j] {msg}", flush=True)


# ------------------------------------------------------------
# Qdrant helpers
# ------------------------------------------------------------

def get_qdrant_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api = os.environ.get("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("QDRANT_URL mangler i miljøvariabler.")
    if not api:
        raise RuntimeError("QDRANT_API_KEY mangler i miljøvariabler.")

    log(f"Kobler til Qdrant @ {url}")
    client = QdrantClient(url=url, api_key=api)

    # test
    _ = client.get_collections()
    log("Qdrant-tilkobling OK.")

    return client


def scroll_all_points(client: QdrantClient, collection: str) -> List[Tuple[str, Dict[str, Any]]]:
    """Scroller ALLE Qdrant-punkter i batches."""
    points = []
    offset = None

    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            offset=offset,
            limit=256,
            with_payload=True,
            with_vectors=False
        )
        if not batch:
            break

        for pt in batch:
            points.append((str(pt.id), pt.payload or {}))

        if offset is None:
            break

    log(f"Fant totalt {len(points)} points i Qdrant-collection '{collection}'.")
    return points


# ------------------------------------------------------------
# Neo4j helpers
# ------------------------------------------------------------

def get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")            # ← RIKTIG SECRET NAVN
    pwd = os.environ.get("NEO4J_PASSWORD")
    db = os.environ.get("NEO4J_DATABASE", "neo4j")

    if not uri:
        raise RuntimeError("NEO4J_URI mangler i miljøvariabler.")
    if not user:
        raise RuntimeError("NEO4J_USER mangler i miljøvariabler.")
    if not pwd:
        raise RuntimeError("NEO4J_PASSWORD mangler i miljøvariabler.")

    log(f"Kobler til Neo4j @ {uri} (database={db})")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))

    # test
    with driver.session(database=db) as session:
        ok = session.run("RETURN 1 AS ok").single()["ok"]
        if ok != 1:
            raise RuntimeError("Neo4j test-tilkobling feilet.")

    log("Neo4j-tilkobling OK.")
    return driver, db


def upsert_chunks(driver, database: str, points):
    """Lagrer chunks i Neo4j i batches."""
    BATCH_SIZE = 100
    total = len(points)

    log(f"Starter Neo4j-sync av {total} chunks...")

    def write_tx(tx, rows):
        tx.run(
            """
            UNWIND $rows AS row
            WITH row WHERE row.slug IS NOT NULL

            MERGE (p:EFCPaper {slug: row.slug})
              ON CREATE SET
                p.title = coalesce(row.paper_title, p.title),
                p.doi   = coalesce(row.doi, p.doi)

            MERGE (c:RAGChunk {id: row.id})
              ON CREATE SET
                c.text        = row.text,
                c.chunk_index = row.chunk_index,
                c.path        = row.path,
                c.slug        = row.slug,
                c.doi         = row.doi,
                c.source      = row.source
              ON MATCH SET
                c.text        = row.text,
                c.chunk_index = row.chunk_index,
                c.path        = row.path,
                c.slug        = row.slug,
                c.doi         = row.doi,
                c.source      = row.source

            MERGE (c)-[:FROM_PAPER]->(p)

            WITH c, row
            WHERE row.keywords IS NOT NULL AND size(row.keywords) > 0
            UNWIND row.keywords AS kw
            WITH c, trim(kw) AS kw_name WHERE kw_name <> ""

            MERGE (k:Keyword {name: kw_name})
            MERGE (c)-[:HAS_KEYWORD]->(k)
            """,
            rows=rows
        )

    with driver.session(database=database) as session:
        for i in range(0, total, BATCH_SIZE):
            batch = []

            for pid, payload in points[i:i+BATCH_SIZE]:
                keywords = payload.get("keywords", [])
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",") if k.strip()]

                batch.append({
                    "id": pid,
                    "text": payload.get("text", ""),
                    "chunk_index": payload.get("chunk_index"),
                    "path": payload.get("path"),
                    "slug": payload.get("slug"),
                    "doi": payload.get("doi"),
                    "paper_title": payload.get("paper_title"),
                    "source": payload.get("source", "efc_paper"),
                    "keywords": keywords,
                })

            session.execute_write(write_tx, batch)
            log(f"  Synced {min(i+BATCH_SIZE, total)} / {total} chunks...")

    log("Neo4j-sync ferdig.")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    log("Starter SYNC RAG → Neo4j...")

    collection = os.environ.get("QDRANT_COLLECTION", "efc_rag_local")

    qdrant = get_qdrant_client()
    points = scroll_all_points(qdrant, collection)

    if not points:
        log("Ingen points funnet i Qdrant.")
        return

    driver, db = get_neo4j_driver()
    upsert_chunks(driver, db, points)

    log("SYNC RAG → Neo4j FULLFØRT.")


if __name__ == "__main__":
    main()
