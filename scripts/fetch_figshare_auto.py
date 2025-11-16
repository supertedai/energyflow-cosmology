#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime

API_URL = "https://api.figshare.com/v2/account/articles"


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}")


# ---------------------------------------------------------
# Hent artikler fra Figshare API
# ---------------------------------------------------------
def get_articles():
    token = os.environ.get("FIGSHARE_TOKEN")
    if not token:
        raise RuntimeError("FIGSHARE_TOKEN er ikke satt i miljøvariabler")

    headers = {
        "Authorization": f"token {token}",
        "User-Agent": "Mozilla/5.0"
    }

    log("Henter liste over artikler via Figshare API…")
    r = requests.get(API_URL, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------
# Finn nyeste artikkel (safe sort)
# ---------------------------------------------------------
def pick_latest(articles):
    if not articles:
        raise RuntimeError("Ingen artikler returnert fra Figshare API")

    def safe_date(a):
        d = a.get("published_date")
        if isinstance(d, str) and len(d) > 0:
            return d
        return "0000-00-00"

    sorted_list = sorted(
        articles,
        key=safe_date,
        reverse=True
    )
    return sorted_list[0]


# ---------------------------------------------------------
# Lagring av metadata
# ---------------------------------------------------------
def save_metadata(latest):
    os.makedirs("figshare", exist_ok=True)

    out_path = "figshare/latest.json"
    with open(out_path, "w") as f:
        json.dump(latest, f, indent=2)

    log(f"Lagret: {out_path}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    try:
        articles = get_articles()
        latest = pick_latest(articles)

        log("------ Nyeste Figshare-artikkel funnet ------")
        log(f"ID: {latest['id']}")
        log(f"Tittel: {latest.get('title', 'Ukjent')}")
        log(f"Publiseringsdato: {latest.get('published_date', 'Ingen dato')}")
        log("------------------------------------------------")

        save_metadata(latest)

    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
