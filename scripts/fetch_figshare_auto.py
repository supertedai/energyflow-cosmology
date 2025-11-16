#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime

API_URL = "https://api.figshare.com/v2/account/articles"

def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}")


# --------------------------
# Henter artikler fra Figshare
# --------------------------
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


# --------------------------
# Velger nyeste artikkel
# --------------------------
def pick_latest(articles):
    def safe_date(a):
        d = a.get("published_date")
        return d if isinstance(d, str) and len(d) > 0 else "0000-00-00"

    sorted_list = sorted(articles, key=safe_date, reverse=True)
    return sorted_list[0]


# --------------------------
# Lagre Figshare metadata
# --------------------------
def save_latest_json(latest):
    os.makedirs("figshare", exist_ok=True)
    out_path = "figshare/latest.json"
    with open(out_path, "w") as f:
        json.dump(latest, f, indent=2)
    log(f"Lagret: {out_path}")


# --------------------------
# Oppdaterer API v1
# --------------------------
def update_api_meta(latest):
    meta_path = "api/v1/meta.json"

    # Les eksisterende meta
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
    else:
        meta = {}

    # Oppdater Figshare-seksjon
    meta["figshare"] = {
        "id": latest.get("id"),
        "title": latest.get("title"),
        "published_date": latest.get("published_date"),
        "url": latest.get("url"),
        "doi": latest.get("doi"),
        "resource_id": latest.get("resource_id"),
        "resource_doi": latest.get("resource_doi")
    }

    # Lagre
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    log(f"Oppdatert: {meta_path}")


# --------------------------
# Main
# --------------------------
def main():
    try:
        articles = get_articles()
        latest = pick_latest(articles)

        log("------ Nyeste Figshare-artikkel ------")
        log(f"ID: {latest['id']}")
        log(f"Tittel: {latest.get('title')}")
        log(f"Publisert: {latest.get('published_date')}")
        log("--------------------------------------")

        save_latest_json(latest)
        update_api_meta(latest)

    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
