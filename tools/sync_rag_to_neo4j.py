#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYNC RAG → NEO4J
================

Leser alle RAG-chunks fra Qdrant og speiler dem inn i Neo4j.

- Kilde: Qdrant collection (default: "efc_rag_local")
- Lager noder i Neo4j:
    (:RAGChunk { id, text, chunk_index, path, slug, doi, source })
- Kobler til:
    (:EFCPaper {slug}) via [:FROM_PAPER]
    (:Keyword {name}) via [:HAS_KEYWORD]

Forventer miljøvariabler:

    QDRANT_URL
    QDRANT_API_KEY

    NEO4J_URI
    NEO4J_USERNAME
    NEO4J_PASSWORD
    NEO4J_DATABASE

Kjør trygt i GitHub Actions.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

from qdrant_client import QdrantClient
from qdrant_client import models as qm
from neo4j import GraphDatabase


ROOT = Path(__file__).resolve().parents[1]

# Samme collection som ingest-scriptet bruker
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "efc_rag_local")


def log(msg: str) -> None:
    print(f"[sync-rag-neo4j] {msg}", flush=True)


# ------------------------- QDRANT -------------------------


def get_qdrant_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("QDRANT_URL mangler i miljøvariabler")
    if not api_key:
        raise RuntimeError("QDRANT_API_KEY mangler i miljøvariabler")

    log(f"Kobler til Qdrant @ {url}")
    client = QdrantClient(url=url, api_key=api_key)

    # Enkel sanity check
    _ = client.get_collections()
    log("Qdrant-tilkobling OK.")
    return client


def scroll_all_points(
    client: QdrantClient, collection_name: str
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Leser alle points (id + payload) fra Qdrant-collection.
    Returnerer liste av (id, payload).
    """
    all_points: List[Tuple[str, Dict[str, Any]]] = []
    offset = None

    while True:
        res, offset = client.scroll(
            collection_name=collection_name,
            offset=offset,
            limit=256,
            with_payload=True,
            with_vectors=False,
        )
        if not res:
            break

        for pt in res:
            pid = str(pt.id)
            payload = pt.payload or {}
            all_points.append((pid, payload))

        if offset is None:
            break

    log(f"Fant totalt {len(all_points)} points i Qdrant-collection '{collection_name}'.")
    return all_points


# ------------------------- NEO4J -------------------------


def get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME")
    pwd = os.environ.get("NEO4J_PASSWORD")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")

    if not uri:
        raise RuntimeError("NEO4J_URI mangler i miljøvariabler")
    if not user:
        raise RuntimeError("NEO4J_USERNAME mangler i miljøvariabler")
    if not pwd:
        raise RuntimeError("NEO4J_PASSWORD mangler i miljøvariabler")

    log(f"Kobler til Neo4j @ {uri}, database={database}")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    # test-connection
    with driver.session(database=database) as session:
        val = session.run("RETURN 1 AS ok").single()["ok"]
        if val != 1:
            raise RuntimeError("Neo4j test-tilkobling feilet.")
    log("Neo4j-tilkobling OK.")
    return driver, database


def upsert_chunks_in_neo4j(
    driver,
    database: str,
    points: List[Tuple[str, Dict[str, Any]]],
) -> None:
    """
    Skriver RAG-chunks til Neo4j:

    MERGE (p:EFCPaper {slug})
    MERGE (c:RAGChunk {id})
    MERGE (c)-[:FROM_PAPER]->(p)
    MERGE (c)-[:HAS_KEYWORD]->(k:Keyword {name})
    """

    def _tx_write(tx, batch: List[Dict[str, Any]]):
        query = """
        UNWIND $rows AS row
        WITH row
        WHERE row.slug IS NOT NULL

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
        WITH c, trim(kw) AS kw_name
        WHERE kw_name <> ""
        MERGE (k:Keyword {name: kw_name})
        MERGE (c)-[:HAS_KEYWORD]->(k)
        """
        tx.run(query, rows=batch)

    if not points:
        log("Ingen points å sync'e til Neo4j.")
        return

    batch_size = 100
    total = len(points)
    log(f"Starter Neo4j-sync av {total} chunks...")

    with driver.session(database=database) as session:
        for i in range(0, total, batch_size):
            chunk = points[i : i + batch_size]
            batch_rows = []
            for pid, payload in chunk:
                slug = payload.get("slug")
                text = payload.get("text")
                cidx = payload.get("chunk_index")
                path = payload.get("path")
                doi = payload.get("doi")
                paper_title = payload.get("paper_title")
                source = payload.get("source", "efc_paper")
                keywords = payload.get("keywords")

                if isinstance(keywords, str):
                    keywords_list = [k.strip() for k in keywords.split(",") if k.strip()]
                elif isinstance(keywords, list):
                    keywords_list = [str(k).strip() for k in keywords if str(k).strip()]
                else:
                    keywords_list = []

                row = {
                    "id": pid,
                    "slug": slug,
                    "text": text,
                    "chunk_index": cidx,
                    "path": path,
                    "doi": doi,
                    "paper_title": paper_title,
                    "source": source,
                    "keywords": keywords_list,
                }
                batch_rows.append(row)

            session.execute_write(_tx_write, batch=batch_rows)
            log(f"  Synced {min(i + batch_size, total)} / {total} chunks...")

    log("Neo4j-sync ferdig.")


# ------------------------- MAIN -------------------------


def main():
    log("Starter SYNC RAG → Neo4j...")

    qdrant = get_qdrant_client()
    points = scroll_all_points(qdrant, QDRANT_COLLECTION)

    if not points:
        log("Ingen points funnet i Qdrant. Avslutter.")
        return

    driver, database = get_neo4j_driver()
    upsert_chunks_in_neo4j(driver, database, points)

    log("SYNC RAG → Neo4j fullført.")


if __name__ == "__main__":
    main()
