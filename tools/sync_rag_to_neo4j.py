#!/usr/bin/env python3
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


def sync():
    print(f"[SYNC] QDRANT={QDRANT_URL}, collection={QDRANT_COLLECTION}")
    print(f"[SYNC] NEO4J={NEO4J_URI}")

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        prefer_grpc=False
    )

    neo4j = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    print("[SYNC] Connected. Begin scroll...")

    offset = None
    total = 0

    while True:
        scroll_result = qdrant.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        points, offset = scroll_result

        if not points:
            break

        for p in points:
            payload = p.payload or {}
            text = payload.get("text")
            source = payload.get("source")
            chunk_id = payload.get("chunk_id")

            if not text:
                continue

            with neo4j.session() as session:
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

        print(f"[SYNC] Processed batch. Total: {total}")

        if offset is None:
            break

    print(f"[SYNC] Completed. Total synced: {total}")


if __name__ == "__main__":
    sync()
