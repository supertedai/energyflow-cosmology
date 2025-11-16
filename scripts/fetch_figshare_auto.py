#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys
import os
from datetime import datetime

FIGSHARE_USER_ID = 20477774
OUTPUT_DIR = "downloads"        # mappe for å lagre nedlastinger
LOG_FILE = "fetch_figshare_auto.log"

def log(msg):
    ts = datetime.utcnow().isoformat()
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\\n")

def get_articles(user_id):
    url = f"https://api.figshare.com/v2/authors/{user_id}/articles"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def pick_latest(articles):
    # Antar at objektene har 'published_date' eller bruker id
    sorted_list = sorted(
        articles,
        key=lambda x: x.get("published_date", ""),
        reverse=True
    )
    if not sorted_list:
        raise RuntimeError("Ingen artikler funnet for bruker.")
    return sorted_list[0]

def download_article(article_id):
    url = f"https://api.figshare.com/v2/articles/{article_id}/files"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    files = r.json()
    for f in files:
        download_url = f.get("download_url")
        name = f.get("name")
        if download_url and name:
            outpath = os.path.join(OUTPUT_DIR, name)
            log(f"Downloader fil: {name}")
            with requests.get(download_url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with open(outpath, "wb") as of:
                    for chunk in resp.iter_content(chunk_size=8192):
                        of.write(chunk)
            log(f"Ferdig: {outpath}")

def main():
    try:
        log("Starter henting fra Figshare")
        articles = get_articles(FIGSHARE_USER_ID)
        latest = pick_latest(articles)
        log(f"Nyeste artikkel funnet: id={latest['id']} tittel=\"{latest.get('title')}\"")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        download_article(latest['id'])
        log("Fullført off-Line prosess")
    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
