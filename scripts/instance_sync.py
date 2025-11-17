#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Production Version (with Git push)
==================================================

Gjør:
- Fjerner feilplasserte JSON-LD
- Genererer manglende JSON-LD i whitelisted nodedirs
- Rebuilder meta-index.json
- Commit + push hvis noe er endret

Kjøres typisk via .github/workflows/instance_sync.yml
"""

import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --------------------------- Konfig ---------------------------

# Mapper som kan inneholde kunnskapsnoder (JSON-LD)
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

# Mapper vi aldri vil behandle som noder
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


# ---------------------- Utility ----------------------

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass


def run(cmd, cwd=None, check=True):
    """Kjør kommando med enkel feilhåndtering."""
    safe_print(f"[instance_sync] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or ROOT, text=True)
    if check and result.returncode != 0:
        safe_print(f"[instance_sync] Command failed with code {result.returncode}")
        raise SystemExit(result.returncode)
    return result


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

        # Fjern JSON-LD i root
        if rel == ".":
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    path.unlink(missing_ok=True)
                    safe_print(f"[instance_sync] Removed root JSON-LD: {path}")
            continue

        # Ignorer hard-ignores
        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        # Hvis ikke under whitelisted node-prefix → slett JSON-LD
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
            continue  # allerede JSON-LD her

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
        text=True,
    )
    return result.stdout.strip()


def configure_git_user():
    """Konfigurer git-bruker for Actions og lokal kjøring."""
    run(["git", "config", "user.name", "github-actions"], check=False)
    run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=False)


def commit_and_push():
    status = git_status()

    safe_print("[instance_sync] Git status (porcelain):")
    safe_print(status if status else "(clean)")

    if not status:
        safe_print("[instance_sync] No changes to commit.")
        return

    configure_git_user()

    run(["git", "add", "-A"])
    msg = "Instance sync auto-update [skip ci]"
    run(["git", "commit", "-m", msg])

    # push bruker GITHUB_TOKEN i Actions, eller dine lokale credentials
    run(["git", "push"])
    safe_print("[instance_sync] Changes pushed successfully.")


# ------------------------------ MAIN ------------------------------

def main():
    safe_print("[instance_sync] Starting instance sync (clean + generate + meta + push)...")

    cleanup_stray_jsonld()
    generate_jsonld_for_missing_nodes()
    rebuild_meta_index()
    commit_and_push()

    safe_print("[instance_sync] Done.")


if __name__ == "__main__":
    main()
