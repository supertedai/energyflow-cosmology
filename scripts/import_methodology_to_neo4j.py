#!/usr/bin/env python3
"""
Import methodology layer into Neo4j.

- Creates one MethodologyProcess node (from open-process.json)
- Creates one MethodologyDocument node per .md in hasPart
- Connects them with :HAS_PART
"""

import os
import json
from pathlib import Path

from neo4j import GraphDatabase

# --- Config ---------------------------------------------------------

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

REPO_ROOT = Path(__file__).resolve().parent.parent
METHOD_DIR = REPO_ROOT / "methodology"
OPEN_PROCESS_PATH = METHOD_DIR / "open-process.json"


# --- Core logic -----------------------------------------------------

def load_open_process():
    with OPEN_PROCESS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def import_methodology(driver):
    data = load_open_process()

    process_id = data.get("@id")
    process_name = data.get("name")
    process_desc = data.get("description")

    has_part = data.get("hasPart", [])

    with driver.session() as session:
        # Process node
        session.run(
            """
            MERGE (p:MethodologyProcess {id: $id})
            SET p.name = $name,
                p.description = $description
            """,
            id=process_id,
            name=process_name,
            description=process_desc,
        )

        # Document nodes
        for part in has_part:
            name = part.get("name")
            enc = part.get("encodingFormat", "text/markdown")

            path = METHOD_DIR / name
            content = ""
            if path.exists():
                content = path.read_text(encoding="utf-8")

            session.run(
                """
                MERGE (d:MethodologyDocument {name: $name})
                SET d.encodingFormat = $enc,
                    d.path = $path,
                    d.content = $content
                """,
                name=name,
                enc=enc,
                path=str(path.relative_to(REPO_ROOT)),
                content=content,
            )

            session.run(
                """
                MATCH (p:MethodologyProcess {id: $pid}),
                      (d:MethodologyDocument {name: $name})
                MERGE (p)-[:HAS_PART]->(d)
                """,
                pid=process_id,
                name=name,
            )


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        import_methodology(driver)
        print("✅ Imported methodology layer into Neo4j")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
