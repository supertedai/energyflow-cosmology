#!/usr/bin/env python3
"""
Full repository validation for Energy-Flow Cosmology.

Validates:
- schema files
- site-graph.json
- methodology API
- all api/v1/*.json
- all reflection metadata
- figshare links
"""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

def validate_json(path: Path):
    try:
        json.loads(path.read_text(encoding="utf-8"))
        print(f"✅ Valid JSON: {path}")
        return True
    except Exception as e:
        print(f"❌ Invalid JSON in {path}: {e}")
        return False

def scan_directory(directory: Path):
    print(f"\n=== Scanning: {directory} ===")
    valid = True
    for file in directory.rglob("*.json"):
        if not validate_json(file):
            valid = False
    return valid

def main():
    checks = [
        ROOT / "schema",
        ROOT / "api",
        ROOT / "figshare",
        ROOT / "reflection",
        ROOT / "methodology",
    ]

    all_ok = True
    for check in checks:
        if not scan_directory(check):
            all_ok = False

    # Validate site-graph explicitly
    site_graph = ROOT / "schema" / "site-graph.json"
    print("\n=== Validating site-graph.json ===")
    all_ok &= validate_json(site_graph)

    if all_ok:
        print("\n🎉 ALL VALIDATION PASSED — SAFE TO UPDATE WORDPRESS")
    else:
        print("\n🔍 VALIDATION ERRORS DETECTED — FIX BEFORE UPDATING WP")
        sys.exit(1)

if __name__ == "__main__":
    main()
