#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC — Figshare Sync v3
=======================

Dette scriptet:
- Leser inn FIGSHARE_TOKEN fra miljøvariabel
- Henter ALLE Figshare-artikler fra din konto
- Lager stabil slug for hver artikkel (SEO safe, filesystem safe)
- Oppretter/oppdaterer mappe: figshare/<slug>/
- Skriver metadata.json for hver artikkel
- Skriver doi-map.json for hele figshare-mappen
- Loggfører alt til stdout (GitHub Actions)

Rører aldri andre deler av repoet.
"""

import os
import json
import requests
from pathlib import Path
from slugify import slugify


ROOT = Path(__file__).resolve().parents[1]
FIGSHARE_ROOT = ROOT / "figshare"


def log(msg: str):
    print(msg, flush=True)


# ------------------------------------------------------------
# API calls
# ------------------------------------------------------------

def get_figshare_articles(token: str):
    """Returnerer liste over dine artikler (kun metadata)."""
    headers = {"Authorization": f"token {token}"}
    url = "https://api.figshare.com/v2/account/articles"

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        log(f"[FAIL] Figshare API error: {r.text}")
        return []

    log("[OK] Figshare articles retrieved")
    return r.json()


def fetch_article_details(aid: int, token: str):
    """Henter full metadata for én artikkel."""
    headers = {"Authorization": f"token {token}"}
    url = f"https://api.figshare.com/v2/account/articles/{aid}"

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        log(f"[FAIL] Error fetching article {aid}: {r.text}")
        return None

    return r.json()


# ------------------------------------------------------------
# Metadata writing
# ------------------------------------------------------------

def update_local_metadata(article: dict):
    """Skriver metadata.json for én artikkel i figshare/<slug>/."""
    raw_title = article.get("title", "")
    slug = slugify(raw_title, lowercase=True)

    # sikre at figshare/<slug>/ eksisterer
    local_dir = FIGSHARE_ROOT / slug
    local_dir.mkdir(parents=True, exist_ok=True)

    md = {
        "id": article.get("id"),
        "title": raw_title,
        "slug": slug,
        "doi": article.get("doi"),
        "url": article.get("url_public_html"),
        "published": article.get("published_date"),
        "updated": article.get("modified_date"),
        "files": article.get("files", []),
        "version": article.get("version"),
        "status": article.get("status"),
        "defined_type": article.get("defined_type"),
        "description": article.get("description"),
    }

    with open(local_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(md, f, indent=2)

    log(f"[OK] Metadata updated for: {slug}")


def write_doi_map(articles: list):
    """Skriver samlet DOI-map."""
    FIGSHARE_ROOT.mkdir(exist_ok=True)
    doi_map = {}

    for a in articles:
        doi = a.get("doi")
        if not doi:
            continue

        slug = slugify(a.get("title", ""), lowercase=True)

        doi_map[doi] = {
            "id": a.get("id"),
            "slug": slug,
            "url": a.get("url_public_html"),
        }

    out = FIGSHARE_ROOT / "doi-map.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doi_map, f, indent=2)

    log("[OK] DOI map updated")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    log("=== FIGSHARE SYNC START ===")

    token = os.getenv("FIGSHARE_TOKEN")
    if not token:
        log("[FAIL] No FIGSHARE_TOKEN provided")
        return

    # hent alle artikler
    articles_basic = get_figshare_articles(token)
    if not articles_basic:
        log("[FAIL] No articles retrieved")
        return

    articles_full = []

    for a in articles_basic:
        aid = a.get("id")
        title = a.get("title", "")
        log(f"[SYNC] {aid}: {title}")

        full = fetch_article_details(aid, token)
        if full:
            articles_full.append(full)
            update_local_metadata(full)

    write_doi_map(articles_full)

    log("=== FIGSHARE SYNC COMPLETE ===")


if __name__ == "__main__":
    main()
