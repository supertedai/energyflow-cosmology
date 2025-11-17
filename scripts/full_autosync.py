#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EFC Full Autosync (self-healing version)

Funksjoner:
1) Figshare sync (best effort)
2) Auto-CLEAN:
   - fjerner feil/legacy JSON-LD
   - retter mappenavn med whitespace
   - rydder ugyldige filer
3) Auto-GENERATE JSON-LD
4) Auto-BUILD meta-index.json
"""

import os
import json
import requests
import shutil

# ------------------------------------------------------------
# 0. Hjelpefunksjoner
# ------------------------------------------------------------

def normalize_folder_name(path):
    """Fjerner leading/trailing whitespace fra mappenavn."""
    base = os.path.basename(path)
    clean = base.strip()
    if clean != base:
        parent = os.path.dirname(path)
        new_path = os.path.join(parent, clean)
        try:
            os.rename(path, new_path)
            print(f"[autosync] Renamed folder: '{path}' -> '{new_path}'")
            return new_path
        except Exception as e:
            print(f"[autosync] Could not rename: {path}: {e}")
    return path


def slug_from_dirpath(path: str) -> str:
    return os.path.basename(path.strip("./")).strip()


def layer_from_dirpath(path: str) -> str:
    clean = path.strip("./")
    parts = clean.split("/")
    return parts[0] if parts else ""


# ------------------------------------------------------------
# 1. Figshare sync
# ------------------------------------------------------------

FIGSHARE_TOKEN = os.environ.get("FIGSHARE_TOKEN")

def fetch_figshare():
    if not FIGSHARE_TOKEN:
        print("[autosync] No FIGSHARE_TOKEN found.")
        return

    print("[autosync] Figshare: trying sync...")
    try:
        r = requests.get(
            "https://api.figshare.com/v2/account/articles",
            headers={"Authorization": f"token {FIGSHARE_TOKEN}"},
            timeout=10
        )
        if r.status_code != 200:
            print(f"[autosync] Figshare failed: HTTP {r.status_code}")
            return
        print(f"[autosync] Figshare OK, {len(r.json())} articles.")
    except Exception as e:
        print(f"[autosync] Figshare connection error: {e}")

fetch_figshare()


# ------------------------------------------------------------
# 2. AUTO-CLEAN + AUTO-GENERATE JSON-LD
# ------------------------------------------------------------

print("[autosync] Auto-clean + auto-generate JSON-LD startet...")

IGNORED_PREFIX = ("./.", "./.git", "./.github", "./venv", "./.venv")
IGNORED_DOCS = {"readme.md", "index.md"}

AUTHOR = {
    "@type": "Person",
    "name": "Morten Magnusson",
    "identifier": "https://orcid.org/0009-0002-4860-5095"
}


def generate_jsonld(dirpath, docs):
    node_id = slug_from_dirpath(dirpath)
    layer = layer_from_dirpath(dirpath)

    md_docs = [d for d in docs if d.lower().endswith(".md")]
    pdf_docs = [d for d in docs if d.lower().endswith(".pdf")]

    doc = md_docs[0] if md_docs else (pdf_docs[0] if pdf_docs else docs[0])

    description = ""
    if doc.lower().endswith(".md"):
        try:
            with open(os.path.join(dirpath, doc), "r", encoding="utf-8") as f:
                description = f.read()[:400].replace("\n", " ")
        except:
            pass

    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "identifier": node_id,
        "name": node_id.replace("_", " ").replace("-", " "),
        "layer": layer,
        "description": description,
        "version": "1.0",
        "author": AUTHOR
    }

    outfile = os.path.join(dirpath, f"{node_id}.jsonld")
    with open(outfile, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)

    print(f"[autosync] Created JSON-LD: {outfile}")


# Rydd + generer
for root, dirs, files in os.walk(".", topdown=True):

    # Rens mappenavn
    for i, d in enumerate(dirs):
        full = os.path.join(root, d)
        new_path = normalize_folder_name(full)
        if new_path != full:
            # oppdater i dirs så walk ikke mister path
            dirs[i] = os.path.basename(new_path)

    if any(root.startswith(p) for p in IGNORED_PREFIX):
        continue
    if root == ".":
        continue

    files_lower = [f.lower() for f in files]

    docs = [
        f for f in files
        if (f.lower().endswith(".md") or f.lower().endswith(".pdf"))
        and f.lower() not in IGNORED_DOCS
    ]

    jsonlds = [f for f in files if f.lower().endswith(".jsonld")]

    # forventet filnavn
    expected = slug_from_dirpath(root) + ".jsonld"

    # slett feil/legacy jsonld
    for js in jsonlds:
        if js != expected:
            try:
                os.remove(os.path.join(root, js))
                print(f"[autosync] Removed invalid JSON-LD: {root}/{js}")
            except Exception as e:
                print(f"[autosync] Could not delete {root}/{js}: {e}")

    # re-scan
    jsonlds = [f for f in os.listdir(root) if f.endswith(".jsonld")]

    if docs and not jsonlds:
        generate_jsonld(root, docs)


# ------------------------------------------------------------
# 3. Build meta-index.json
# ------------------------------------------------------------

print("[autosync] Building meta-index.json...")

nodes = []

for dirpath, _, filenames in os.walk("."):
    if any(dirpath.startswith(p) for p in IGNORED_PREFIX):
        continue
    for f in filenames:
        if not f.lower().endswith(".jsonld"):
            continue

        path = os.path.join(dirpath, f).replace("./", "")

        try:
            data = json.load(open(os.path.join(dirpath, f), "r", encoding="utf-8"))
            identifier = data.get("identifier", os.path.splitext(f)[0])
            node_type = data.get("@type", "CreativeWork")
        except:
            identifier = os.path.splitext(f)[0]
            node_type = "CreativeWork"

        nodes.append({
            "id": identifier,
            "path": path,
            "type": node_type
        })

with open("meta-index.json", "w", encoding="utf-8") as fp:
    json.dump({"version": "1.0", "nodes": nodes}, fp, indent=2)

print(f"[autosync] meta-index.json built with {len(nodes)} nodes.")
for n in nodes:
    print(f"  → {n['id']} : {n['path']}")

print("[autosync] Full autosync completed successfully.")
