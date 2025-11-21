#!/usr/bin/env python3
"""
Bygger Paper-noder i Neo4j fra docs/papers/efc/*

For hver paper-mappe i docs/papers/efc:

  docs/papers/efc/<slug>/
      <slug>.jsonld   (valgfritt, brukes hvis finnes)
      <slug>.md       (fallback for tittel)
      README.md       (ikke strikt nødvendig her)

Oppretter noder:

  (p:Paper:EFCPaper {
      id: <slug>,
      slug: <slug>,
      title: <title>,
      path: "docs/papers/efc/<slug>",
      doi: <fra jsonld om finnes>,
      version: <fra jsonld om finnes>,
      keywords: [..]
  })

Relasjoner til MetaNode tar vi i neste steg (bevisst).
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = REPO_ROOT / "docs" / "papers" / "efc"


def get_driver():
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))


def slug_from_dir(d: Path) -> str:
    return d.name


def find_jsonld(dir_path: Path) -> Path | None:
    candidates = list(dir_path.glob("*.jsonld"))
    return candidates[0] if candidates else None


def find_md_main(dir_path: Path, slug: str) -> Path | None:
    # foretrekk <slug>.md, ellers første .md
    p = dir_path / f"{slug}.md"
    if p.exists():
        return p
    mds = list(dir_path.glob("*.md"))
    return mds[0] if mds else None


def extract_title_from_md(md_path: Path) -> str | None:
    """
    Enkel heuristikk:
    - første linje som starter med '# '
    """
    if not md_path or not md_path.exists():
        return None
    for line in md_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def load_paper_metadata(dir_path: Path) -> Dict[str, Any]:
    slug = slug_from_dir(dir_path)
    meta: Dict[str, Any] = {
        "id": slug,
        "slug": slug,
        "path": str(dir_path.relative_to(REPO_ROOT)),
        "title": slug,
        "version": None,
        "doi": None,
        "keywords": [],
    }

    jsonld_path = find_jsonld(dir_path)
    if jsonld_path:
        try:
            data = json.loads(jsonld_path.read_text(encoding="utf-8"))
            # Støtt både enkel og liste av @graph/@context-varianter senere om nødvendig
            meta["title"] = data.get("name", meta["title"])
            meta["version"] = data.get("version", None)
            meta["doi"] = data.get("identifier", None)

            # keywords kan hete 'keywords' eller 'about'
            kws = []
            if "keywords" in data and isinstance(data["keywords"], list):
                kws.extend([str(k) for k in data["keywords"]])
            if "about" in data:
                if isinstance(data["about"], list):
                    kws.extend([str(k) for k in data["about"]])
                else:
                    kws.append(str(data["about"]))
            meta["keywords"] = list(sorted(set(kws)))
        except Exception as e:
            print(f"[PaperGraph] Klarte ikke å lese JSON-LD for {slug}: {e}")

    # Fallback for tittel hvis JSON-LD ikke ga noe
    if not meta["title"] or meta["title"] == slug:
        md_main = find_md_main(dir_path, slug)
        t = extract_title_from_md(md_main) if md_main else None
        if t:
            meta["title"] = t

    return meta


def discover_papers(root: Path) -> List[Dict[str, Any]]:
    if not root.exists():
        print(f"[PaperGraph] PAPERS_ROOT finnes ikke: {root}")
        return []
    papers = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            meta = load_paper_metadata(child)
            papers.append(meta)
    return papers


def ingest_papers(tx, papers: List[Dict[str, Any]]):
    for p in papers:
        tx.run(
            """
            MERGE (paper:Paper:EFCPaper {id: $id})
            SET paper.slug = $slug,
                paper.title = $title,
                paper.path = $path,
                paper.version = $version,
                paper.doi = $doi,
                paper.keywords = $keywords
            """,
            **p,
        )


def main():
    print(f"[PaperGraph] Scanner {PAPERS_ROOT} ...")
    papers = discover_papers(PAPERS_ROOT)
    print(f"[PaperGraph] Fant {len(papers)} papers.")

    if not papers:
        print("[PaperGraph] Ingen papers å ingestere. Avslutter.")
        return

    driver = get_driver()
    with driver.session() as session:
        session.execute_write(ingest_papers, papers)

    print("[PaperGraph] Ingestion complete.")


if __name__ == "__main__":
    main()
