#!/usr/bin/env python3
"""
Auto-generert Paper → MetaNode-relasjoner.

Systemet identifiserer meta-lag automatisk via patterns:
- slug-ord
- title-ord
- keywords
- tematiske grupper

Output:
(:EFCPaper)-[:ADDRESSES {confidence:float, rules:list}]->(:MetaNode)
"""

import os
import re
import json
from pathlib import Path
from neo4j import GraphDatabase


REPO_ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------
# 1. Definer meta-lagene (autoritative labels)
# ------------------------------------------------------------
META_CATEGORIES = {
    "s0s1": ["s0", "s1", "collapse", "bell", "drag", "entropy", "flow"],
    "entropy_clarity": ["entropy", "clarity", "gradient", "information"],
    "grid": ["grid", "higgs", "field", "entropic", "geometry", "spacetime"],
    "cosmic": ["galactic", "clusters", "cosmic", "cmb", "redshift"],
    "meta_process": ["workflow", "process", "framework", "method"],
    "reflection": ["ego", "mirror", "insight", "reflection", "signature"],
    "architecture": ["architecture", "pattern", "topology", "integration"],
    "global": ["applications", "implications", "complete", "v2.1", "v2.2"]
}


# ------------------------------------------------------------
# 2. Hent EFCPapers fra Neo4j
# ------------------------------------------------------------
def get_driver():
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )


def fetch_papers(tx):
    q = """
    MATCH (p:EFCPaper)
    RETURN p.id AS id, p.slug AS slug, p.title AS title, p.keywords AS keywords
    """
    return list(tx.run(q))


# ------------------------------------------------------------
# 3. Pattern-matching funksjon
# ------------------------------------------------------------
def classify_paper(paper):
    slug = paper["slug"].lower()
    title = (paper["title"] or "").lower()
    keywords = [k.lower() for k in (paper["keywords"] or [])]

    text = " ".join([slug, title] + keywords)

    matched_categories = []
    match_rules = {}

    for meta, patterns in META_CATEGORIES.items():
        hits = [p for p in patterns if p in text]
        if hits:
            matched_categories.append(meta)
            match_rules[meta] = hits

    # hvis ingen treff: fallback
    if not matched_categories:
        matched_categories = ["global"]
        match_rules = {"fallback": ["no match"]}

    # confidence basert på hvor mange regler som trigget
    total_patterns = sum(len(p) for p in META_CATEGORIES.values())
    activated = sum(len(v) for v in match_rules.values())
    confidence = round(activated / total_patterns, 3)

    return matched_categories, confidence, match_rules


# ------------------------------------------------------------
# 4. Opprett relasjoner i Neo4j
# ------------------------------------------------------------
def create_rel(tx, pid, meta_id, confidence, rules):
    tx.run(
        """
        MATCH (p:EFCPaper {id: $pid})
        MATCH (m:MetaNode {id: $mid})
        MERGE (p)-[r:ADDRESSES]->(m)
        SET r.confidence = $confidence,
            r.rules = $rules
        """,
        pid=pid,
        mid=meta_id,
        confidence=confidence,
        rules=rules
    )


# ------------------------------------------------------------
# 5. MAIN
# ------------------------------------------------------------
def main():
    driver = get_driver()
    with driver.session() as session:

        papers = session.read_transaction(fetch_papers)

        print(f"[PaperRelations] Fant {len(papers)} papers i grafen.")

        for p in papers:
            pid = p["id"]
            categories, confidence, rules = classify_paper(p)

            for cat in categories:
                mid = cat  # MetaNode {id: "s0s1"} etc.
                session.write_transaction(
                    create_rel,
                    pid,
                    mid,
                    confidence,
                    list(rules.get(cat, []))
                )

            print(f"[PaperRelations] {pid}: {categories} (conf={confidence})")

    print("[PaperRelations] FULLFØRT: Auto-relasjoner generert.")


if __name__ == "__main__":
    main()
