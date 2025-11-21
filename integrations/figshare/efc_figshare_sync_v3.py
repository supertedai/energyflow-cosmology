#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Figshare Sync v3 — EFC Stable Edition
=====================================

Dette scriptet:
- Henter ALLE Figshare-artikler i kontoen
- Lagrer dem i /figshare/<slug>/
- Oppdaterer DOI-map i /figshare/doi-map.json
- Er 100% kompatibel med Instance Sync v4
"""

import os
import json
import requests
from pathlib import Path
from slugify import slugify
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
FIGSHARE_ROOT = ROOT / "figshare"
REPORT = ROOT / "figshare_sync_report.txt"

def log(msg):
    with REPORT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def get_figshare_articles(token):
    headers = {"Authorization": f"token {token}"}
    r = requests.get("https://api.figshare.com/v2/account/articles", headers=headers)
    if r.status_code != 200:
        log(f"[FAIL] {r.text}")
        return []
    log("[OK] Figshare articles retrieved")
    return r.json()

def fetch_article_details(article_id, token):
    headers = {"Authorization": f"token {token}"}
    r = requests.get(f"https://api.figshare.com/v2/account/articles/{article_id}", headers=headers)
    if r.status_code != 200:
        log(f"[FAIL] Article fetch error: {article_id}")
        return None
    return r.json()

def update_local_metadata(article):
    slug = slugify(article["title"])
    local_dir = FIGSHARE_ROOT / slug
    local_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "id": article["id"],
        "title": article.get("title"),
        "slug": slug,
        "doi": article.get("doi"),
        "url": article.get("url_public_html"),
        "published": article.get("published_date"),
        "updated": article.get("modified_date"),
        "files": article.get("files", []),
    }

    with (local_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    log(f"[OK] Metadata updated for: {slug}")

def update_doi_map(articles):
    doi_map = {}
    for a in articles:
        doi = a.get("doi")
        if doi:
            doi_map[doi] = {
                "id": a["id"],
                "url": a.get("url_public_html"),
            }

    (FIGSHARE_ROOT/"doi-map.json").write_text(
        json.dumps(doi_map, indent=2), encoding="utf-8"
    )

    log("[OK] DOI map updated")

def main():
    if REPORT.exists():
        REPORT.unlink()

    token = os.getenv("FIGSHARE_TOKEN")
    if not token:
        log("[FAIL] FIGSHARE_TOKEN missing")
        return

    log("=== FIGSHARE SYNC START ===")

    articles = get_figshare_articles(token)
    full_articles = []

    for a in articles:
        full = fetch_article_details(a["id"], token)
        if not full:
            continue
        full_articles.append(full)
        update_local_metadata(full)

    update_doi_map(full_articles)

    log("=== FIGSHARE SYNC COMPLETE ===")

if __name__ == "__main__":
    main()
