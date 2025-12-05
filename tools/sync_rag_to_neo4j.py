#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sync RAG fra Qdrant Cloud til Neo4j (DEDUP-SIKKER).

- Leser alle points fra Qdrant (scroll)
- Lager deterministisk chunk_id = sha256(path + chunk_index)
- MERGE i Neo4j (ingen duplikater)
- Oppdaterer full metadata tryggt
"""

import os
import hashlib
from qdrant_client import QdrantClient
from neo4j import GraphDatabase


# === ENV ===
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

BATCH_SIZE = 100


def log(msg: str) -> None:
    print(f"[SYNC] {msg}", flush=True)


def make_chunk_id(path: str, idx: int) -> str:
    key = f"{path}:{idx}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def main() -> None:

    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL og QDRANT_API_KEY må være satt.")
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        raise RuntimeError("NEO4J_URI/USER/PASSWORD må være satt.")

    log(f"QDRANT={QDRANT_URL}, collection={QDRANT_COLLECTION}")
    log(f"NEO4J={NEO4J_URI}")

    # --- Connect ---
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        prefer_grpc=False,
    )

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )

    offset = None
    total = 0

    log("Connected. Begin scroll...")

    with driver.session(database=NEO4J_DATABASE) as session:

        while True:
            points, offset = qdrant.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=BATCH_SIZE,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not points:
                break

            for p in points:
                payload = p.payload or {}

                text = payload.get("text")
                source = payload.get("source")
                path = payload.get("path", "")
                slug = payload.get("slug")
                idx = int(payload.get("chunk_index", 0))
                paper_title = payload.get("paper_title")
                doi = payload.get("doi")
                keywords = payload.get("keywords", [])

                if not text:
                    continue

                chunk_id = make_chunk_id(path, idx)

                session.run(
                    """
                    MERGE (c:Chunk {id: $id})
                    SET
                        c.text = $text,
                        c.source = $source,
                        c.path = $path,
                        c.slug = $slug,
                        c.chunk_index = $chunk_index,
                        c.paper_title = $paper_title,
                        c.doi = $doi,
                        c.keywords = $keywords
                    """,
                    id=chunk_id,
                    text=text,
                    source=source,
                    path=path,
                    slug=slug,
                    chunk_index=idx,
                    paper_title=paper_title,
                    doi=doi,
                    keywords=keywords,
                )

                total += 1

            log(f"Processed batch. Total: {total}")

            if offset is None:
                break

    log(f"Completed. Total synced: {total}")


if __name__ == "__main__":
    main()
