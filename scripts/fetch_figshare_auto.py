#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import requests
from datetime import datetime

API_URL = "https://api.figshare.com/v2/account/articles"

def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}")

def get_articles():
    token = os.environ.get("FIGSHARE_TOKEN")
    if not token:
        raise RuntimeError("FIGSHARE_TOKEN er ikke satt i miljøvariabler")

    headers = {
        "Authorization": f"token {token}",
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(API_URL, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def pick_latest(articles):
    if not articles:
        raise RuntimeError("Ingen artikler returnert fra Figshare API")
    # published_date finnes alltid
    sorted_list = sorted(articles, key=lambda x: x.get("published_date", ""), reverse=True)
    return sorted_list[0]

def main():
    try:
        log("Henter liste over artikler via Figshare API…")
        articles = get_articles()
        latest = pick_latest(articles)
        log(f"Siste artikkel-ID: {latest['id']}")
        log(f"Tittel: {latest.get('title', 'ukjent')}")

    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
