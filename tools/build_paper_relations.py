#!/usr/bin/env python3
"""
Auto-generert Paper → MetaNode-relasjoner.

Systemet identifiserer meta-lag automatisk via patterns i:
- slug
- title
- keywords

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
# 1. Meta-category patterns
# ------------------------------------------------------------
META_CATEGORIES = {
    "s0s1": ["s0", "s1", "collapse", "bell", "drag", "entropy", "flow"],
    "entropy_clarity": ["entropy", "clarity", "gradient", "information"],
    "grid": ["grid", "higgs", "entropic", "geometry", "spacetime"],
    "cosmic": ["galactic", "cluster", "cosmic", "cmb", "redshift"],
    "meta_process": ["workflow", "process", "framework", "method"],
    "reflection": ["ego", "mirror", "insight", "signature"],
    "architecture": ["architecture", "pattern", "topology", "integration"],
    "global": ["applications", "implications", "complete", "v2.1", "v2.2"]
}

# ------------------------------------------------------------
# 2. Neo4j driver
# ------------------------------------------------------------
def get_driver():
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )

# ------------------------------------------------------------
# 3. Query to get all papers
# ------------------------------------------------------------
def fetch_papers(tx):
    q = """
    MATCH (p:EFCPaper)
    RETURN p.id AS id, p.slug AS slug, p.title AS title, p.keywords AS keywords
    """
    return list(tx.run(q))

# ------------------------------------------------------------
# 4. Auto-classify paper into meta-categories
# ------------------------------------------------------------
def classify_paper(paper):
    slug = paper["slug"].lower()
    title = (paper["title"] or "").lower()
    keywords = [k.lower() for k in (paper["keywords"] or [])]

    text = " ".join([slug, title] + keywords)

    matches = {}
    matched_categories = []

    for meta, patterns in META_CATEGORIES.items():
        hits = [p for p in patterns if p in text]
        if hits:
            matched_categories.append(meta)
            matches[meta] = hits

    if not matched_categories:
        matched_categories = ["global"]
        matches = {"fallback": ["no-match"]}

    # confidence based on how many patterns triggered
    total_patterns = sum(len(v) for v in META_CATEGORIES.values())
    activated = sum(len(v) for v in matches.values())
    confidence = round(activated / total_patterns, 3)

    return matched_categories, confidence, matches

# ------------------------------------------------------------
# 5. Create relation
# ------------------------------------------------------------
def create_rel(tx, pid, mid, confidence, rules):
    tx.run(
        """
        MATCH (p:EFCPaper {id: $pid})
        MATCH (m:MetaNode {id: $mid})
        MERGE (p)-[r:ADDRESSES]->(m)
        SET r.confidence = $confidence,
            r.rules = $rules
        """,
        pid=pid,
        mid=mid,
        confidence=confidence,
        rules=rules
    )

# ------------------------------------------------------------
# 6. MAIN
# ------------------------------------------------------------
def main():
    driver = get_driver()
    with driver.session() as session:

        # -- Neo4j 5.x AURA FIX --
        papers = session.execute_read(fetch_papers)

        print(f"[PaperRelations] Fant {len(papers)} papers.")

        for p in papers:
            pid = p["id"]

            categories, confidence, rulemap = classify_paper(p)

            for meta in categories:
                mid = meta
                rules = rulemap.get(meta, [])

                session.execute_write(
                    create_rel,
                    pid,
                    mid,
                    confidence,
                    rules
                )

            print(f"[PaperRelations] {pid} → {categories} (conf={confidence})")

    print("[PaperRelations] FULLFØRT — Auto-relasjoner generert.")


if __name__ == "__main__":
    main()
