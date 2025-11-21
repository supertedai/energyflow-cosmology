#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Semantic Harvest v3 (EFC-safe)
=============================================

Gjør:
- Rydder bort feilplasserte JSON-LD (utenfor whitelista nodedirs, men IKKE i PROTECTED_DIRS)
- Genererer EN JSON-LD per dokument (.md/.pdf/.docx/.txt) i whitelista mapper
- Trekker ut enkel semantikk fra .md:
  - tittel (første heading)
  - beskrivelse (første avsnitt)
  - nøkkelord (fra tittel)
- Rebuilder meta-index.json med alle noder
- Commit + push hvis det finnes endringer

Viktig:
- Rører IKKE figshare/ (beskyttet)
- Rører IKKE integration/ (beskyttet)
- Rører IKKE .github/ (via HARD_IGNORES)
"""

import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --------------------------- Konfig ---------------------------

# Mapper som kan inneholde innhold som skal bli noder (fil-baserte)
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

# Mapper vi aldri rører (alt under disse ignoreres fullstendig)
HARD_IGNORES = [
    ".git", ".github", ".venv", "venv",
    "__pycache__", ".idea", ".vscode",
    "output", "notebooks", "scripts",
    "data/raw", "data/archive",
    "figshare",     # figshare håndteres av egen pipeline
    "integration",  # integrasjoner (figshare, wp, osv.) røres ikke
]

# Top-level mapper som er eksplisitt beskyttet mot JSON-LD-cleanup
PROTECTED_DIRS = [
    "figshare",     # ikke rør jsonld/metadata under figshare/
    "integration",  # ikke rør noe under integration/
]

# Filtyper som regnes som "dokument"
DOC_EXTS = [".md", ".pdf", ".docx", ".txt"]

# Dokumenter vi ikke lager egen node for
IGNORED_DOC_BASENAMES = {"readme", "license", "changelog"}

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
    """Kjør kommando med enkel logging."""
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


def extract_semantics_from_md(path: Path):
    """
    Enkel semantisk høsting fra en .md-fil:
    - tittel = første heading (# eller ##)
    - beskrivelse = første avsnitt
    - keywords = ord > 3 tegn fra tittel
    """
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None, None, []

    lines = [ln.rstrip() for ln in text.splitlines()]

    title = None
    for ln in lines:
        if ln.startswith("#"):
            title = ln.lstrip("#").strip()
            if title:
                break

    # Finn første avsnitt (kontinuerlige ikke-tomme linjer)
    desc_lines = []
    started = False
    for ln in lines:
        if not started:
            # hopp over overskrift-linjer
            if ln.startswith("#"):
                continue
            if ln.strip():
                desc_lines.append(ln.strip())
                started = True
        else:
            if not ln.strip():
                break
            desc_lines.append(ln.strip())
            if len(desc_lines) >= 4:
                break

    description = " ".join(desc_lines).strip()
    if len(description) > 600:
        description = description[:600]

    # Keywords fra tittel
    keywords = []
    if title:
        for word in title.replace("–", " ").replace("-", " ").split():
            w = word.strip(".,;:!?()[]{}\"'").lower()
            if len(w) > 3:
                keywords.append(w)
    keywords = sorted(set(keywords))

    return title, description or None, keywords


# ---------------------------- Cleanup ----------------------------

def cleanup_stray_jsonld():
    """
    Fjern JSON-LD:
    - i root (unntatt meta-index.json)
    - i mapper som ikke ligger under NODE_DIR_PREFIXES
    MEN:
    - Rører ikke mapper som er i HARD_IGNORES
    - Rører ikke mapper under PROTECTED_DIRS (som figshare/ og integration/)
    """
    safe_print("[instance_sync] Cleanup: removing stray JSON-LD...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        # root-mappe
        if rel == ".":  # kun root
            for f in files:
                if f.endswith(".jsonld") and f != "meta-index.json":
                    path = Path(root) / f
                    path.unlink(missing_ok=True)
                    safe_print(f"[instance_sync] Removed root JSON-LD: {path}")
            continue

        parts = rel.split(os.sep)

        # hard-ignore alt under disse
        if any(x in HARD_IGNORES for x in parts):
            continue

        # beskytt top-level PROTECTED_DIRS (f.eks. figshare/, integration/)
        top = parts[0]
        if top in PROTECTED_DIRS:
            continue

        # Alt utenfor whitelist → slett .jsonld
        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    path.unlink(missing_ok=True)
                    safe_print(f"[instance_sync] Removed stray JSON-LD: {path}")


# ----------------------- JSON-LD Generation -----------------------

def generate_jsonld_for_documents():
    """
    Lag EN JSON-LD per dokumentfil i whitelista mapper.
    Overstyrer ikke eksisterende per-fil JSON-LD.
    Rører ikke HARD_IGNORES eller PROTECTED_DIRS.
    """
    safe_print("[instance_sync] Generating JSON-LD for documents...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)
        if rel == ".":
            continue

        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        top = parts[0]
        if top in PROTECTED_DIRS:
            continue

        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        layer = rel.split(os.sep)[0]

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in DOC_EXTS:
                continue

            base = os.path.splitext(f)[0]
            if base.lower() in IGNORED_DOC_BASENAMES:
                continue

            # forventet JSON-LD navn: <basename>.jsonld
            expected_jsonld = f"{base}.jsonld"
            jsonld_path = Path(root) / expected_jsonld

            # ikke overskriv eksisterende per-fil JSON-LD
            if jsonld_path.exists():
                continue

            doc_path = Path(root) / f
            rel_doc_path = os.path.relpath(doc_path, ROOT).replace(os.sep, "/")
            identifier = rel_doc_path.rsplit(".", 1)[0]

            title = None
            description = None
            keywords = []

            if ext == ".md":
                t, d, kw = extract_semantics_from_md(doc_path)
                title = t
                description = d
                keywords = kw

            # fallback for tittel
            if not title:
                human_name = base.replace("_", " ").replace("-", " ")
                title = human_name.strip().title()

            data = {
                "@context": "https://schema.org",
                "@type": "CreativeWork",
                "identifier": identifier,
                "name": title,
                "author": AUTHOR,
                "version": "1.0",
                "isPartOf": {
                    "@type": "CreativeWorkSeries",
                    "name": layer
                },
                "layer": layer,
                "encodingFormat": ext.lstrip("."),
                "url": rel_doc_path
            }

            if description:
                data["description"] = description
            if keywords:
                data["keywords"] = keywords

            with jsonld_path.open("w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)

            safe_print(f"[instance_sync] Created JSON-LD: {jsonld_path}")


# ------------------------- Meta-index -------------------------

def rebuild_meta_index():
    """
    Bygg meta-index.json med ALLE .jsonld under whitelista mapper.
    Rører ikke HARD_IGNORES eller PROTECTED_DIRS.
    """
    safe_print("[instance_sync] Building meta-index.json...")

    nodes = []

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)
        parts = rel.split(os.sep)
        if any(x in HARD_IGNORES for x in parts):
            continue

        top = parts[0]
        if top in PROTECTED_DIRS:
            continue

        # tillat root (meta-index.json ligger der), men ellers whitelist
        if rel != "." and not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        for f in files:
            if not f.endswith(".jsonld"):
                continue

            # ikke indekser meta-index selv
            if rel == "." and f == "meta-index.json":
                continue

            path = Path(root) / f
            rel_path = os.path.relpath(path, ROOT).replace(os.sep, "/")

            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                identifier = data.get("identifier") or f.replace(".jsonld", "")
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
    """Sett git-bruker for Actions og lokal kjøring."""
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
    msg = "Instance sync semantic harvest [skip ci]"
    run(["git", "commit", "-m", msg])
    run(["git", "push"])

    safe_print("[instance_sync] Changes pushed successfully.")


# ------------------------------ MAIN ------------------------------

def main():
    safe_print("[instance_sync] Starting instance sync (semantic harvest)...")

    cleanup_stray_jsonld()
    generate_jsonld_for_documents()
    rebuild_meta_index()
    commit_and_push()

    safe_print("[instance_sync] Done.")


if __name__ == "__main__":
    main()
