"""
Simple utility to inspect the EFC metascope meta-graph.

Usage:
    python meta-graph/generate_meta_graph.py
"""

import json
from pathlib import Path


def load_meta_graph(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_nodes(graph: dict):
    for node in graph.get("@graph", []):
        yield node


def iter_edges(graph: dict):
    edge_keys = [
        "dependsOn",
        "produces",
        "stabilises",
        "amplifies",
        "emergesFrom",
        "implementedBy",
        "documentedIn",
        "efc:dependsOn",
        "efc:produces",
        "efc:stabilises",
        "efc:amplifies",
        "efc:emergesFrom",
        "efc:implementedBy",
        "efc:documentedIn"
    ]
    for node in graph.get("@graph", []):
        src = node.get("@id") or node.get("id")
        if not src:
            continue
        for key in edge_keys:
            if key in node:
                targets = node[key]
                if isinstance(targets, str):
                    targets = [targets]
                for tgt in targets:
                    yield (src, key, tgt)


def main():
    root = Path(__file__).resolve().parents[1]
    graph_path = root / "meta-graph" / "meta-graph.jsonld"

    graph = load_meta_graph(graph_path)

    print("Nodes:")
    for n in iter_nodes(graph):
        nid = n.get("@id") or n.get("id")
        ntype = n.get("@type") or n.get("type")
        name = n.get("schema:name") or n.get("name")
        layer = n.get("efc:layer") or n.get("layer")
        print(f"  - {nid}  [{ntype}]  name={name!r}  layer={layer!r}")

    print("\nEdges:")
    for src, rel, tgt in iter_edges(graph):
        print(f"  {src} --{rel}--> {tgt}")


if __name__ == "__main__":
    main()
