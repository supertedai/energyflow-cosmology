#!/usr/bin/env python3
# tools/inspect_symbiosis_graph.py

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_URI og NEO4J_PASSWORD må være satt.")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


# ---------------------------------------------
# Helper: count nodes
# ---------------------------------------------
def count(label):
    with driver.session() as s:
        return s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]


# ---------------------------------------------
# Helper: count specific node by id
# ---------------------------------------------
def exists(label, id_value):
    with driver.session() as s:
        res = s.run(
            f"MATCH (n:{label} {{id:$id}}) RETURN count(n) AS c",
            id=id_value
        ).single()["c"]
    return res == 1


# ---------------------------------------------
# Helper: count relationships
# ---------------------------------------------
def count_rel(type_):
    with driver.session() as s:
        return s.run(
            f"MATCH ()-[r:{type_}]->() RETURN count(r) AS c"
        ).single()["c"]


# ---------------------------------------------
# CHECK DEFINITIONS
# ---------------------------------------------
expected_labels = [
    "Concept",
    "EFCPaper",
    "MetaProcess",
    "SemanticAxis",
    "SymbiosisArch",
    "PaperGroup",
    "IMXClass",
    "GraphInterface",
    "Insight",
    "MetaPattern",
    "CognitiveMechanism",
    "Symbiosis",
]

expected_nodes = {
    ("MetaProcess", "mp:reflection-loop"),
    ("MetaProcess", "mp:entropy-clarity-cycle"),
    ("MetaProcess", "mp:cross-domain-alignment"),

    ("SemanticAxis", "axis:structure"),
    ("SemanticAxis", "axis:dynamics"),
    ("SemanticAxis", "axis:entropy"),
    ("SemanticAxis", "axis:information"),
    ("SemanticAxis", "axis:resonance"),
    ("SemanticAxis", "axis:meta-integration"),

    ("SymbiosisArch", "sym-arch:core"),
    ("SymbiosisArch", "sym-arch:ai-generic"),
    ("SymbiosisArch", "sym-arch:human-generic"),
    ("SymbiosisArch", "sym-arch:interface"),
    ("SymbiosisArch", "sym-arch:reflection-engine"),
    ("SymbiosisArch", "sym-arch:imx-coordinator"),

    ("PaperGroup", "pg:efc-core"),
    ("PaperGroup", "pg:efc-meta"),
    ("PaperGroup", "pg:efc-imx"),
    ("PaperGroup", "pg:efc-dynamics"),

    ("IMXClass", "imx:layer-structure"),
    ("IMXClass", "imx:code-unit"),
    ("IMXClass", "imx:semantic-channel"),
    ("IMXClass", "imx:sync-process"),

    ("GraphInterface", "gi:routing"),
    ("GraphInterface", "gi:semantic"),
    ("GraphInterface", "gi:rag-export"),
    ("GraphInterface", "gi:neo4j-cloud"),
}

expected_relations = [
    "PART_OF",
    "DEPENDS_ON",
    "ALIGNS_WITH_AXIS",
    "BELONGS_TO",
    "DEFINES_CLASS",
    "EXPOSES_INTERFACE",
    "HAS_ARCHITECTURE",
    "HAS_ROLE",
    "USES_INTERFACE",
    "USES_ENGINE",
    "COORDINATES_IMX",
]


# ---------------------------------------------
# MAIN CHECKER
# ---------------------------------------------
def main():

    print("\n=== ⭐ SYMBIOSIS GRAPH INSPECTION ⭐ ===\n")

    # ---- LABELS ----
    print("→ Sjekker labels:")
    for label in expected_labels:
        c = count(label)
        print(f"  {label:<20} {c} noder")
    print()

    # ---- NODES ----
    print("→ Sjekker forventede noder:")
    missing_nodes = []
    for label, id_value in expected_nodes:
        if not exists(label, id_value):
            missing_nodes.append((label, id_value))
            print(f"  MISSING: {label} {id_value}")
        else:
            print(f"  OK     : {label} {id_value}")

    print()

    # ---- RELATION TYPES ----
    print("→ Sjekker relasjonstyper:")
    missing_rels = []
    for rel in expected_relations:
        c = count_rel(rel)
        if c == 0:
            missing_rels.append(rel)
            print(f"  MISSING: {rel}")
        else:
            print(f"  OK     : {rel}  ({c} relasjoner)")

    print()

    # ---- SUMMARY ----
    if missing_nodes or missing_rels:
        print("❌ Symbiosis Graph har mangler.")
        print("Mangler noder:", missing_nodes)
        print("Mangler relasjoner:", missing_rels)
        exit(1)
    else:
        print("✅ Symbiosis Graph er komplett og konsistent.")
        exit(0)


if __name__ == "__main__":
    main()
