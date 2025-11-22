#!/usr/bin/env python3
from fastapi import FastAPI
from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
app = FastAPI()


def run_query(query: str):
    with driver.session() as s:
        return [r.data() for r in s.run(query)]


@app.get("/rag/chunks")
def rag_chunks():
    q = """
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n.id AS id,
           labels(n) AS labels,
           properties(n) AS props,
           collect({type:type(r), target:m.id}) AS rels
    """
    return run_query(q)
