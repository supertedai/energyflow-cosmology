#!/usr/bin/env python3
"""
Bygger Neo4j-grafen fra meta-graph/nodes.md og meta-graph/edges.md

- Leser kategorier + noder fra nodes.md
- Leser relasjoner fra edges.md (### A → B, ### A ↔ B ↔ C)
- Slugifier navn til stabile id-er
- Skriver noder og relasjoner inn i Neo4j
"""

import os
import re
from pathlib import Path
from neo4j import GraphDatabase

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
META_GRAPH_DIR = REPO_ROOT / "meta-graph"
NODES_MD = META_GRAPH_DIR / "nodes.md"
EDGES_MD = META_GRAPH_DIR / "edges.md"

# ---------------------------------------------------------
# Utils
# ---------------------------------------------------------

def slugify(name: str) -> str:
    """Enkel slug: lower, A–Z0–9, '-'."""
    s = name.strip().lower()
    s = re.sub(r"[\(\)\[\]]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


# ---------------------------------------------------------
# Parse nodes.md
# ---------------------------------------------------------

def parse_nodes_md(path: Path):
    """
    Forventer struktur ala:

    # Meta-Graph Nodes

    ## Cognition Nodes
    - Cognitive Field Model (CFM)
    - Entropy → Clarity Model
    ...

    Returnerer liste dicts:
    {id, name, category}
    """
    if not path.exists():
        raise FileNotFoundError(f"nodes.md ikke funnet: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    nodes = []
    current_cat = None

    for line in lines:
        line = line.rstrip()

        if line.startswith("## "):
            # kategori
            current_cat = line[3:].strip()
        elif line.startswith("- "):
            name = line[2:].strip()
            if not name:
                continue
            node_id = slugify(name)
            nodes.append(
                {
                    "id": node_id,
                    "name": name,
                    "category": current_cat,
                }
            )

    return nodes


# ---------------------------------------------------------
# Parse edges.md
# ---------------------------------------------------------

def parse_edges_md(path: Path):
    """
    Forventer struktur ala:

    # Meta-Graph Relations (Edges)

    ### Cognition → Reflection
    - Insight stabilisation
    - Recursive interpretation

    ### Cognition ↔ Co-Field ↔ MSE
    - resonance loops
    ...

    Returnerer liste dicts:
    {source, target, relation, group}
    """
    if not path.exists():
        raise FileNotFoundError(f"edges.md ikke funnet: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    edges = []
    current_pairs = []
    current_title = None

    for line in lines:
        line = line.rstrip()

        if line.startswith("### "):
            current_title = line[4:].strip()
            current_pairs = []

            # støtt både → og ↔
            if "→" in current_title:
                parts = [p.strip() for p in current_title.split("→") if p.strip()]
                for i in range(len(parts) - 1):
                    current_pairs.append((parts[i], parts[i + 1]))
            elif "↔" in current_title:
                parts = [p.strip() for p in current_title.split("↔") if p.strip()]
                # gjør det som dobbeltrettede kanter
                for i in range(len(parts) - 1):
                    a, b = parts[i], parts[i + 1]
                    current_pairs.append((a, b))
                    current_pairs.append((b, a))
            else:
                # ukjent format – ignorer
                current_pairs = []

        elif line.startswith("- ") and current_pairs:
            rel = line[2:].strip()
            if not rel:
                continue
            for src_name, dst_name in current_pairs:
                edges.append(
                    {
                        "source": slugify(src_name),
                        "target": slugify(dst_name),
                        "relation": rel,
                        "group": current_title,
                    }
                )

    return edges


# ---------------------------------------------------------
# Neo4j
# ---------------------------------------------------------

def get_driver():
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def ingest_nodes(tx, nodes):
    for node in nodes:
        tx.run(
            """
            MERGE (n:MetaNode {id: $id})
            SET n.name = $name,
                n.category = $category
            """,
            id=node["id"],
            name=node["name"],
            category=node.get("category"),
        )


def ingest_edges(tx, edges):
    for edge in edges:
        tx.run(
            """
            MATCH (a:MetaNode {id: $src})
            MATCH (b:MetaNode {id: $dst})
            MERGE (a)-[r:REL {relation: $relation}]->(b)
            SET r.group = $group
            """,
            src=edge["source"],
            dst=edge["target"],
            relation=edge["relation"],
            group=edge.get("group"),
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    print("[Neo4j] Leser meta-graph/nodes.md og meta-graph/edges.md ...")
    nodes = parse_nodes_md(NODES_MD)
    edges = parse_edges_md(EDGES_MD)

    # sørg for at alle konsept-navn fra relasjoner finnes som noder
    node_ids = {n["id"] for n in nodes}
    extra_nodes = []

    for e in edges:
        for key in ("source", "target"):
            nid = e[key]
            if nid not in node_ids:
                # lag en enkel node med name = id
                extra_nodes.append(
                    {"id": nid, "name": nid, "category": "RelGroup"}
                )
                node_ids.add(nid)

    if extra_nodes:
        print(f"[Neo4j] Fant {len(extra_nodes)} ekstra noder fra relasjoner.")
        nodes.extend(extra_nodes)

    print(f"[Neo4j] Klar til ingest: {len(nodes)} noder, {len(edges)} kanter.")

    driver = get_driver()
    with driver.session() as session:
        session.execute_write(ingest_nodes, nodes)
        session.execute_write(ingest_edges, edges)

    print("[Neo4j] Ingestion complete.")


if __name__ == "__main__":
    main()
