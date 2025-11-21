from pathlib import Path
import json
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = ROOT / "docs" / "papers" / "efc"
SCHEMA_ROOT = ROOT / "schema"
DATA_ROOT = ROOT / "data"

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
)

def upsert(tx, query, params):
    tx.run(query, **params)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def sync_papers(session):
    for meta_path in PAPER_ROOT.rglob("metadata.json"):
        meta = load_json(meta_path)
        slug = meta["slug"]
        title = meta["title"]
        domain = meta["domain"]
        files = meta["files"]
        # enkel versjon
        session.write_transaction(
            upsert,
            """
            MERGE (p:Paper {slug: $slug})
            SET p.title = $title,
                p.domain = $domain,
                p.path = $path
            """,
            {
                "slug": slug,
                "title": title,
                "domain": domain,
                "path": str(meta_path.parent.relative_to(ROOT))
            }
        )
        # Domain-node
        session.write_transaction(
            upsert,
            """
            MERGE (d:Domain {id: $domain})
            MERGE (p:Paper {slug: $slug})-[:IN_DOMAIN]->(d)
            """,
            {"domain": domain, "slug": slug}
        )
