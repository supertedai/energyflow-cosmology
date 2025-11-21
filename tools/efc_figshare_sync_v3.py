#!/usr/bin/env python3
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from slugify import slugify

REPORT = "figshare_sync_report.txt"

def log(msg):
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def get_figshare_articles(token):
    headers = {"Authorization": f"token {token}"}
    url = "https://api.figshare.com/v2/account/articles"
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        log(f"[FAIL] Figshare API error: {r.text}")
        return []

    log("[OK] Figshare articles retrieved")
    return r.json()

def sync_article_metadata(article, token):
    aid = article["id"]
    url = f"https://api.figshare.com/v2/account/articles/{aid}"
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        log(f"[FAIL] Error fetching article {aid}: {r.text}")
        return None

    data = r.json()
    title = data.get("title", "")
    log(f"[SYNC] {aid}: {title}")
    return data

def write_doi_map(articles):
    path = Path("figshare/doi-map.json")
    path.parent.mkdir(exist_ok=True)
    doi_map = {}

    for a in articles:
        doi = a.get("doi")
        if doi:
            doi_map[doi] = {
                "article_id": a["id"],
                "url": a.get("url_public_html", "")
            }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doi_map, f, indent=2)
    log("[OK] DOI map updated")

def update_local_metadata(article):
    raw_title = article.get("title", "")
    slug = slugify(raw_title, lowercase=True)

    local_dir = Path("figshare") / slug
    local_dir.mkdir(parents=True, exist_ok=True)

    md = {
        "id": article["id"],
        "title": raw_title,
        "slug": slug,
        "doi": article.get("doi"),
        "url": article.get("url_public_html"),
        "published": article.get("published_date"),
        "updated": article.get("modified_date"),
        "files": article.get("files", [])
    }

    with open(local_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(md, f, indent=2)

    log(f"[OK] Metadata updated for: {slug}")

def main():
    if os.path.exists(REPORT):
        os.remove(REPORT)

    token = os.getenv("FIGSHARE_TOKEN")
    if not token:
        log("[FAIL] No FIGSHARE_TOKEN provided")
        return

    log("=== FIGSHARE SYNC START ===")

    articles = get_figshare_articles(token)
    if not articles:
        log("[FAIL] No articles retrieved")
        return

    full_data = []
    for a in articles:
        meta = sync_article_metadata(a, token)
        if meta:
            full_data.append(meta)
            update_local_metadata(meta)

    write_doi_map(full_data)

    log("=== FIGSHARE SYNC COMPLETE ===")

if __name__ == "__main__":
    main()
