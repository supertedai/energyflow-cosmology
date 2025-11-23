#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symbiose Query API – Msty-adapter
=================================

Denne tjenesten er et tynt lag rundt unified-API-et ditt.
Nå utvidet med et matematikkfilter (LaTeX, EFC-operatører,
validering, beautifier).
"""

import os
import time
import logging
from typing import Any, Dict
import re

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# ------------------------------------------------------------
# Konfig
# ------------------------------------------------------------

UNIFIED_API_URL = os.getenv(
    "UNIFIED_API_URL",
    "https://unified-api-958872099364.europe-west1.run.app/unified_query",
)

UNIFIED_API_TIMEOUT = float(os.getenv("UNIFIED_API_TIMEOUT", "30.0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("symbiose-query-api")

app = FastAPI(
    title="Symbiose Query API (Msty adapter)",
    version="1.1.0",
    description="Tynt proxy-lag + matematikkfilter for EFC.",
)


class UnifiedQueryRequest(BaseModel):
    text: str


# ------------------------------------------------------------
# Mattefilter
# ------------------------------------------------------------

UNICODE_MAP = {
    "×": r"\times ",
    "·": r"\cdot ",
    "∂": r"\partial ",
    "∇": r"\nabla ",
    "∞": r"\infty ",
    "±": r"\pm ",
    "≤": r"\leq ",
    "≥": r"\geq ",
    "≠": r"\neq ",
    "√": r"\sqrt{}",
    "λ": r"\lambda",
    "Σ": r"\Sigma",
    "Δ": r"\Delta",
}

def sanitize_unicode(text: str) -> str:
    for k, v in UNICODE_MAP.items():
        text = text.replace(k, v)
    return text

def wrap_loose_math(text: str) -> str:
    pattern = r"([A-Za-z0-9\^_\/\*\+\-\(\) ]+=+[A-Za-z0-9\^_\/\*\+\-\(\) ]+)"
    return re.sub(pattern, lambda m: r"\[ " + m.group(1) + r" \]", text)

def math_validator(text: str) -> str:
    issues = []
    if text.count("{") != text.count("}"):
        issues.append("Ubalanserte {}")
    if text.count("\\[") != text.count("\\]"):
        issues.append("Ubalanserte \\[ \\]")
    if issues:
        text += "\n\n% VALIDATOR: " + "; ".join(issues)
    return text

def beautify_equations(text: str) -> str:
    lines = text.split("\n")
    out = []
    count = 1

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("\\[") and stripped.endswith("\\]"):
            core = stripped[2:-2].strip()
            numbered = (
                f"\\begin{{equation}}\n"
                f"{core}\n"
                f"\\label{{eq:{count}}}\n"
                f"\\end{{equation}}"
            )
            out.append(numbered)
            count += 1
        else:
            out.append(line)

    return "\n".join(out)

EFC_OPERATORS = r"""
% --- EFC Math Mode operators ---
\newcommand{\GridGrad}{\nabla_{\text{grid}}}
\newcommand{\EntropyFlow}{\Phi_{\text{entropy}}}
\newcommand{\Flow}{\mathcal{F}}
\newcommand{\sZero}{s_{0}}
\newcommand{\sOne}{s_{1}}
\newcommand{\HaloT}{T_{\text{halo}}}
\newcommand{\CMBT}{T_{\text{CMB}}}
\newcommand{\LightSpeed}{c}
\newcommand{\EnergyDensity}{\rho_E}
\newcommand{\EntropyGrad}{\nabla S}
"""

def apply_math_filter(text: str) -> str:
    if not isinstance(text, str):
        return text

    # 1. Unicode → LaTeX
    t1 = sanitize_unicode(text)

    # 2. Automatisk wrapping av løse uttrykk
    t2 = wrap_loose_math(t1)

    # 3. Valider LaTeX-syntaks
    t3 = math_validator(t2)

    # 4. Beautify / nummerering
    t4 = beautify_equations(t3)

    # 5. Prepender EFC-operators hvis matte finnes
    if "\\begin{equation}" in t4 or "\\(" in t4 or "\\[" in t4:
        return EFC_OPERATORS + "\n" + t4

    return t4


# ------------------------------------------------------------
# Intern helper – kaller unified-API-et
# ------------------------------------------------------------

def call_unified_backend(query_text: str) -> Dict[str, Any]:
    """
    Forwarder til unified backend og legger mattefilter på responsen.
    """

    if not UNIFIED_API_URL:
        raise HTTPException(
            status_code=500,
            detail="UNIFIED_API_URL er ikke konfigurert."
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
            detail=f"Feil ved kontakt: {exc}",
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Unified API feil: {resp.text}",
        )

    try:
        data = resp.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Unified API returnerte ikke gyldig JSON."
        )

    # --- MATTEFILTER HER ---
    if isinstance(data, dict) and "response" in data:
        data["response"] = apply_math_filter(data["response"])

    return data


# ------------------------------------------------------------
# Endepunkter
# ------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "symbiose-query-api",
        "time": time.time(),
        "unified_api_url": UNIFIED_API_URL,
    }


@app.post("/unified_query")
def unified_query(body: UnifiedQueryRequest) -> Dict[str, Any]:
    return call_unified_backend(body.text)


@app.get("/search")
def search(q: str = Query(..., description="Fritekst-spørring (Msty-kompatibel)")) -> Dict[str, Any]:
    return call_unified_backend(q)
