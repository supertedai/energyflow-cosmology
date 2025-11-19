#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = REPO_ROOT / "schema" / "global_schema.json"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def classify_node_id(root_rel, subdir):
    # for papers: id = folder name
    if root_rel == Path("docs/papers/efc"):
        return subdir.name
    # else: use path-based id
    return str(root_rel / subdir.name).replace("\\", "/")

def ensure_paper_files(domain_def, subdir, jsonld_type):
    """
    Sikrer standardstruktur i docs/papers/efc/*
    Lager bare skeletter hvis filer mangler.
    """
    basename = subdir.name
    readme = subdir / "README.md"
    jsonld = subdir / f"{basename}.jsonld"
    index_json = subdir / "index.json"
    schema_json = subdir / "schema.json"
    bib = subdir / "citations.bib"

    if not readme.exists():
        readme.write_text(
            f"# {basename.replace('-', ' ')}\n\n"
            f"This directory contains the paper `{basename}` in the Energy-Flow Cosmology project.\n\n"
            "Version: 1.0\n",
            encoding="utf-8",
        )

    if not jsonld.exists():
        data = {
            "@context": "https://schema.org",
            "@type": jsonld_type,
            "@id": f"https://github.com/supertedai/energyflow-cosmology/docs/papers/efc/{basename}",
            "identifier": basename,
            "name": basename.replace("-", " "),
            "version": "1.0"
        }
        save_json(jsonld, data)

    if not index_json.exists():
        idx = {
            "id": basename,
            "title": basename.replace("-", " "),
            "path": f"docs/papers/efc/{basename}",
            "pdf": f"{basename}.pdf",
            "md": f"{basename}.md",
            "layer": "docs",
            "type": "paper",
            "version": "1.0"
        }
        save_json(index_json, idx)

    if not schema_json.exists():
        schema = {
            "required": [
                "@context",
                "@type",
                "identifier",
                "name",
                "version"
            ],
            "properties": {
                "@context": {"type": "string"},
                "@type": {"type": "string"},
                "identifier": {"type": "string"},
                "name": {"type": "string"},
                "version": {"type": "string"}
            }
        }
        save_json(schema_json, schema)

    if not bib.exists():
        bib.write_text(
            f"@article{{{basename.lower().replace('-', '')},\n"
            f"  title={{{{ {basename.replace('-', ' ')} }}}},\n"
            "  author={Magnusson, Morten},\n"
            "  year={2025},\n"
            "  note={Energy-Flow Cosmology Project},\n"
            "  url={https://github.com/supertedai/energyflow-cosmology}\n"
            "}\n",
            encoding="utf-8",
        )

def scan_domain(domain):
    root_rel = Path(domain["root"])
    root_abs = REPO_ROOT / root_rel
    domain_type = domain["type"]
    jsonld_type = domain["jsonld_type"]
    nodes = []

    if not root_abs.exists():
        return nodes

    # bare direkte under-mapper
    for sub in sorted(root_abs.iterdir()):
        if not sub.is_dir():
            continue
        node_id = classify_node_id(root_rel, sub)

        # domain-spesifikk behandling
        if domain_type == "paper":
            ensure_paper_files(domain, sub, jsonld_type)

        nodes.append({
            "id": node_id,
            "path": str((root_rel / sub.name).as_posix()),
            "domain": domain["id"],
            "type": domain_type,
            "jsonld_type": jsonld_type
        })

    return nodes

def generate_global_indexes(nodes, schema_def):
    # meta-index: oversikt per domain
    meta_index = {
        "version": "1.0",
        "domains": []
    }
    by_domain = {}
    for n in nodes:
        by_domain.setdefault(n["domain"], []).append(n)

    for d in schema_def["domains"]:
        did = d["id"]
        meta_index["domains"].append({
            "id": did,
            "root": d["root"],
            "type": d["type"],
            "count": len(by_domain.get(did, []))
        })

    # node-index: flat liste
    node_index = {
        "version": "1.0",
        "nodes": nodes
    }

    # schema-map: mapping type -> schema location (her enkel)
    schema_map = {
        "version": "1.0",
        "types": {}
    }
    for tname in schema_def["type_definitions"].keys():
        schema_map["types"][tname] = {
            "schema_source": "schema/global_schema.json",
            "required_files": schema_def["type_definitions"][tname]["required_files"]
            if "required_files" in schema_def["type_definitions"][tname] else []
        }

    return meta_index, node_index, schema_map

def generate_efc_paper_indexes(nodes):
    # filtrer ut bare docs/papers/efc
    efc_nodes = [n for n in nodes if n["path"].startswith("docs/papers/efc/")]
    # jsonld collection
    efc_jsonld = {
        "@context": "https://schema.org",
        "@type": "Collection",
        "@id": "https://github.com/supertedai/energyflow-cosmology/docs/papers/efc",
        "name": "EFC Papers — Energy-Flow Cosmology",
        "version": "1.0",
        "hasPart": [{"@id": n["id"]} for n in efc_nodes]
    }
    # machine index
    efc_index = {
        "version": "1.0",
        "root": "docs/papers/efc",
        "papers": [
            {
                "id": n["id"],
                "path": n["path"].split("docs/papers/efc/")[-1],
                "type": "paper"
            }
            for n in efc_nodes
        ]
    }
    return efc_jsonld, efc_index

def main():
    schema_def = load_json(SCHEMA_FILE)
    all_nodes = []
    for domain in schema_def["domains"]:
        all_nodes.extend(scan_domain(domain))

    meta_index, node_index, schema_map = generate_global_indexes(all_nodes, schema_def)
    save_json(REPO_ROOT / "meta-index.json", meta_index)
    save_json(REPO_ROOT / "node-index.json", node_index)
    save_json(REPO_ROOT / "schema-map.json", schema_map)

    efc_jsonld, efc_index = generate_efc_paper_indexes(all_nodes)
    save_json(REPO_ROOT / "docs/papers/efc/efc_index.jsonld", efc_jsonld)
    save_json(REPO_ROOT / "docs/papers/efc/efc_index.json", efc_index)

    print(f"Updated meta-index, node-index, schema-map and EFC paper indexes. Total nodes: {len(all_nodes)}")

if __name__ == "__main__":
    main()
