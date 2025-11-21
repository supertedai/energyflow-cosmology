#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC MCP Server
==============

Eksponerer EFC-repoet som MCP-verktøy:

- search_efc_papers(query): enkel søk i semantic-index / metadata
- get_efc_document(path): leser en fil fra repoet (md/tex/txt)
- graph_search(query): kaller Graph-RAG API hvis satt opp

Kjøres via stdio fra en MCP-klient (Msty, Claude, osv.).
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import asyncio
import aiohttp  # pip install aiohttp
from mcp.server.fastmcp import FastMCP  # pip install "mcp[cli]"

# ----------------- Konfig -----------------

# Rot til repoet (kan overrides i env)
EFC_ROOT = Path(os.getenv("EFC_REPO_ROOT", ".")).resolve()

SEMANTIC_INDEX = EFC_ROOT / "semantic-search-index.json"

# URL til Graph-RAG API (env-styrt)
GRAPH_API_URL = os.getenv("EFC_GRAPH_API_URL", "").rstrip("/")

mcp = FastMCP("efc_repo")


def _load_semantic_index() -> List[Dict[str, Any]]:
    """Leser semantic-search-index.json hvis den finnes."""
    if not SEMANTIC_INDEX.exists():
        return []

    try:
        data = json.loads(SEMANTIC_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []

    # håndter både liste og dict
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # forsøk å hente ut en liste
        for key in ("items", "nodes", "entries"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # fallback: pakk hele dict-en
        return [data]

    return []


@mcp.tool()
async def search_efc_papers(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Søk etter EFC-innhold i semantic-search-index.json.

    - query: fritekst (tittel, nøkkelord, path osv.)
    - max_results: maks antall treff

    Returnerer en liste med små objekter:
    { "title": ..., "path": ..., "tags": [...], "score_hint": ... }
    """
    q = query.lower().strip()
    if not q:
        return []

    items = _load_semantic_index()
    scored: List[Dict[str, Any]] = []

    for item in items:
        text_parts = []
        for k in ("title", "description", "path", "keywords", "tags"):
            v = item.get(k)
            if isinstance(v, str):
                text_parts.append(v)
            elif isinstance(v, list):
                text_parts.extend(str(x) for x in v)
        haystack = " ".join(text_parts).lower()

        if not haystack:
            continue

        # veldig enkel "score": antall treff av query-strengen
        score = haystack.count(q)
        if score > 0:
            scored.append({
                "title": item.get("title"),
                "path": item.get("path"),
                "tags": item.get("tags") or item.get("keywords"),
                "raw": item,
                "score_hint": score,
            })

    # sorter beste først
    scored.sort(key=lambda x: x.get("score_hint", 0), reverse=True)
    return scored[:max_results]


@mcp.tool()
async def get_efc_document(rel_path: str) -> str:
    """
    Hent innholdet i en fil i repoet.

    - rel_path: relativ sti fra repo-root, f.eks.
      "docs/papers/efc/EFC-Master-Specification/README.md"

    Returnerer tekstinnhold. For binære filer gir den en kort melding.
    """
    rel = rel_path.lstrip("/")

    file_path = (EFC_ROOT / rel).resolve()
    # ikke tillat å gå ut av repoet
    if not str(file_path).startswith(str(EFC_ROOT)):
        return f"Path {rel_path} er utenfor repo-root."

    if not file_path.exists():
        return f"Fant ikke fil: {rel_path}"

    # veldig enkel sjekk på filtype
    suffix = file_path.suffix.lower()
    if suffix in [".md", ".txt", ".tex", ".json", ".jsonld"]:
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Feil ved lesing av {rel_path}: {e}"
    else:
        return f"Fil {rel_path} ser ut til å være binær ({suffix}); les den via GitHub-lenke i stedet."


@mcp.tool()
async def graph_search(query: str, limit: int = 10) -> Any:
    """
    Spør Graph-RAG API-et ditt (Neo4j-bakenden).

    Forventer at EFC_GRAPH_API_URL peker til f.eks.
    http://localhost:8082/search

    - query: naturlig språk (f.eks. "papers om s₀/s₁ og CMB")
    - limit: maks antall noder/treff

    Returnerer rå JSON fra API-et.
    """
    if not GRAPH_API_URL:
        return "EFC_GRAPH_API_URL er ikke satt. Sett den til Graph API-endpoint."

    url = GRAPH_API_URL
    payload = {"query": query, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                text = await resp.text()
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {
                        "status": resp.status,
                        "raw": text,
                    }
    except Exception as e:
        return {"error": str(e), "endpoint": url}


if __name__ == "__main__":
    # kjør som stdio-server for MCP-klienter
    mcp.run(transport="stdio")
