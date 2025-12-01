#!/usr/bin/env python
import os
from qdrant_client import QdrantClient
from qdrant_client.models import ScrollRequest
from neo4j import GraphDatabase


QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc_docs")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def connect_qdrant():
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL/QDRANT_API_KEY is not set")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return client


def connect_neo4j():
    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        raise RuntimeError("NEO4J_URI/USER/PASSWORD is not set")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver


def upsert_document(tx, doc_id: str):
    tx.run(
        """
        MERGE (d:Document {id: $doc_id})
        ON CREATE SET d.first_seen = datetime()
        SET d.last_ingested = datetime()
        """,
        doc_id=doc_id,
    )


def main():
    print(f"[SYNC] Qdrant={QDRANT_URL}, collection={QDRANT_COLLECTION}")
    print(f"[SYNC] Neo4j={NEO4J_URI}")

    qdrant = connect_qdrant()
    driver = connect_neo4j()

    offset = None
    total_points = 0
    docs_seen = set()

    with driver.session() as session:
        while True:
            points, offset = qdrant.scroll(
                collection_name=QDRANT_COLLECTION,
                scroll_filter=None,
                limit=256,
                offset=offset,
                with_payload=True,
            )
            if not points:
                break

            for p in points:
                total_points += 1
                payload = p.payload or {}
                source = payload.get("source")
                if not source:
                    continue

                # "docs/efc/efc_core.md#chunk=0001" → "docs/efc/efc_core.md"
                doc_id = source.split("#", 1)[0]
                if doc_id in docs_seen:
                    continue
                docs_seen.add(doc_id)

                session.write_transaction(upsert_document, doc_id)
                print(f"[SYNC] Document node: {doc_id}")

    print(f"[SYNC] Done. Points scanned: {total_points}, documents: {len(docs_seen)}")


if __name__ == "__main__":
    main()
