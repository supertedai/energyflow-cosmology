#!/usr/bin/env python3
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

def load_json(rel_path):
    full = REPO_ROOT / rel_path
    if not full.exists():
        print(f"[ERROR] JSON missing: {rel_path}")
        return None
    try:
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse {rel_path}: {e}")
        return None

def check_file(label, rel_path):
    if not rel_path:
        return True
    p = REPO_ROOT / rel_path
    if p.exists():
        print(f"[OK] {label}: {rel_path}")
        return True
    else:
        print(f"[MISSING] {label}: {rel_path}")
        return False

def check_paths_in_json(label_prefix, json_data, key):
    ok = True
    if isinstance(json_data, dict) and key in json_data:
        items = json_data[key]
        for item in items:
            if "path" in item and isinstance(item["path"], str):
                ok &= check_file(f"{label_prefix}:{item.get('id', 'unknown')}", item["path"])
    return ok

def check_semantic_index():
    data = load_json("semantic-search-index.json")
    if not data:
        return False
    ok = True
    for n in data.get("nodes", []):
        ok &= check_file(f"semantic:{n.get('id')}", n.get("path"))
    return ok

def check_site_graph():
    data = load_json("schema/site-graph.json")
    if not data:
        return False
    ok = True
    for ds in data.get("dataset", []):
        for dist in ds.get("distribution", []):
            url = dist.get("contentUrl")
            if url and "://" not in url:
                ok &= check_file(f"site:{ds.get('@id')}", url)
    return ok

def check_api_meta():
    data = load_json("api/v1/meta.json")
    if not data:
        return False
    ok = True
    for layer in data.get("nodes", []):
        path = layer.get("path")
        if path:
            ok &= check_file(f"api:{layer.get('id')}", path)
    return ok

def check_global_schema():
    data = load_json("schema/global_schema.json")
    if not data:
        return False
    ok = True
    for dom in data.get("domains", []):
        root = dom.get("root")
        ok &= check_file(f"domain:{dom.get('id')}", root)
    return ok

def main():
    overall_ok = True
    print("\n=== Checking semantic-search-index.json ===")
    overall_ok &= check_semantic_index()

    print("\n=== Checking schema/site-graph.json ===")
    overall_ok &= check_site_graph()

    print("\n=== Checking api/v1/meta.json ===")
    overall_ok &= check_api_meta()

    print("\n=== Checking schema/global_schema.json ===")
    overall_ok &= check_global_schema()

    print("\n=== Scan complete ===")
    if not overall_ok:
        print("[FAIL] One or more paths are missing or invalid.")
        sys.exit(1)
    print("[SUCCESS] All schema paths validated.")
    sys.exit(0)

if __name__ == "__main__":
    main()
