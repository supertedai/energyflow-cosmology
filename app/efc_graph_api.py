# efc_graph_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://119e751c.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "change-me")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

app = FastAPI(title="EFC Graph API")

class Concept(BaseModel):
  slug: str
  name: str
  summary: Optional[str] = None
  category: Optional[str] = None
  level: Optional[int] = None
  status: Optional[str] = None

class Paper(BaseModel):
  doi: str
  title: str
  version: Optional[str] = None
  year: Optional[int] = None

def run_query(query: str, params: dict = None):
  with driver.session(database=NEO4J_DATABASE) as session:
    result = session.run(query, params or {})
    return [r.data() for r in result]

@app.get("/concepts", response_model=List[Concept])
def list_concepts():
  rows = run_query("""
    MATCH (c:Concept)
    RETURN c.slug AS slug, c.name AS name, c.summary AS summary,
           c.category AS category, c.level AS level, c.status AS status
    ORDER BY c.level, c.slug
  """)
  return [Concept(**row) for row in rows]

@app.get("/concepts/{slug}", response_model=Concept)
def get_concept(slug: str):
  rows = run_query("""
    MATCH (c:Concept {slug:$slug})
    RETURN c.slug AS slug, c.name AS name, c.summary AS summary,
           c.category AS category, c.level AS level, c.status AS status
  """, {"slug": slug})
  if not rows:
    raise HTTPException(status_code=404, detail="Concept not found")
  return Concept(**rows[0])

@app.get("/concepts/{slug}/neighbourhood")
def concept_neighbourhood(slug: str):
  rows = run_query("""
    MATCH (c:Concept {slug:$slug})
    OPTIONAL MATCH (c)-[r]-(n)
    RETURN c, collect({type:type(r), other:n}) AS relations
  """, {"slug": slug})
  if not rows:
    raise HTTPException(status_code=404, detail="Concept not found")
  return rows[0]

@app.get("/papers/{doi}", response_model=Paper)
def get_paper(doi: str):
  rows = run_query("""
    MATCH (p:Paper {doi:$doi})
    RETURN p.doi AS doi, p.title AS title,
           p.version AS version, p.year AS year
  """, {"doi": doi})
  if not rows:
    raise HTTPException(status_code=404, detail="Paper not found")
  return Paper(**rows[0])

@app.get("/concepts/{slug}/papers", response_model=List[Paper])
def get_papers_for_concept(slug: str):
  rows = run_query("""
    MATCH (c:Concept {slug:$slug})<-[:DESCRIBES]-(p:Paper)
    RETURN p.doi AS doi, p.title AS title,
           p.version AS version, p.year AS year
    ORDER BY p.year DESC
  """, {"slug": slug})
  return [Paper(**row) for row in rows]
