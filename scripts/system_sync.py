#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEM SYNC — Semantic Graph v3 (max)
=====================================

Gjør tre ting:

1) Oppdaterer EFC-konsepter og API
   - kjører update_concepts.py hvis finnes
   - kjører update_efc_api.py hvis finnes

2) Bygger semantiske indekser basert på meta-index.json:
   - schema/node-index.json   → alle noder
   - schema/docs-index.json   → menneskevennlige dokumentnoder
   - schema/semantic-graph.json → lettvekts kunnskapsgraf (struktur + keywords)
   - api/v1/node_index.json   → API-eksponering av node-index

3) Validerer sentrale JSON-filer (schema, api, figshare, methodology)
   - gir grønn “SAFE TO UPDATE WORDPRESS” hvis alt er gyldig

Kjører trygt både lokalt og i GitHub Actions.
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_DIR = ROOT / "schema"
API_DIR = ROOT / "api" / "v1"
META_INDEX_PATH = ROOT / "meta-index.json"

# hvilke path-prefixer regnes som “dokument”-noder
DOC_PREFIXES = [
    "docs/",
    "meta/",
    "methodology/",
    "figshare/",
]


# ---------------------- util ----------------------

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass


def run(cmd, cwd=None, check=True):
    safe_print(f"[system_sync] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or ROOT, text=True)
    if check and result.returncode != 0:
        safe_print(f"[system_sync] Command failed with code {result.returncode}")
        raise SystemExit(result.returncode)
    return result


def file_exists(path: Path) -> bool:
    return path.is_file()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ------------------ steg 1: update concepts / API ------------------

def update_concepts():
    safe_print("=== Update concepts ===")
    script = ROOT / "scripts" / "update_concepts.py"
    if file_exists(script):
        run(["python", str(script)])
    else:
        safe_print("🔄 No update_concepts.py logic found — placeholder executed successfully.")


def update_efc_api():
    safe_print("=== Update EFC API ===")
    script = ROOT / "scripts" / "update_efc_api.py"
    if file_exists(script):
        run(["python", str(script)])
    else:
        safe_print("🔄 No update_efc_api.py script found — skipping API update.")


# ------------------ steg 2: bygg semantiske indekser ------------------

def build_semantic_indices():
    safe_print("=== Build semantic indices from meta-index.json ===")

    if not META_INDEX_PATH.is_file():
        safe_print("[system_sync] meta-index.json not found — skipping semantic indices.")
        return

    try:
        meta_index = load_json(META_INDEX_PATH)
    except Exception as e:
        safe_print(f"[system_sync] Could not read meta-index.json: {e}")
        return

    nodes_raw = meta_index.get("nodes", [])
    safe_print(f"[system_sync] Loaded {len(nodes_raw)} nodes from meta-index.json")

    node_index = []
    docs_index = []
    keyword_map = {}   # keyword -> set(node_id)
    id_to_node = {}    # for senere grafbygging

    for entry in nodes_raw:
        node_id = entry.get("id")
        path_str = entry.get("path")
        node_type = entry.get("type", "CreativeWork")

        if not node_id or not path_str:
            continue

        jsonld_path = ROOT / path_str
        data = {}
        if jsonld_path.is_file():
            try:
                data = load_json(jsonld_path)
            except Exception:
                data = {}

        name = data.get("name")
        layer = data.get("layer")
        keywords = data.get("keywords", [])
        description = data.get("description")

        # normaliser keywords til liste av strenger
        if isinstance(keywords, str):
            keywords = [keywords]
        elif not isinstance(keywords, list):
            keywords = []

        rel_path = path_str.replace("\\", "/")

        flat = {
            "id": node_id,
            "path": rel_path,
            "type": node_type,
        }
        if name:
            flat["name"] = name
        if layer:
            flat["layer"] = layer
        if keywords:
            flat["keywords"] = keywords
        if description:
            # kort beskrivelse her, ikke hele teksten
            flat["description"] = description[:400]

        node_index.append(flat)
        id_to_node[node_id] = flat

        # docs-index: kun menneskeorienterte noder
        if any(rel_path.startswith(p) for p in DOC_PREFIXES):
            docs_index.append(flat)

        # keyword-graf
        for kw in keywords:
            kw_norm = str(kw).strip().lower()
            if not kw_norm:
                continue
            keyword_map.setdefault(kw_norm, set()).add(node_id)

    # sortér for determinisme
    node_index.sort(key=lambda x: x["id"])
    docs_index.sort(key=lambda x: x["id"])

    # bygg enkel semantisk graf:
    # - parent = mappe (dir) som strukturell “forelder”
    # - related = noder som deler minst ett keyword
    semantic_nodes = []
    for n in node_index:
        nid = n["id"]
        path_str = n["path"]
        parent_dir = os.path.dirname(path_str)

        related_ids = set()
        for kw in n.get("keywords", []):
            kw_norm = str(kw).strip().lower()
            if kw_norm in keyword_map:
                related_ids.update(keyword_map[kw_norm])
        related_ids.discard(nid)
        # begrens relasjoner for å unngå eksplosjon
        related_sorted = sorted(list(related_ids))[:30]

        semantic_nodes.append({
            "id": nid,
            "path": path_str,
            "layer": n.get("layer"),
            "parent": parent_dir if parent_dir not in (".", "") else None,
            "related": related_sorted,
        })

    semantic_graph = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "node_count": len(node_index),
        "doc_node_count": len(docs_index),
        "keyword_count": len(keyword_map),
        "nodes": semantic_nodes,
    }

    # skriv ut filer
    dump_json(SCHEMA_DIR / "node-index.json", {
        "version": "1.0",
        "generated_at": semantic_graph["generated_at"],
        "nodes": node_index,
    })

    dump_json(SCHEMA_DIR / "docs-index.json", {
        "version": "1.0",
        "generated_at": semantic_graph["generated_at"],
        "nodes": docs_index,
    })

    dump_json(SCHEMA_DIR / "semantic-graph.json", semantic_graph)

    dump_json(API_DIR / "node_index.json", {
        "version": "1.0",
        "generated_at": semantic_graph["generated_at"],
        "nodes": node_index,
    })

    safe_print(f"[system_sync] node-index: {len(node_index)} noder")
    safe_print(f"[system_sync] docs-index: {len(docs_index)} noder")
    safe_print(f"[system_sync] semantic-graph: {len(semantic_nodes)} noder")


