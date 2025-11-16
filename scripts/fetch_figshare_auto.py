#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import sys
from datetime import datetime

PROFILE_URL = "https://figshare.com/authors/Morten_Magnusson/20477774"

def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}")

def fetch_profile_html():
    log("Henter HTML fra Figshare-profil…")
    r = requests.get(PROFILE_URL, timeout=20, headers={
        "User-Agent": "Mozilla/5.0"
    })
    r.raise_for_status()
    return r.text

def extract_article_ids(html):
    """
    Finne alle artikkel-IDer fra profile HTML.
    Pattern: /articles/.../<id>
    """
    pattern = r"/articles/[A-Za-z0-9_\-]+/(\d+)"
    found = re.findall(pattern, html)
    return list(set(found))  # fjern duplikater

def pick_latest(article_ids):
    if not article_ids:
        raise RuntimeError("Fant ingen artikkel-IDer på Figshare-profilen.")
    article_ids = [int(x) for x in article_ids]
    return max(article_ids)

def main():
    try:
        html = fetch_profile_html()
        ids = extract_article_ids(html)
        log(f"Fant ID-er: {ids}")

        latest = pick_latest(ids)
        log(f"Siste Figshare-artikkel: {latest}")

    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
