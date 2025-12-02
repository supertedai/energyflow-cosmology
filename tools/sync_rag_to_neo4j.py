#!/usr/bin/env python3
"""
Sync RAG fra Qdrant Cloud til Neo4j.

Leser alle points fra Qdrant (scroll)
og lager Chunk-noder i Neo4j.
"""

import os
from qdrant_client import QdrantClient
from neo4j import GraphDatabase


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc_docs")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

BATCH_SIZE = 100


def log(msg: str) -> None:
    print(f"[SYNC] {msg}", flush=True)


def main() -> None:
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL og QDRANT_API_KEY må være satt.")
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        raise RuntimeError("NEO4J_URI/USER/PASSWORD må være satt.")

    log(f"QDRANT={QDRANT_URL}, collection={QDRANT_COLLECTION}")
    log(f"NEO4J={NEO4J_URI}")

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

    with driver.session() as session:
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
                chunk_id = payload.get("chunk_id") or str(p.id)

                if not text:
                    continue

                session.run(
                    """
                    MERGE (c:Chunk {id: $id})
                    SET c.text = $text,
                        c.source = $source
                    """,
                    id=chunk_id,
                    text=text,
                    source=source,
                )
                total += 1

            log(f"Processed batch. Total: {total}")

            if offset is None:
                break

    log(f"Completed. Total synced: {total}")


if __name__ == "__main__":
    main()
