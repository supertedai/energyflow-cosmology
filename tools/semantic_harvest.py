#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEMANTIC HARVEST v3
-------------------

- Leser gjennom innhold i definerte mapper
- Ekstraherer enkel semantikk fra .md, .txt, .pdf osv.
- Oppdaterer meta-index.json
"""

import os
import json
from pathlib import Path
from slugify import slugify

ROOT = Path(__file__).resolve().parents[1]

# Mapper som inneholder innhold som skal indekseres i symbiosen
SCAN_DIRS = [
    "docs",
    "meta",
    "schema",
    "api",
]

OUTPUT_INDEX = ROOT / "semantic-index.json"


def extract_from_md(path: Path):
    """Trekk ut tittel og beskrivelse fra en .md fil."""
    title = None
    desc = None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except:
        return None

    for line in lines:
        if not title and line.strip().startswith("#"):
            title = line.replace("#", "").strip()
        elif title and line.strip():
            desc = line.strip()
            break

    if not title:
        title = path.stem

    return {"title": title, "description": desc or "", "file": str(path)}


def harvest():
    items = []

    for folder in SCAN_DIRS:
        folder_path = ROOT / folder

        if not folder_path.exists():
            continue

        for path in folder_path.rglob("*"):
            if path.is_dir():
                continue

            if path.suffix.lower() == ".md":
                meta = extract_from_md(path)
                if meta:
                    meta["slug"] = slugify(meta["title"])
                    items.append(meta)

            elif path.suffix.lower() in [".txt", ".pdf", ".jsonld"]:
                items.append({
                    "title": path.stem,
                    "description": "",
                    "file": str(path),
                    "slug": slugify(path.stem)
                })

    print(f"[semantic-harvest] Found {len(items)} items.")

    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

    print(f"[semantic-harvest] Wrote {OUTPUT_INDEX}")


if __name__ == "__main__":
    harvest()
