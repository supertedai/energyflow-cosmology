#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests

FIGSHARE_TOKEN = os.environ.get("FIGSHARE_TOKEN")

def fetch_figshare_articles():
    if not FIGSHARE_TOKEN:
        print("[autosync] No FIGSHARE_TOKEN found – skipping Figshare sync.")
        return
    
    print("[autosync] Fetching Figshare articles...")
    headers = {"Authorization": f"token {FIGSHARE_TOKEN}"}
    url = "https://api.figshare.com/v2/account/articles"
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print(f"[autosync] Figshare failed: HTTP {r.status_code}")
        return

    print(f"[autosync] Found {len(r.json())} articles.")

fetch_figshare_articles()

print("[autosync] Scanning repository for .jsonld files...")

nodes = []
for dirpath, _, filenames in os.walk("."):
    for f in filenames:
        if f.endswith(".jsonld"):
            path = os.path.join(dirpath, f).replace("./", "")
            nodes.append({
                "id": os.path.splitext(f)[0],
                "path": path,
                "type": "CreativeWork"
            })

with open("meta-index.json", "w") as fp:
    json.dump({ "version": "1.0", "nodes": nodes }, fp, indent=2)

print(f"[autosync] meta-index.json built with {len(nodes)} nodes.")
for n in nodes:
    print("  -", n["id"])

print("[autosync] Full autosync completed successfully.")
