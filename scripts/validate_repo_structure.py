#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GLOBAL_SCHEMA = REPO_ROOT / "schema" / "global_schema.json"
NODE_INDEX = REPO_ROOT / "node-index.json"

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    schema_def = load(GLOBAL_SCHEMA)
    node_index = load(NODE_INDEX)

    type_defs = schema_def.get("type_definitions", {})
    nodes = node_index.get("nodes", [])

    errors = []
    warnings = []

    for node in nodes:
        ntype = node["type"]
        tdef = type_defs.get(ntype, {})
        required_files = tdef.get("required_files", [])
        path = REPO_ROOT / node["path"]

        if not path.exists():
            errors.append(f"[MISSING DIR] {node['id']} → {node['path']}")
            continue

        # handle {basename}
        basename = Path(node["path"]).name
        for rf in required_files:
            rf_resolved = rf.replace("{basename}", basename)
            fpath = path / rf_resolved
            if not fpath.exists():
                errors.append(f"[MISSING FILE] {node['id']} → {rf_resolved}")

    print("=== Repo structure validation ===")
    if not errors:
        print("OK: No missing required files.")
    else:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(" -", e)

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(" -", w)

if __name__ == "__main__":
    main()
