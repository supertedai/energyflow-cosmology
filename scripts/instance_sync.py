#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Production Version
==================================

Funksjoner:
- Rydder bort feilplasserte JSON-LD
- Genererer manglende JSON-LD i whitelisted nodedirs
- Rebuilder meta-index.json
- Commit + push hvis noe er endret

Dette er "light maintenance"-laget i EFC.
Kjører ofte. Lager aldri kaos. Gir rene noder.

"""

import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# --------------------------- Konfig ---------------------------

NODE_DIR_PREFIXES = [
    "schema",
    "meta",
    "meta-graph",
    "api",
    "docs",
    "figshare",
    "src/efc",
    "data/sparc",
    "data/processed",
]

HARD_IGNORES = [
    ".git", ".github", ".venv", "venv",
    "__pycache__", ".idea", ".vscode",
    "output", "notebooks", "scripts",
    "data/raw", "data/archive",
]

AUTHOR = {
    "@type": "Person",
    "name": "Morten Magnusson",
    "identifier": "https://orcid.org/0009-0002-4860-5095",
}


# ---------------------- Utility Functions ----------------------

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass


def is_under_prefix(rel_path: str, prefixes) -> bool:
    for p in prefixes:
        if rel_path == p or rel_path.startswith(p + "/"):
            return True
    return False


def dir_slug(rel_path: str) -> str:
    return os.path.basename(rel_path) if rel_path and rel_path != "." else ""


# ---------------------------- Cleanup ----------------------------

def cleanup_stray_jsonld():
    safe_print("[instance_sync] Cleanup: removing stray JSON-LD...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        if rel == ".":
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    path.unlink(missing_ok=True)
                    safe_print(f"[instance_sync] Removed root JSON-LD: {path}")
            continue

        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    path.unlink(missing_ok=True)
                    safe_print(f"[instance_sync] Removed stray JSON-LD: {path}")


# ----------------------- JSON-LD Generation -----------------------

def generate_jsonld_for_missing_nodes():
    safe_print("[instance_sync] Generating missing JSON-LD in whitelisted dirs...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)
        if rel == ".":
            continue

        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        slug = dir_slug(rel)
        if not slug:
            continue

        expected = f"{slug}.jsonld"

        if expected in files:
            continue

        jsonld_path = Path(root) / expected
        data = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "identifier": slug,
            "name": slug.replace("_", " ").replace("-", " "),
            "layer": rel.split(os.sep)[0],
            "author": AUTHOR,
            "version": "1.0",
        }

        with jsonld_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        safe_print(f"[instance_sync] Created JSON-LD: {jsonld_path}")


# ------------------------- Meta-index -------------------------

def rebuild_meta_index():
    safe_print("[instance_sync] Building meta-index.json...")

    nodes = []

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        for f in files:
            if not f.endswith(".jsonld"):
                continue

            path = Path(root) / f
            rel_path = os.path.relpath(path, ROOT).replace(os.sep, "/")

            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                identifier = data.get("identifier")
                node_type = data.get("@type", "CreativeWork")
            except Exception:
                identifier = f.replace(".jsonld", "")
                node_type = "CreativeWork"

            nodes.append({
                "id": identifier,
                "path": rel_path,
                "type": node_type,
            })

    meta_path = ROOT / "meta-index.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "nodes": nodes}, f, indent=2)

    safe_print(f"[instance_sync] meta-index.json updated with {len(nodes)} nodes.")


# ---------------------- Git Commit + Push ----------------------

def git_status():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def commit_and_push():
    status = git_status()
    if not status:
        safe_print("[instance_sync] No changes to commit.")
        return

    safe_print("[instance_sync] Changes detected:")
    safe_print(status)

    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    msg = "Instance sync auto-update [skip ci]"
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT)

    safe_print("[instance_sync] Changes pushed successfully.")


# ------------------------------ MAIN ------------------------------

def main():
    safe_print("[instance_sync] Starting instance sync (clean + generate + push)...")

    cleanup_stray_jsonld()
    generate_jsonld_for_missing_nodes()
    rebuild_meta_index()
    commit_and_push()

    safe_print("[instance_sync] Done.")


if __name__ == "__main__":
    main()
