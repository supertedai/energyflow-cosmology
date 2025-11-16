#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import requests
from datetime import datetime

API_URL = "https://api.figshare.com/v2/account/articles"

# Harde semantiske koblinger for master-spesifikasjonen
CONCEPT_LINKS = [
    "EFC-S",
    "EFC-D",
    "EFC-C₀",
    "Grid-Higgs Framework",
    "Halo Entropy Model",
    "CEM-Cosmos",
    "IMX"
]

METHODOLOGY_LINKS = [
    "Open Cognitive Methodology",
    "Reflective Loop",
    "Author-Method-Note",
    "Symbiose Interface",
    "EFC Epistemology v1"
]


def log(msg):
    ts = datetime.now().isoformat()
    print(f"[{ts}] {msg}")


# --------------------------
# Hent artikler fra Figshare
# --------------------------
def get_articles():
    token = os.environ.get("FIGSHARE_TOKEN")
    if not token:
        raise RuntimeError("FIGSHARE_TOKEN er ikke satt i miljøvariabler")

    headers = {
        "Authorization": f"token {token}",
        "User-Agent": "Mozilla/5.0"
    }

    log("Henter liste over artikler via Figshare API…")
    r = requests.get(API_URL, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()


# --------------------------
# Velg nyeste artikkel
# --------------------------
def pick_latest(articles):
    if not articles:
        raise RuntimeError("Ingen artikler returnert fra Figshare API")

    def safe_date(a):
        d = a.get("published_date")
        return d if isinstance(d, str) and len(d) > 0 else "0000-00-00"

    sorted_list = sorted(articles, key=safe_date, reverse=True)
    return sorted_list[0]


# --------------------------
# Lagre figshare/latest.json
# --------------------------
def save_latest_json(latest):
    os.makedirs("figshare", exist_ok=True)
    out_path = "figshare/latest.json"
    with open(out_path, "w") as f:
        json.dump(latest, f, indent=2)
    log(f"Lagret: {out_path}")


# --------------------------
# Oppdater api/v1/meta.json
# --------------------------
def update_api_meta(latest):
    meta_path = "api/v1/meta.json"

    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            try:
                meta = json.load(f)
            except json.JSONDecodeError:
                log("Advarsel: api/v1/meta.json var korrupt, lager ny.")
                meta = {}
    else:
        meta = {}

    meta.setdefault("sources", {})
    meta["sources"]["figshare"] = {
        "id": latest.get("id"),
        "title": latest.get("title"),
        "published_date": latest.get("published_date"),
        "url": latest.get("url"),
        "doi": latest.get("doi"),
        "resource_id": latest.get("resource_id"),
        "resource_doi": latest.get("resource_doi")
    }

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    log(f"Oppdatert: {meta_path}")


# --------------------------
# Hjelpere for schema-map
# --------------------------
def _ensure_list(node: dict, key: str):
    val = node.get(key)
    if val is None:
        node[key] = []
    elif not isinstance(val, list):
        node[key] = [val]
    return node[key]


def _append_unique(ref_list, item, key_fields):
    """Legg til item i ref_list hvis det ikke finnes fra før basert på key_fields."""
    for existing in ref_list:
        if all(existing.get(k) == item.get(k) for k in key_fields):
            return  # finnes allerede
    ref_list.append(item)


# --------------------------
# Oppdater schema/schema-map.json
# --------------------------
def update_schema_map(latest):
    schema_path = "schema/schema-map.json"

    if not os.path.exists(schema_path):
        log(f"Schema-map ikke funnet ({schema_path}), hopper over oppdatering.")
        return

    with open(schema_path, "r") as f:
        try:
            schema = json.load(f)
        except json.JSONDecodeError:
            log("Advarsel: schema-map.json var korrupt, hopper over oppdatering.")
            return

    doi = latest.get("doi")
    fig_id = latest.get("id")
    url = latest.get("url")
    published_date = latest.get("published_date")

    schema["last_updated"] = datetime.now().date().isoformat()
    nodes = schema.setdefault("nodes", {})

    # ---------------- FigshareNode ----------------
    fig_node = {
        "description": "Auto-synkronisert Figshare-kilde for siste publiserte EFC-masterspesifikasjon.",
        "files": [
            {
                "name": "latest.json",
                "path": "figshare/latest.json",
                "type": "latest_metadata",
                "figshare_id": fig_id,
                "doi": doi,
                "url": url,
                "published_date": published_date
            }
        ],
        "links": []
    }

    # legg til semantiske lenker fra FigshareNode til konsepter og metodologi
    for cname in CONCEPT_LINKS:
        fig_node["links"].append({
            "type": "covers_concept",
            "ref": cname
        })
    for mname in METHODOLOGY_LINKS:
        fig_node["links"].append({
            "type": "uses_method",
            "ref": mname
        })

    nodes["FigshareNode"] = fig_node

    # ---------------- ConceptNode ----------------
    concept_node = nodes.get("ConceptNode")
    if concept_node is not None:
        refs = _ensure_list(concept_node, "figshare_refs")
        _append_unique(
            refs,
            {
                "id": fig_id,
                "doi": doi,
                "url": url,
                "role": "master_spec"
            },
            key_fields=["id", "doi"]
        )
        nodes["ConceptNode"] = concept_node

    # ---------------- MethodologyNode ----------------
    methodology_node = nodes.get("MethodologyNode")
    if methodology_node is not None:
        refs = _ensure_list(methodology_node, "figshare_refs")
        _append_unique(
            refs,
            {
                "id": fig_id,
                "doi": doi,
                "url": url,
                "role": "master_spec"
            },
            key_fields=["id", "doi"]
        )
        nodes["MethodologyNode"] = methodology_node

    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)

    log(f"Oppdatert: {schema_path} (FigshareNode + figshare_refs)")


# --------------------------
# Main
# --------------------------
def main():
    try:
        articles = get_articles()
        latest = pick_latest(articles)

        log("------ Nyeste Figshare-artikkel ------")
        log(f"ID: {latest.get('id')}")
        log(f"Tittel: {latest.get('title')}")
        log(f"Publisert: {latest.get('published_date')}")
        log("--------------------------------------")

        save_latest_json(latest)
        update_api_meta(latest)
        update_schema_map(latest)

    except Exception as e:
        log(f"Feil: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
