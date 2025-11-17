#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EFC Full Autosync
- Fetches Figshare articles (if token exists)
- Generates JSON-LD nodes for all documents
- Builds global meta-index.json
"""

import os
import json
import requests

# ------------------------------------------------------------
# 1. Optional: Sync Figshare content
# ------------------------------------------------------------

FIGSHARE_TOKEN = os.environ.get("FIGSHARE_TOKEN")

def fetch_figshare_articles():
    if not FIGSHARE_TOKEN:
        print("[autosync] No FIGSHARE_TOKEN found – skipping Figshare sync.")
        return
    
    print("[autosync] Fetching Figshare articles...")
    headers = {"Authorization": f"token {FIGSHARE_TOKEN}"}
    url = "https://api.figshare.com/v2/account/articles"

    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"[autosync] Figshare failed: HTTP {r.status_code}")
            return

        articles = r.json()
        print(f"[autosync] Found {len(articles)} articles.")
    except Exception as e:
        print(f"[autosync] Figshare connection error: {e}")

fetch_figshare_articles()


# ------------------------------------------------------------
# 2. Automatic JSON-LD Generator
# ------------------------------------------------------------

print("[autosync] Generating JSON-LD nodes where missing...")

def build_jsonld_for_directory(dirpath, doc):
    name = os.path.splitext(doc)[0]
    layer = dirpath.split("/")[0]

    description = ""
    md_path = os.path.join(dirpath, doc)

    if doc.endswith(".md"):
        try:
            raw = open(md_path).read()
            description = raw[:400].replace("\n", " ")
        except:
            pass

    jsonld = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": name.replace("_", " ").title(),
        "identifier": name,
        "layer": layer,
        "description": description,
        "version": "1.0",
        "author": {
            "@type": "Person",
            "name": "Morten Magnusson",
            "identifier": "https://orcid.org/0009-0002-4860-5095"
        }
    }

    outfile = os.path.join(dirpath, f"{name}.jsonld")
    with open(outfile, "w") as fp:
        json.dump(jsonld, fp, indent=2)

    print(f"[autosync] Created JSON-LD: {outfile}")


# Walk repository and auto-build JSON-LD nodes
for dirpath, dirnames, filenames in os.walk("."):
    if dirpath.startswith("./.") or dirpath == ".":
        continue

    docs = [f for f in filenames if f.endswith((".md", ".pdf"))]
    jsonlds = [f for f in filenames if f.endswith(".jsonld")]

    if docs and not jsonlds:
        build_jsonld_for_directory(dirpath, docs[0])


# ------------------------------------------------------------
# 3. Build the global meta-index.json
# ------------------------------------------------------------

print("[autosync] Building meta-index.json...")

nodes = []

for dirpath, _, filenames in os.walk("."):
    for f in filenames:
        if f.endswith(".jsonld"):
            full_path = os.path.join(dirpath, f).replace("./", "")
            node_id = os.path.splitext(f)[0]

            nodes.append({
                "id": node_id,
                "path": full_path,
                "type": "CreativeWork"
            })

meta_index = {
    "version": "1.0",
    "nodes": nodes
}

with open("meta-index.json", "w") as fp:
    json.dump(meta_index, fp, indent=2)

print(f"[autosync] meta-index.json built with {len(nodes)} nodes.")
for n in nodes:
    print("  -", n["id"])

print("[autosync] Full autosync completed successfully.")
