#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def validate_json(path: Path, errors: list):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"Invalid JSON in {path}: {e}")

def validate_domain(path: Path, errors: list):
    if not (path / "index.md").exists():
        errors.append(f"Missing index.md in {path}")

    jsonld = path / "index.jsonld"
    if not jsonld.exists():
        errors.append(f"Missing index.jsonld in {path}")
    else:
        validate_json(jsonld, errors)

def main():
    repo = Path(".").resolve()
    errors = []

    DOMAINS = [
        "meta/meta-process/pattern",
        "meta/meta-process/topology",
        "meta/meta-process/integration",
        "meta/metascope",
        "meta/symbiosis",
        "meta-graph",
        "auth",
        "schema",
        "theory/formal"
    ]

    for d in DOMAINS:
        validate_domain(repo / d, errors)

    # Combine with existing paper validator
    print("\n[INFO] Running paper validator:")
    code = os.system("python scripts/validate_papers.py")
    if code != 0:
        errors.append("Paper validator failed")

    if errors:
        print("\n✖ ERRORS:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("\n✔ All domain nodes validated successfully.")

if __name__ == "__main__":
    main()
