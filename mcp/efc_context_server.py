#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC CONTEXT MCP SERVER
======================

Bruker GitHub som kilde:

- Leser semantic-search-index.json live fra GitHub
- Leser vilkårlige filer via raw.githubusercontent.com
- Kan spørre Graph-RAG API (Neo4j) hvis EFC_GRAPH_API_URL er satt
- Bygger "live context" rundt et fokus (full symbiose-modus)

Env-variabler:

- GITHUB_REPO_OWNER  (f.eks. "supertedai")
- GITHUB_REPO_NAME   (f.eks. "energyflow-cosmology")
- GITHUB_BRANCH      (f.eks. "main")
- GITHUB_TOKEN       (optional, for rate-limit / private repo)
- EFC_GRAPH_API_URL  (f.eks. "http://localhost:8082/search")

Krever:
    pip install "mcp[cli]" aiohttp
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import asyncio
import aiohttp
from mcp.server.fastmcp import FastMCP


# ------------------------ Konfig ------------------------

OWNER = os.getenv("GITHUB_REPO_OWNER", "supertedai")
REPO = os.getenv("GITHUB_REPO_NAME", "energyflow-cosmology")
BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

GRAPH_API_URL = os.getenv("EFC_GRAPH_API_URL", "").rstrip("/")

RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}"

SEMANTIC_INDEX_PATH = "semantic-search-index.json"

# Enkel in-memory cache: { key: (timestamp, data) }
CACHE_TTL_SECONDS = 60
_cache: Dict[str, Tuple[float, Any]] = {}

mcp = FastMCP("efc_context")


# ------------------------ Hjelpere ------------------------


def _cache_get(key: str) -> Optional[Any]:
    now = time.time()
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < CACHE_TTL_SECONDS:
            return data
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (time.time(), data)


async def _fetch_raw_text(session: aiohttp.ClientSession, rel_path: str) -> str:
    """
    Hent tekstinnhold fra GitHub raw.
    rel_path: f.eks. "docs/papers/efc/EFC-Master-Specification/README.md"
    """
    rel = rel_path.lstrip("/")
    url = f"{RAW_BASE}/{rel}"

    cache_key = f"raw:{rel}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with session.get(url, headers=headers, timeout=60) as resp:
        if resp.status != 200:
            text = await resp.text()
            _cache_set(cache_key, f"[HTTP {resp.status}] Could not fetch {rel_path}: {text[:2000]}")
            return _cache_get(cache_key)

        data = await resp.text()
        _cache_set(cache_key, data)
        return data


