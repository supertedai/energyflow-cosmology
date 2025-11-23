#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Genererer JSON-LD metadata for alle dokumenter i semantic-index.json.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_INDEX = ROOT / "semantic-index.json"
OUT_DIR = ROOT / "jsonld"

OUT_DIR.mkdir(exist_ok=True)

def main():
    items = json.loads(INPUT_INDEX.read_text(encoding="utf-8"))
    for item in items:
        slug = item["slug"]
        jsonld_file = OUT_DIR / f"{slug}.jsonld"
        data = {
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            "identifier": slug,
            "name": item["title"],
            "description": item["description"],
            "file": item["file"]
        }
        jsonld_file.write_text(json.dumps(data, indent=2))
        print(f"[jsonld] Wrote {jsonld_file}")

if __name__ == "__main__":
    main()
