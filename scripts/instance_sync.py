#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Semantic Harvest v4 (EFC-safe, Figshare-safe)
=============================================================

Beskyttede mapper:
- figshare/
- integrations/
- integrations/figshare/

Denne versjonen sikrer:
- Figshare-data slettes aldri
- Integrations/ slettes aldri
- Integrations/figshare/ slettes aldri
- JSON-LD genereres kun i whitelista mapper
- Repoet holdes strukturelt konsistent uten å ødelegge forskningsdata
"""

import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --------------------------- Konfig ---------------------------

NODE_DIR_PREFIXES = [
    "meta",
    "methodology",
    "schema",
    "api",
    "docs",
    "src/efc",
    "data/sparc",
    "data/processed",
]

# Mapper som ALDRI røres
HARD_IGNORES = [
    ".git", ".github", ".venv", "venv",
    "__pycache__", ".idea", ".vscode",
    "output", "notebooks", "scripts",
    "data/raw", "data/archive",
    "figshare",            # beskyttet
    "integrations",        # beskyttet
    "integration",         # beskyttet feilmappe
]

# Top-level mapper som er beskyttet mot cleanup
PROTECTED_DIRS = [
    "figshare",
    "integrations",
    "integrations/figshare",
    "integration",
]

DOC_EXTS = [".md", ".pdf", ".docx", ".txt"]
IGNORED_DOC_BASENAMES = {"readme", "license", "changelog"}

AUTHOR = {
    "@type": "Person",
    "name": "Morten Magnusson",
    "identifier": "https://orcid.org/0009-0002-4860-5095",
}

# ---------------------- Util ----------------------

def safe_print(msg: str):
    try:
        print(msg)
    except:
        pass

def run(cmd, cwd=None, check=True):
    safe_print(f"[instance_sync] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or ROOT, text=True)
    if check and result.returncode != 0:
        safe_print(f"Command failed {result.returncode}")
        raise SystemExit(result.returncode)
    return result

def is_under_prefix(rel_path, prefixes):
    return any(rel_path == p or rel_path.startswith(p + "/") for p in prefixes)

# ---------------------------- Cleanup ----------------------------

def cleanup_stray_jsonld():
    safe_print("[instance_sync] Cleanup JSON-LD...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        # root
        if rel == ".":
            for f in files:
                if f.endswith(".jsonld") and f != "meta-index.json":
                    (Path(root)/f).unlink(missing_ok=True)
            continue

        parts = rel.split(os.sep)

        # ignorér beskyttede mapper
        if parts[0] in PROTECTED_DIRS:
            continue

        # hard-ignores
        if any(x in HARD_IGNORES for x in parts):
            continue

        # slett kun det som er utenfor whitelist
        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            for f in files:
                if f.endswith(".jsonld"):
                    (Path(root)/f).unlink(missing_ok=True)

# ---------------------------- Metadata extraction ----------------------------

def extract_semantics_from_md(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except:
        return None, None, []

    lines = [ln.rstrip() for ln in text.splitlines()]

    # Title
    title = None
    for ln in lines:
        if ln.startswith("#"):
            title = ln.lstrip("#").strip()
            break

    # Description
    desc = []
    started = False
    for ln in lines:
        if not started:
            if ln.startswith("#"):
                continue
            if ln.strip():
                desc.append(ln.strip())
                started = True
        else:
            if not ln.strip():
                break
            desc.append(ln.strip())
            if len(desc) >= 4:
                break

    description = " ".join(desc).strip()[:600]

    # Keywords
    keywords = []
    if title:
        for w in title.replace("-", " ").replace("–", " ").split():
            w = w.strip(".,!?;:()[]'\"").lower()
            if len(w) > 3:
                keywords.append(w)

    return title, description, sorted(set(keywords))

# ----------------------- JSON-LD Generation -----------------------

def generate_jsonld_for_documents():
    safe_print("[instance_sync] Generate JSON-LD...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        if rel == ".":
            continue

        parts = rel.split(os.sep)

        if parts[0] in PROTECTED_DIRS:
            continue

        if any(x in HARD_IGNORES for x in parts):
            continue

        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        layer = parts[0]

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in DOC_EXTS:
                continue

            base = os.path.splitext(f)[0]
            if base.lower() in IGNORED_DOC_BASENAMES:
                continue

            jsonld_path = Path(root)/f"{base}.jsonld"

            if jsonld_path.exists():
                continue

            doc_path = Path(root)/f
            rel_doc = os.path.relpath(doc_path, ROOT).replace(os.sep, "/")
            identifier = rel_doc.rsplit(".", 1)[0]

            title, desc, kw = (None, None, [])

            if ext == ".md":
                title, desc, kw = extract_semantics_from_md(doc_path)

            if not title:
                title = base.replace("_", " ").replace("-", " ").title()

            data = {
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "identifier": identifier,
                "name": title,
                "author": AUTHOR,
                "version": "1.0",
                "isPartOf": {"@type": "CreativeWorkSeries", "name": layer},
                "layer": layer,
                "encodingFormat": ext.lstrip("."),
                "url": rel_doc,
            }

            if desc:
                data["description"] = desc
            if kw:
                data["keywords"] = kw

            jsonld_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ------------------------- Meta-index -------------------------

def rebuild_meta_index():
    safe_print("[instance_sync] Build meta-index.json...")

    nodes = []

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)
        parts = rel.split(os.sep)

        if parts[0] in PROTECTED_DIRS:
            continue

        if any(x in HARD_IGNORES for x in parts):
            continue

        if rel != "." and not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        for f in files:
            if not f.endswith(".jsonld"):
                continue

            if rel == "." and f == "meta-index.json":
                continue

            p = Path(root)/f
            rel_path = os.path.relpath(p, ROOT).replace(os.sep, "/")

            try:
                data = json.loads(p.read_text())
                identifier = data.get("identifier", f[:-7])
                typ = data.get("@type", "CreativeWork")
            except:
                identifier = f[:-7]
                typ = "CreativeWork"

            nodes.append({"id": identifier, "path": rel_path, "type": typ})

    (ROOT/"meta-index.json").write_text(
        json.dumps({"version": "1.0", "nodes": nodes}, indent=2),
        encoding="utf-8"
    )

# ---------------------- Git commit ----------------------

def git_status():
    r = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip()

def configure_git_user():
    run(["git", "config", "user.name", "github-actions"], check=False)
    run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=False)

def commit_and_push():
    s = git_status()

    if not s:
        safe_print("[instance_sync] No changes.")
        return

    configure_git_user()

    run(["git", "add", "-A"])
    run(["git", "commit", "-m", "Instance sync semantic harvest [skip ci]"])
    run(["git", "push"])

# ------------------------------ MAIN ------------------------------

def main():
    safe_print("[instance_sync] START")
    cleanup_stray_jsonld()
    generate_jsonld_for_documents()
    rebuild_meta_index()
    commit_and_push()
    safe_print("[instance_sync] DONE")

if __name__ == "__main__":
    main()
