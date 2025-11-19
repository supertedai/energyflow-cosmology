#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def load_json(path):
    full = REPO_ROOT / path
    if not full.exists():
        print(f"[WARN] JSON file not found: {path}")
        return None
    try:
        return json.load(open(full, "r", encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to parse {path}: {e}")
        return None

def check_path(label, rel_path):
    if not rel_path:
        return
    p = REPO_ROOT / rel_path
    if p.exists():
        print(f"[OK] {label}: {rel_path}")
    else:
        print(f"[MISSING] {label}: {rel_path}")

def check_semantic_index():
    data = load_json("semantic-search-index.json")
    if not data:
        return
    for node in data.get("nodes", []):
        check_path(f"semantic-node:{node.get('id')}", node.get("path"))

def check_site_graph():
    data = load_json("schema/site-graph.json")
    if not data:
        return
    for ds in data.get("dataset", []):
        for dist in ds.get("distribution", []):
            url = dist.get("contentUrl")
            # ignorer eksterne lenker
            if url and "://" not in url:
                check_path(f"site-graph:{ds.get('@id')}", url)

def check_api_meta():
    data = load_json("api/v1/meta.json")
    if not data:
        return
    for layer in data.get("layers", []):
        for p in layer.get("paths", []):
            check_path(f"api-meta:{layer.get('id')}", p)

def check_global_schema():
    data = load_json("schema/global_schema.json")
    if not data:
        return
    for dom in data.get("domains", []):
        root = dom.get("root")
        if root:
            check_path(f"global-schema:{dom.get('id')}", root)

def main():
    print("=== Checking semantic-search-index.json ===")
    check_semantic_index()
    print("\n=== Checking schema/site-graph.json ===")
    check_site_graph()
    print("\n=== Checking api/v1/meta.json ===")
    check_api_meta()
    print("\n=== Checking schema/global_schema.json ===")
    check_global_schema()

if __name__ == "__main__":
    main()
