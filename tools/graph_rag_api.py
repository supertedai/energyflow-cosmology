#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph-RAG API
=============

Tynt API-lag over Neo4j-grafen din.

Formål:
- Gi et raskt, lettvekts endepunkt for graf-søk
- Bruke EFCPaper-noder som primær inngang
- Klart skille fra unified-API-et (som også blander inn RAG/Qdrant)

Endepunkter:
- GET  /health
- GET  /search?q=...
"""

import os
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from neo4j import GraphDatabase, Driver

# ------------------------------------------------------------
# Konfig via miljøvariabler (Cloud Run / GitHub Actions)
# ------------------------------------------------------------

NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    # Vi lar appen starte, men loggfører hardt.
    logging.warning(
        "NEO4J-konfig er ikke komplett. "
        "Sett NEO4J_URI, NEO4J_USER og NEO4J_PASSWORD i miljøvariabler."
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graph-rag-api")

# ------------------------------------------------------------
# FastAPI-init
# ------------------------------------------------------------

app = FastAPI(
    title="EFC Graph-RAG API",
    version="1.0.0",
    description=(
        "Lettvekts API for søk i EFC-grafen (Neo4j). "
        "Primært over EFCPaper-noder + enkle tekstmatcher."
    ),
)


# ------------------------------------------------------------
# Pydantic-modeller
# ------------------------------------------------------------

class GraphPaper(BaseModel):
    slug: str
    title: str
    doi: Optional[str] = None
    keywords: Optional[List[str]] = None
    score: Optional[float] = None  # enkel heuristisk score


class SearchResponse(BaseModel):
    query: str
    count: int
    results: List[GraphPaper]


# ------------------------------------------------------------
# Neo4j-driver (global)
# ------------------------------------------------------------

_driver: Optional[Driver] = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
            raise RuntimeError("NEO4J-tilkobling ikke konfigurert (mangler env vars).")
        logger.info("Oppretter Neo4j-driver mot %s", NEO4J_URI)
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j-driver lukket.")


@app.on_event("shutdown")
def shutdown_event():
    close_driver()


# ------------------------------------------------------------
# Internt: enkel søkefunksjon
# ------------------------------------------------------------

def _search_papers(query: str, limit: int = 25) -> List[GraphPaper]:
    """
    En enkel søkefunksjon over EFCPaper-noder.

    Strategi (robust, ikke avhengig av fulltekst-indeks):
    - Matcher på title (CONTAINS, case-insensitive)
    - Matcher på keywords (hvis liste-felt)
    """
    driver = get_driver()

    cypher = """
    MATCH (p:EFCPaper)
    WHERE toLower(p.title) CONTAINS toLower($q)
       OR (exists(p.keywords) AND any(k IN p.keywords WHERE toLower(k) CONTAINS toLower($q)))
    RETURN p
    LIMIT $limit
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        records = session.run(cypher, q=query, limit=limit)

        results: List[GraphPaper] = []
        for rec in records:
            node = rec["p"]
            slug = node.get("slug") or node.get("id") or ""
            title = node.get("title") or slug or "Untitled"

            kp = node.get("keywords")
            if isinstance(kp, str):
                keywords = [kp]
            elif isinstance(kp, list):
                keywords = kp
            else:
                keywords = None

            doi = node.get("doi")

            # Her kan du senere plugge inn en "ordentlig" relevansscore
            paper = GraphPaper(
                slug=slug,
                title=title,
                doi=doi,
                keywords=keywords,
                score=None,
            )
            results.append(paper)

    return results


# ------------------------------------------------------------
# Endepunkter
# ------------------------------------------------------------

@app.get("/health")
def health():
    """
    Enkel helsesjekk.
    Verifiserer også at Neo4j-URI er satt (men ikke at vi nødvendigvis får kontakt).
    """
    status = "ok"
    neo4j_status = "configured" if NEO4J_URI else "missing"

    return {
        "status": status,
        "neo4j": neo4j_status,
        "uri": NEO4J_URI,
        "database": NEO4J_DATABASE,
    }


@app.get("/search", response_model=SearchResponse)
def search(q: str = Query(..., description="Fritekst-spørring mot EFCPaper-grafen"),
           limit: int = Query(25, ge=1, le=100)) -> SearchResponse:
    """
    GET /search?q=...

    Lettvekts graf-søk.
    Matcher på title + keywords for EFCPaper.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query kan ikke være tom.")

    try:
        papers = _search_papers(q.strip(), limit=limit)
    except RuntimeError as exc:
        logger.exception("Konfig-/tilkoblingsfeil mot Neo4j")
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Uventet feil ved graf-søk")
        raise HTTPException(status_code=500, detail=f"Feil ved graf-søk: {exc}")

    return SearchResponse(
        query=q,
        count=len(papers),
        results=papers,
    )
