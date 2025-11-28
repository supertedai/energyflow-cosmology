import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

def run_query(q: str, params: dict = None):
    with driver.session() as session:
        result = session.run(q, params or {})
        return result.data()
