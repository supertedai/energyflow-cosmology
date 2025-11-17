#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Light Maintenance Layer
=======================================

Funksjon:
- Rydder repo for feil/rot
- Normaliserer mappenavn
- Genererer JSON-LD der det mangler
- Bygger meta-index.json
- ALDRI committer
- ALDRI stopper pipeline
- ALDRI krever tokens

Dette scriptet er "grunnpusten" i systemet.
Kjører automatisk hver time via instance_sync.yml
"""

import os
import json

# --- 0. Hjelpefunksjoner ------------------------------------------------------

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass


def normalize_folder_name(path):
    base = os.path.basename(path)
    clean = base.strip()
    if clean != base:
        new_path = os.path.join(os.path.dirname(path), clean)
        try:
            os.rename(path, new_path)
            safe_print(f"[instance_sync] Renamed folder: '{path}' -> '{new_path}'")
            return new_path
        except Exception as e:
            safe_print(f"[instance_sync] Could not rename {path}: {e}")
    return path


def slug(path):
    return os.path.basename(path.strip("./")).strip()


def layer(path):
    clean = path.strip("./")
    parts = clean.split("/")
    return parts[0] if parts else ""


# --- 1. Auto-clean + Normalize ------------------------------------------------

safe_print("[instance_sync] Starting auto-clean...")

IGNORED_PREFIX = ("./.", "./.git", "./.github", "./venv", "./.venv")

for root, dirs, files in os.walk(".", topdown=True):
    # skip system folders
    if any(root.startswith(p) for p in IGNORED_PREFIX):
        continue

    # normalize subfolder names
    for i, d in enumerate(dirs):
        full = os.path.join(root, d)
        new = normalize_folder_name(full)
        dirs[i] = os.path.basename(new)


# --- 2. Auto-generate JSON-LD -------------------------------------------------

safe_print("[instance_sync] Generating missing JSON-LD...")

AUTHOR = {
    "@type": "Person",
    "name": "Morten Magnusson",
    "identifier": "https://orcid.org/0009-0002-4860-5095"
}

def generate_jsonld(dirpath, docs):
    node_id = slug(dirpath)
    out = os.path.join(dirpath, f"{node_id}.jsonld")

    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "identifier": node_id,
        "layer": layer(dirpath),
        "name": node_id.replace("_", " ").replace("-", " "),
        "author": AUTHOR,
        "version": "1.0"
    }

    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        safe_print(f"[instance_sync] Created JSON-LD: {out}")
    except Exception as e:
        safe_print(f"[instance_sync] Error writing {out}: {e}")


for root, dirs, files in os.walk(".", topdown=True):
    if any(root.startswith(p) for p in IGNORED_PREFIX):
        continue

    md_or_pdf = [f for f in files if f.lower().endswith((".md", ".pdf"))]
    expected = f"{slug(root)}.jsonld"
    have_jsonld = expected in files

    if md_or_pdf and not have_jsonld:
        generate_jsonld(root, md_or_pdf)


# --- 3. Build meta-index.json -------------------------------------------------

safe_print("[instance_sync] Building meta-index.json...")

nodes = []

for dirpath, _, files in os.walk("."):
    if any(dirpath.startswith(p) for p in IGNORED_PREFIX):
        continue
    for f in files:
        if f.endswith(".jsonld"):
            try:
                data = json.load(open(os.path.join(dirpath, f), "r", encoding="utf-8"))
                ident = data.get("identifier", f.replace(".jsonld", ""))
            except Exception:
                ident = f.replace(".jsonld", "")
            nodes.append({
                "id": ident,
                "path": os.path.join(dirpath, f).replace("./", "")
            })

try:
    with open("meta-index.json", "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes}, f, indent=2)
    safe_print("[instance_sync] meta-index.json updated.")
except Exception as e:
    safe_print(f"[instance_sync] Failed writing meta-index.json: {e}")

safe_print("[instance_sync] Done.")
