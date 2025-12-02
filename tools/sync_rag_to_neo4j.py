#!/usr/bin/env python3
"""
Sync RAG embeddings from Qdrant → Neo4j
Compatible with Qdrant Cloud (no scroll, uses search batching)
"""

import os
from qdrant_client import QdrantClient
from neo4j import GraphDatabase


# ======================
#  ENVIRONMENT
# ======================
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc_docs")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# ======================
#  HELPERS
# ======================
def log(msg):
    print(f"[SYNC] {msg}", flush=True)


# ======================
#  QDRANT CLIENT
# ======================
def connect_qdrant():
    log(f"Connecting to Qdrant: {QDRANT_URL}")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30,
        prefix=None,
    )
    return client


# ======================
#  NEO4J CLIENT
# ======================
def connect_neo4j():
    log(f"Connecting to Neo4j: {NEO4J_URI}")
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_lifetime=200,
    )
    return driver


# Create node
def create_node(tx, point_id, text, source, chunk, url):
    tx.run(
        """
        MERGE (d:Document {id: $point_id})
        SET d.text = $text,
            d.source = $source,
            d.chunk = $chunk,
            d.url = $url
        """,
        point_id=point_id,
        text=text,
        source=source,
        chunk=chunk,
        url=url,
    )


# ======================
#  SYNC FUNCTION
# ======================
def sync():
    qdrant = connect_qdrant()
    neo4j = connect_neo4j()

    batch_size = 100
    offset = None
    total_synced = 0

    with neo4j.session() as session:

        log(f"Start sync from Qdrant collection: {QDRANT_COLLECTION}")

        while True:
            # ================================
            #  CLOUD-SAFE SEARCH BATCHING
            # ================================
            search_result = qdrant.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=[0.0] * 1536,  # dummy vector required for Cloud
                limit=batch_size,
                with_payload=True,
                offset=offset,
            )

            if not search_result:
                break

            for point in search_result:
                pid = str(point.id)
                payload = point.payload or {}

                text = payload.get("text", "")
                source = payload.get("source", "")
                chunk = payload.get("chunk", 0)
                url = payload.get("url", "")

                session.write_transaction(
                    create_node,
                    pid,
                    text,
                    source,
                    chunk,
                    url,
                )

                total_synced += 1

            offset = (offset or 0) + batch_size
            log(f"Synced {total_synced} points so far...")

        log(f"DONE. Total synced: {total_synced}")


# ======================
#  MAIN
# ======================
if __name__ == "__main__":
    log(f"QDRANT={QDRANT_URL}, collection={QDRANT_COLLECTION}")
    log(f"NEO4J={NEO4J_URI}")

    sync()