# ------------------ steg 3: valider JSON ------------------

def validate_json_file(path: Path):
    try:
        load_json(path)
        safe_print(f"✅ Valid JSON: {path}")
        return True
    except Exception as e:
        safe_print(f"❌ Invalid JSON: {path} ({e})")
        return False


def validate_system():
    safe_print("=== Validate system ===")

    ok = True

    # schema-core
    schema_core = [
        "schema-map.json",
        "pages-structure.json",
        "posts-structure.json",
        "docs-index.json",
        "site-graph.json",
        "concepts.json",
        "sitemap-links.json",
        "methodology-index.json",
    ]
    for name in schema_core:
        path = SCHEMA_DIR / name
        if path.is_file():
            ok = validate_json_file(path) and ok

    # api-core
    api_core = [
        ROOT / "api" / "index.json",
        ROOT / "api" / "metadata.json",
        API_DIR / "concepts.json",
        API_DIR / "terms.json",
        API_DIR / "api_index.json",
        API_DIR / "methodology.json",
        API_DIR / "meta.json",
        API_DIR / "node_index.json",
    ]
    for path in api_core:
        if path.is_file():
            ok = validate_json_file(path) and ok

    # figshare
    figshare_dir = ROOT / "figshare"
    for name in ["figshare-links.json", "latest.json", "figshare-index.json"]:
        path = figshare_dir / name
        if path.is_file():
            ok = validate_json_file(path) and ok

    # methodology
    methodology_dir = ROOT / "methodology"
    open_process = methodology_dir / "open-process.json"
    if open_process.is_file():
        ok = validate_json_file(open_process) and ok

    if ok:
        safe_print("\n🎉 ALL VALIDATION PASSED — SAFE TO UPDATE WORDPRESS")
    else:
        safe_print("\n⚠️ Validation reported errors — check logs before updating WordPress")

    return ok


# ------------------ git commit + push ------------------

def git_status_porcelain():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def configure_git_user():
    run(["git", "config", "user.name", "github-actions"], check=False)
    run(["git", "config", "user.email", "github-actions@users.noreply.github.com"], check=False)


def commit_and_push_if_needed():
    status = git_status_porcelain()
    safe_print("[system_sync] Git status (porcelain):")
    safe_print(status if status else "(clean)")

    if not status:
        safe_print("[system_sync] No changes to commit.")
        return

    configure_git_user()
    run(["git", "add", "-A"])
    msg = "System sync semantic graph [skip ci]"
    run(["git", "commit", "-m", msg])
    run(["git", "push"])
    safe_print("[system_sync] Changes pushed successfully.")


# ------------------ main ------------------

def main():
    safe_print("=== System Sync start ===")
    update_concepts()
    update_efc_api()
    build_semantic_indices()
    validate_system()
    commit_and_push_if_needed()
    safe_print("=== System Sync complete ===")


if __name__ == "__main__":
    main()
