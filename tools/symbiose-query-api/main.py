#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symbiose Query API – Msty-adapter
=================================

Denne tjenesten er en TYNNT LAG rundt hoved-API-et ditt
(`unified-api-.../unified_query`).

Den gjør:

- /health      → enkel helsesjekk
- /unified_query (POST) → forward til UNIFIED_API_URL
- /search (GET) → Msty-kompatibel endpoint, forwarder til UNIFIED_API_URL

All “smarthet” (Neo4j, Qdrant, semantic index, AUTH-lag osv.)
ligger i unified-API-et. Denne tjenesten bare speiler det.
"""

import os
import time
import logging
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# ------------------------------------------------------------
# Konfig
# ------------------------------------------------------------

# URL til hoved-API-et som faktisk gjør jobben.
# Kan overstyres med env-var i Cloud Run.
UNIFIED_API_URL = os.getenv(
    "UNIFIED_API_URL",
    "https://unified-api-958872099364.europe-west1.run.app/unified_query",
)

UNIFIED_API_TIMEOUT = float(os.getenv("UNIFIED_API_TIMEOUT", "30.0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("symbiose-query-api")

app = FastAPI(
    title="Symbiose Query API (Msty adapter)",
    version="1.0.0",
    description=(
        "Tynt proxy-lag som eksponerer /search for Msty og forwarder "
        "til unified EFC-API-et."
    ),
)


class UnifiedQueryRequest(BaseModel):
    text: str


# ------------------------------------------------------------
# Intern helper – kaller unified-API-et
# ------------------------------------------------------------

def call_unified_backend(query_text: str) -> Dict[str, Any]:
    """
    Kall hoved-API-et (unified-api) med samme struktur som curl-kallet ditt:

        POST UNIFIED_API_URL
        {
            "text": "<spørringen>"
        }
    """
    if not UNIFIED_API_URL:
        logger.error("UNIFIED_API_URL er ikke satt")
        raise HTTPException(
            status_code=500,
            detail="UNIFIED_API_URL er ikke konfigurert i miljøvariabler.",
        )

    payload = {"text": query_text}
    logger.info("Forwarder til unified backend: %s", UNIFIED_API_URL)

    try:
        resp = requests.post(
            UNIFIED_API_URL,
            json=payload,
            timeout=UNIFIED_API_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Feil ved kall til unified backend")
        raise HTTPException(
            status_code=502,
            detail=f"Feil ved kontakt med unified API: {exc}",
        )

    if resp.status_code >= 400:
        logger.error(
            "Unified backend svarte med %s: %s",
            resp.status_code,
            resp.text[:500],
        )
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Unified API feil: {resp.text}",
        )

    try:
        data = resp.json()
    except ValueError:
        logger.error("Unified backend returnerte ikke gyldig JSON")
        raise HTTPException(
            status_code=502,
            detail="Unified API returnerte ikke gyldig JSON.",
        )

    return data


# ------------------------------------------------------------
# Endepunkter
# ------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    """Enkel helsesjekk for Cloud Run / monitoring."""
    return {
        "status": "ok",
        "service": "symbiose-query-api",
        "time": time.time(),
        "unified_api_url": UNIFIED_API_URL,
    }


@app.post("/unified_query")
def unified_query(body: UnifiedQueryRequest) -> Dict[str, Any]:
    """
    POST /unified_query

    Samme semantikk som hoved-API-et.
    Forwarder bare videre til UNIFIED_API_URL.
    """
    return call_unified_backend(body.text)


@app.get("/search")
def search(q: str = Query(..., description="Fritekst-spørring (Msty-kompatibel)")) -> Dict[str, Any]:
    """
    GET /search?q=...

    Dette er *Msty-endepunktet*.

    Tidligere: 404 → FetchError i Msty.
    Nå: forwarder til unified-API-et med samme query som POST /unified_query.
    """
    return call_unified_backend(q)
