from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

app = FastAPI(
    title="Graph-RAG API",
    version="1.0.0"
)

@app.get("/health")
def health():
    return {"status": "ok", "neo4j": bool(NEO4J_URI)}

@app.get("/search")
def search(q: str):
    try:
        cypher = """
        CALL db.index.fulltext.queryNodes('efc_index', $q)
        YIELD node, score
        RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
        ORDER BY score DESC LIMIT 10
        """

        with driver.session(database=NEO4J_DATABASE) as session:
            rows = session.run(cypher, q=q)
            results = [
                {
                    "title": r["title"],
                    "slug": r["slug"],
                    "keywords": r["keywords"],
                    "score": r["score"]
                }
                for r in rows
            ]

        return {"query": q, "results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
