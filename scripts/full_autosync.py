#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EFC Full Autosync

Funksjoner:
1. Figshare: prøver å koble til (stopper ikke hvis det feiler)
2. Auto-clean: Fjerner feil JSON-LD i mapper
3. Auto-generate: Lager korrekt JSON-LD basert på mappenavn
4. Auto-index: Bygger global meta-index.json
"""

import os
import json
import requests

# ------------------------------------------------------------
# 1. Figshare-sync (ikke kritisk, påvirker ingenting)
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
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"[autosync] Figshare failed: HTTP {r.status_code}")
            return

        print(f"[autosync] Figshare OK, {len(r.json())} articles available.")
    except Exception as e:
        print(f"[autosync] Figshare connection error: {e}")

fetch_figshare_articles()


# ------------------------------------------------------------
# Auto JSON-LD system
# ------------------------------------------------------------

print("[autosync] Starting JSON-LD auto-clean + auto-generation...")

IGNORED_DIR_PREFIXES = (
    "./.",
    "./.git",
    "./.github",
    "./venv",
    "./.venv",
)

IGNORED_DOC_NAMES = {"readme.md", "index.md"}

AUTHOR_NAME = "Morten Magnusson"
AUTHOR_ORCID = "https://orcid.org/0009-0002-4860-5095"


def slug_from_dirpath(path: str) -> str:
    """Return stable ID (folder name)."""
    clean = path.strip("./")
    parts = clean.split("/")
    return parts[-1] if parts else clean


def layer_from_dirpath(path: str) -> str:
    """Top-level folder used as 'layer'."""
    clean = path.strip("./")
    parts = clean.split("/")
    return parts[0] if parts else ""


def build_jsonld(dirpath: str, docs: list[str]) -> str:
    """
    Lag JSON-LD basert på mappenavn (ikke dokumentnavn).
    Returnerer filnavn på jsonld.
    """
    node_id = slug_from_dirpath(dirpath)
    layer = layer_from_dirpath(dirpath)

    md_docs = [d for d in docs if d.lower().endswith(".md")]
    pdf_docs = [d for d in docs if d.lower().endswith(".pdf")]

    # Velg dokument for description
    doc = md_docs[0] if md_docs else (pdf_docs[0] if pdf_docs else docs[0])

    description = ""
    if doc.lower().endswith(".md"):
        try:
            with open(os.path.join(dirpath, doc), "r", encoding="utf-8") as f:
                raw = f.read()
            description = raw[:400].replace("\n", " ")
        except Exception as e:
            print(f"[autosync] Warning: cannot read {doc}: {e}")

    jsonld = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": node_id.replace("_", " ").replace("-", " "),
        "identifier": node_id,
        "layer": layer,
        "description": description,
        "version": "1.0",
        "author": {
            "@type": "Person",
            "name": AUTHOR_NAME,
            "identifier": AUTHOR_ORCID
        }
    }

    outfile = os.path.join(dirpath, f"{node_id}.jsonld")

    with open(outfile, "w", encoding="utf-8") as fp:
        json.dump(jsonld, fp, indent=2)

    print(f"[autosync] Created JSON-LD: {outfile}")
    return outfile


# ------------------------------------------------------------
# 2. CLEAN + GENERATE JSON-LD
# ------------------------------------------------------------

for dirpath, dirnames, filenames in os.walk("."):
    if any(dirpath.startswith(pref) for pref in IGNORED_DIR_PREFIXES):
        continue
    if dirpath == ".":
        continue

    lower_files = [f.lower() for f in filenames]

    docs = [
        f for f in filenames
        if (f.lower().endswith(".md") or f.lower().endswith(".pdf"))
        and f.lower() not in IGNORED_DOC_NAMES
    ]

    jsonlds = [f for f in filenames if f.lower().endswith(".jsonld")]

    # Hvis det finnes jsonld, men navnet er feil -> auto-clean
    if jsonlds:
        expected = f"{slug_from_dirpath(dirpath)}.jsonld"
        for js in jsonlds:
            if js != expected:
                try:
                    os.remove(os.path.join(dirpath, js))
                    print(f"[autosync] Removed invalid JSON-LD: {dirpath}/{js}")
                except Exception as e:
                    print(f"[autosync] Could not remove {js}: {e}")
        # Re-scan etter cleaning
        jsonlds = [f for f in os.listdir(dirpath) if f.endswith(".jsonld")]

    # Generer kun hvis det mangler jsonld og det finnes dokumenter
    if docs and not jsonlds:
        build_jsonld(dirpath, docs)


# ------------------------------------------------------------
# 3. Build meta-index.json
# ------------------------------------------------------------

print("[autosync] Building meta-index.json...")

nodes = []

for dirpath, _, filenames in os.walk("."):
    if any(dirpath.startswith(pref) for pref in IGNORED_DIR_PREFIXES):
        continue

    for f in filenames:
        if not f.lower().endswith(".jsonld"):
            continue

        full_path = os.path.join(dirpath, f).replace("./", "")

        try:
            data = json.load(open(os.path.join(dirpath, f), "r", encoding="utf-8"))
            identifier = data.get("identifier", os.path.splitext(f)[0])
            node_type = data.get("@type", "CreativeWork")
        except:
            identifier = os.path.splitext(f)[0]
            node_type = "CreativeWork"

        nodes.append({
            "id": identifier,
            "path": full_path,
            "type": node_type
        })

meta_index = {
    "version": "1.0",
    "nodes": nodes
}

with open("meta-index.json", "w", encoding="utf-8") as fp:
    json.dump(meta_index, fp, indent=2)

print(f"[autosync] meta-index.json built with {len(nodes)} nodes.")
for n in nodes:
    print("  →", n["id"], ":", n["path"])

print("[autosync] Full autosync completed successfully.")