async def _fetch_semantic_index(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """
    Leser semantic-search-index.json fra repoet.
    Håndterer både liste og dict med items/nodes/entries.
    """
    cache_key = "semantic-index"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{RAW_BASE}/{SEMANTIC_INDEX_PATH}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with session.get(url, headers=headers, timeout=60) as resp:
        if resp.status != 200:
            # tom liste hvis ikke funnet
            _cache_set(cache_key, [])
            return []

        text = await resp.text()
        try:
            data = json.loads(text)
        except Exception:
            _cache_set(cache_key, [])
            return []

    items: List[Dict[str, Any]] = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("items", "nodes", "entries"):
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        if not items:
            # fallback: pakk hele dict-en som ett item
            items = [data]

    _cache_set(cache_key, items)
    return items


def _score_item(item: Dict[str, Any], query: str) -> int:
    """
    Veldig enkel scoring: teller treff av query-strengen
    i relevante felt.
    """
    q = query.lower().strip()
    if not q:
        return 0

    fields = ["title", "description", "path", "keywords", "tags"]
    text_parts: List[str] = []

    for field in fields:
        v = item.get(field)
        if isinstance(v, str):
            text_parts.append(v)
        elif isinstance(v, list):
            text_parts.extend(str(x) for x in v)

    haystack = " ".join(text_parts).lower()
    if not haystack:
        return 0

    return haystack.count(q)


def _make_snippet(text: str, max_len: int = 600) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


# ------------------------ MCP-verktøy ------------------------


@mcp.tool()
async def search_efc_papers(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Søk i semantic-search-index.json etter EFC-innhold.

    - query: fritekst (tittel, nøkkelord, path, osv.)
    - max_results: maks antall treff

    Returnerer:
    [
      {
        "title": ...,
        "path": ...,
        "tags": [...],
        "score_hint": int,
        "raw": {...}
      },
      ...
    ]
    """
    q = query.lower().strip()
    if not q:
        return []

    async with aiohttp.ClientSession() as session:
        items = await _fetch_semantic_index(session)

    scored: List[Dict[str, Any]] = []
    for item in items:
        score = _score_item(item, q)
        if score <= 0:
            continue

        scored.append(
            {
                "title": item.get("title"),
                "path": item.get("path"),
                "tags": item.get("tags") or item.get("keywords"),
                "score_hint": score,
                "raw": item,
            }
        )

    scored.sort(key=lambda x: x.get("score_hint", 0), reverse=True)
    return scored[:max_results]


@mcp.tool()
async def get_efc_document(rel_path: str, max_chars: int = 20000) -> str:
    """
    Hent innholdet i en fil fra GitHub-repoet (raw).

    - rel_path: relativ sti i repoet, f.eks.
      "docs/papers/efc/EFC-Master-Specification/README.md"
    - max_chars: maks antall tegn som returneres (default 20k)

    Returnerer tekst. Trunkerer lange filer.
    """
    rel = rel_path.lstrip("/")

    async with aiohttp.ClientSession() as session:
        text = await _fetch_raw_text(session, rel)

    if len(text) > max_chars:
        return text[: max_chars - 3] + "..."
    return text


@mcp.tool()
async def graph_search(query: str, limit: int = 10) -> Any:
    """
    Spør Graph-RAG API-et (Neo4j-backend) om et søk.

    Forventer at EFC_GRAPH_API_URL peker til f.eks:
        http://localhost:8082/search

    - query: naturlig språk, f.eks. "s0 s1 CMB entropi-grense"
    - limit: maks antall treff

    Returnerer rå JSON fra API-et, eller feilmelding.
    """
    if not GRAPH_API_URL:
        return {
            "error": "EFC_GRAPH_API_URL is not set.",
            "hint": "Set EFC_GRAPH_API_URL to your Graph-RAG search endpoint.",
        }

    url = GRAPH_API_URL
    payload = {"query": query, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    return {"status": resp.status, "raw": text}
                return data
    except Exception as e:
        return {"error": str(e), "endpoint": url}


@mcp.tool()
async def efc_live_context(
    focus: str,
    extra_notes: Optional[str] = None,
    max_results: int = 5,
    include_graph: bool = True,
) -> Dict[str, Any]:
    """
    Bygg en "live context"-pakke for modellen.

    - focus: hovedspørsmål / fokus-tema
    - extra_notes: evt. ekstra tekst (f.eks. sammendrag av siste dialog)
    - max_results: hvor mange papers/noder som skal tas med
    - include_graph: om vi skal prøve Graph-RAG også

    Returnerer:
    {
      "focus": "...",
      "query_used": "...",
      "papers": [
          {
            "title": ...,
            "path": ...,
            "snippet": ...,
            "tags": [...],
          },
          ...
      ],
      "graph_result": {...} eller null,
      "system_context_suggestion": "Tekst som modellen kan bruke som systemprompt."
    }
    """
    # Kombiner fokus og ekstra notater til en søkestreng
    merged_query = focus
    if extra_notes:
        merged_query = f"{focus}\n\n{extra_notes}"

    # Enkelt triks: begrens litt lengde på query
    merged_query_short = merged_query[:1000]

    # 1) Søk i semantic-index
    async with aiohttp.ClientSession() as session:
        items = await _fetch_semantic_index(session)

        # Score manuelt siden vi bruker combined query
        scored: List[Dict[str, Any]] = []
        for item in items:
            score = _score_item(item, merged_query_short)
            if score <= 0:
                continue
            scored.append(
                {
                    "title": item.get("title"),
                    "path": item.get("path"),
                    "tags": item.get("tags") or item.get("keywords"),
                    "score_hint": score,
                    "raw": item,
                }
            )

        scored.sort(key=lambda x: x.get("score_hint", 0), reverse=True)
        top = scored[:max_results]

        # 2) Hent tekstsnutter for disse
        papers: List[Dict[str, Any]] = []
        for it in top:
            path = it.get("path")
            snippet = ""
            if path:
                try:
                    raw_text = await _fetch_raw_text(session, path)
                    snippet = _make_snippet(raw_text)
                except Exception as e:
                    snippet = f"[Feil ved henting av {path}: {e}]"

            papers.append(
                {
                    "title": it.get("title"),
                    "path": path,
                    "tags": it.get("tags"),
                    "snippet": snippet,
                }
            )

    # 3) Spør eventuelt grafen
    graph_result: Any = None
    if include_graph and GRAPH_API_URL:
        try:
            async with aiohttp.ClientSession() as session:
                url = GRAPH_API_URL
                payload = {"query": merged_query_short, "limit": max_results}
                async with session.post(url, json=payload, timeout=60) as resp:
                    text = await resp.text()
                    try:
                        graph_result = json.loads(text)
                    except json.JSONDecodeError:
                        graph_result = {"status": resp.status, "raw": text}
        except Exception as e:
            graph_result = {"error": str(e), "endpoint": GRAPH_API_URL}

    # 4) Lag en system-kontekst-tekst som modellen kan bruke direkte
    lines: List[str] = []

    lines.append("You are operating inside the Energy-Flow Cosmology (EFC) repository context.")
    lines.append("Use the following papers and snippets as primary context for answering the user.")
    lines.append("")
    lines.append(f"FOCUS: {focus}")
    if extra_notes:
        lines.append("")
        lines.append("ADDITIONAL NOTES FROM RECENT DIALOG:")
        lines.append(extra_notes.strip())
    lines.append("")
    if papers:
        lines.append("RELEVANT PAPERS AND FILES:")
        for p in papers:
            title = p.get("title") or "(no title)"
            path = p.get("path") or "(no path)"
            tags = p.get("tags") or []
            tag_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
            lines.append(f"- {title}  [path: {path}]  [tags: {tag_str}]")
    else:
        lines.append("No relevant papers found in semantic index for this focus.")

    if graph_result:
        lines.append("")
        lines.append("GRAPH CONTEXT (Neo4j / Graph-RAG) IS AVAILABLE. Use it as a structural guide if needed.")

    system_context = "\n".join(lines)

    return {
        "focus": focus,
        "query_used": merged_query_short,
        "papers": papers,
        "graph_result": graph_result,
        "system_context_suggestion": system_context,
    }


if __name__ == "__main__":
    # Kjør MCP-server over stdio for klienter (som Msty)
    mcp.run(transport="stdio")
