"""
Export the EFC metascope meta-graph to a Neo4j-compatible Cypher script.

Usage:
    python meta-graph/export_meta_graph_neo4j.py

This will write:
    meta-graph/meta_graph.cypher

You can then load it into Neo4j, e.g.:
    cypher-shell -u neo4j -p <password> -f meta-graph/meta_graph.cypher
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "meta-graph" / "meta-graph.jsonld"
OUT_PATH = ROOT / "meta-graph" / "meta_graph.cypher"


def load_graph() -> dict:
    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def to_rel_type(rel: str) -> str:
    rel = rel.replace("efc:", "")
    rel = rel.upper()
    rel = rel.replace(":", "_")
    return rel


def main():
    data = load_graph()
    nodes = data.get("@graph", [])

    lines: list[str] = []

    # constraint
    lines.append("CREATE CONSTRAINT IF NOT EXISTS FOR (n:MetaNode) REQUIRE n.id IS UNIQUE;")
    lines.append("")

    # nodes
    for n in nodes:
        nid = n.get("@id") or n.get("id")
        if not nid:
            continue

        name = n.get("name") or n.get("schema:name") or nid
        ntype = n.get("@type") or n.get("type") or "Node"
        layer = n.get("layer") or n.get("efc:layer") or "unknown"
        desc = n.get("description", "")

        line = (
            "MERGE (n:MetaNode {id: '%s'}) "
            "SET n.name = '%s', n.type = '%s', n.layer = '%s', n.description = '%s';"
            % (
                escape(nid),
                escape(name),
                escape(ntype) if isinstance(ntype, str) else escape(str(ntype)),
                escape(layer),
                escape(desc),
            )
        )
        lines.append(line)

    lines.append("")

    # edges
    edge_keys = {
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
        "efc:documentedIn",
    }

    for n in nodes:
        src = n.get("@id") or n.get("id")
        if not src:
            continue

        for key, targets in n.items():
            if key not in edge_keys:
                continue
            if isinstance(targets, str):
                targets = [targets]
            for tgt in targets:
                if not tgt:
                    continue
                rel_type = to_rel_type(key)
                line = (
                    "MATCH (a:MetaNode {id: '%s'}), (b:MetaNode {id: '%s'}) "
                    "MERGE (a)-[:%s]->(b);"
                    % (escape(src), escape(tgt), rel_type)
                )
                lines.append(line)

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Cypher export to: {OUT_PATH}")


if __name__ == "__main__":
    main()
