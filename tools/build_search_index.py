#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from slugify import slugify

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "semantic-index.json"
OUTPUT = ROOT / "semantic-search-index.json"


def main():
    items = json.loads(INPUT.read_text(encoding="utf-8"))

    index = []
    for item in items:
        index.append({
            "slug": item["slug"],
            "title": item["title"],
            "keywords": item["title"].lower().split() + item["description"].lower().split(),
            "file": item["file"]
        })

    OUTPUT.write_text(json.dumps(index, indent=2))
    print(f"[search-index] Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
