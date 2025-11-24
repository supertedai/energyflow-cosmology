from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
import os

router = APIRouter()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

class QueryRequest(BaseModel):
    query: str

def neo4j_search(tx, text: str):
    cypher = """
    CALL db.index.fulltext.queryNodes('papersIndex', $q)
    YIELD node, score
    RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
    ORDER BY score DESC LIMIT 10
    """
    return list(tx.run(cypher, q=text))

@router.post("/search")
def search(req: QueryRequest):
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            results = session.read_transaction(neo4j_search, req.query)

        return {
            "query": req.query,
            "results": [
                {
                    "title": r["title"],
                    "slug": r["slug"],
                    "keywords": r["keywords"],
                    "score": r["score"]
                }
                for r in results
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
