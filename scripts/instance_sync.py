#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INSTANCE SYNC — Light Maintenance Layer (Whitelisted & Clean)
=============================================================

Formål:
- Rydde bort feilplasserte / auto-genererte JSON-LD som ikke hører hjemme
- Generere manglende JSON-LD KUN i whitelistede kunnskapsmapper
- Bygge meta-index.json for hele kunnskapsgrafen

Egenskaper:
- Ingen git-commit
- Ingen figshare-kall
- Ingen ekstern avhengighet
- Trygg å kjøre ofte (f.eks. hver time)
"""

import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ------------------------- Konfigurasjon -------------------------

# Mapper som regnes som "kunnskapsnoder" og hvor vi TILLATER JSON-LD
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

# Mapper vi ALDRI vil gå inn i for node-logikk (git, venv osv.)
HARD_IGNORES = [
    ".git",
    ".github",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "output",
]

AUTHOR = {
    "@type": "Person",
    "name": "Morten Magnusson",
    "identifier": "https://orcid.org/0009-0002-4860-5095",
}


def safe_print(msg: str) -> None:
    try:
        print(msg)
    except Exception:
        pass


def is_under_prefix(rel_path: str, prefixes) -> bool:
    """Sjekk om rel_path ligger under en av prefixene."""
    for p in prefixes:
        if rel_path == p or rel_path.startswith(p + "/"):
            return True
    return False


def dir_slug(rel_path: str) -> str:
    """Bruk mappenavnet som slug."""
    return os.path.basename(rel_path) if rel_path and rel_path != "." else ""


# ------------------------- Fase 1: RYDDING -------------------------

def cleanup_stray_jsonld():
    """
    Fjern JSON-LD fra mapper som IKKE er whitelisted kunnskapsnoder.
    Fjerner også evt. JSON-LD i repo-root.
    """
    safe_print("[instance_sync] Cleanup: removing stray JSON-LD...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        # Hopp over hard-ignore-mapper
        parts = rel.split(os.sep)
        if any(part in HARD_IGNORES for part in parts):
            continue

        # Root '.' → ingen JSON-LD skal ligge her
        if rel == ".":
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    try:
                        path.unlink()
                        safe_print(f"[instance_sync] Removed root JSON-LD: {path}")
                    except Exception as e:
                        safe_print(f"[instance_sync] Could not remove {path}: {e}")
            continue

        # Mapper som IKKE er under noen tillatte NODE_DIR_PREFIXES → fjern JSON-LD
        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            for f in files:
                if f.endswith(".jsonld"):
                    path = Path(root) / f
                    try:
                        path.unlink()
                        safe_print(f"[instance_sync] Removed stray JSON-LD: {path}")
                    except Exception as e:
                        safe_print(f"[instance_sync] Could not remove {path}: {e}")


# ------------------------- Fase 2: GENERERING -------------------------

def generate_jsonld_for_missing_nodes():
    """
    Generer minimal JSON-LD for mapper under whitelistede NODE_DIR_PREFIXES
    som ikke allerede har korrekt JSON-LD.
    """
    safe_print("[instance_sync] Generating missing JSON-LD in whitelisted dirs...")

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        # Hopp over root
        if rel == ".":
            continue

        # Hopp over hard-ignores
        parts = rel.split(os.sep)
        if any(part in HARD_IGNORES for part in parts):
            continue

        # Bare operer på whitelisted mapper
        if not is_under_prefix(rel, NODE_DIR_PREFIXES):
            continue

        slug = dir_slug(rel)
        if not slug:
            continue

        expected = f"{slug}.jsonld"
        has_expected = expected in files

        if has_expected:
            # Ikke rør JSON-LD som allerede er der
            continue

        jsonld_path = Path(root) / expected

        data = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "identifier": slug,
            "name": slug.replace("_", " ").replace("-", " "),
            "layer": rel.split(os.sep)[0],  # toppnivå som "schema", "meta", "api", ...
            "author": AUTHOR,
            "version": "1.0",
        }

        try:
            with jsonld_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            safe_print(f"[instance_sync] Created JSON-LD: {jsonld_path}")
        except Exception as e:
            safe_print(f"[instance_sync] Could not write JSON-LD {jsonld_path}: {e}")


# ------------------------- Fase 3: META-INDEX -------------------------

def rebuild_meta_index():
    """
    Skanner hele repoet etter .jsonld (etter rydding),
    og bygger en enkel meta-index.json for kunnskapsnoder.
    """
    safe_print("[instance_sync] Building meta-index.json...")

    nodes = []

    for root, dirs, files in os.walk(ROOT):
        rel = os.path.relpath(root, ROOT)

        # Hopp over hard-ignores
        parts = rel.split(os.sep)
        if any(part in HARD_IGNORES for part in parts):
            continue

        for f in files:
            if not f.endswith(".jsonld"):
                continue

            path = Path(root) / f
            rel_path = os.path.relpath(path, ROOT)

            identifier = None
            node_type = "CreativeWork"

            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                identifier = data.get("identifier")
                node_type = data.get("@type", "CreativeWork")
            except Exception:
                # Fallback: bruk filnavn uten suffiks
                identifier = f.replace(".jsonld", "")

            nodes.append(
                {
                    "id": identifier,
                    "path": rel_path.replace(os.sep, "/"),
                    "type": node_type,
                }
            )

    meta_index_path = ROOT / "meta-index.json"
    try:
        with meta_index_path.open("w", encoding="utf-8") as f:
            json.dump({"version": "1.0", "nodes": nodes}, f, indent=2)
        safe_print(f"[instance_sync] meta-index.json updated with {len(nodes)} nodes.")
    except Exception as e:
        safe_print(f"[instance_sync] Could not write meta-index.json: {e}")


# ------------------------- MAIN -------------------------

def main():
    safe_print("[instance_sync] Starting instance sync (whitelist + cleanup)...")

    cleanup_stray_jsonld()
    generate_jsonld_for_missing_nodes()
    rebuild_meta_index()

    safe_print("[instance_sync] Done.")


if __name__ == "__main__":
    main()
