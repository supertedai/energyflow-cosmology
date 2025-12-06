import os
from neo4j import GraphDatabase

# -------------------------
# Env-variabler
# -------------------------
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = None

if NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
else:
    print("⚠️ Neo4j disabled — missing environment variables.")


def run_query(query: str,
              params: dict | None = None,
              parameters: dict | None = None,
              **kwargs):
    """
    Kjører en enkel Cypher-spørring.

    Støtter begge kall:
      - run_query(query, params={...})
      - run_query(query, parameters={...})
    Ekstra kwargs ignoreres.
    """
    if driver is None:
        raise RuntimeError("Neo4j driver not initialized. Set NEO4J_* env vars.")

    payload = parameters if parameters is not None else params
    if payload is None:
        payload = {}

    with driver.session() as session:
        result = session.run(query, payload)
        return result.data()

