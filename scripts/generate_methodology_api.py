#!/usr/bin/env python3
"""
Generate api/v1/methodology.json from methodology/open-process.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METHOD = ROOT / "methodology"
OPEN = METHOD / "open-process.json"
OUT = ROOT / "api" / "v1" / "methodology.json"

GITHUB_BASE = "https://github.com/supertedai/energyflow-cosmology/blob/main/methodology/"

def main():
    data = json.loads(OPEN.read_text(encoding="utf-8"))

    out = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "EFC Methodology Layer",
        "description": data.get("description"),
        "source": "https://github.com/supertedai/energyflow-cosmology",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "hasPart": []
    }

    for part in data.get("hasPart", []):
        name = part["name"]
        out["hasPart"].append({
            "name": name,
            "url": GITHUB_BASE + name
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Generated methodology API:", OUT)

if __name__ == "__main__":
    main()
