#!/usr/bin/env python3
import os
from pathlib import Path

from neo4j import GraphDatabase, basic_auth

NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

CYHER_FILES = [
    "neo4j/efc_schema.cypher",
    "neo4j/efc_seed_concepts.cypher",
    "neo4j/efc_papers.cypher",
    # valgfritt, hvis du bruker auto-generert:
    "neo4j/generated_papers.cypher",
]

def load_statements(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    # veldig enkel split: én statement per ';'
    raw = text.split(";")
    stmts = []
    for chunk in raw:
        s = chunk.strip()
        if not s:
            continue
        # Neo4j trenger ikke ';' på slutten
        stmts.append(s)
    return stmts

def run_file(driver, filepath: str):
    p = Path(filepath)
    if not p.exists():
        print(f"[skip] {filepath} finnes ikke")
        return
    print(f"[run] {filepath}")
    stmts = load_statements(p)
    with driver.session(database=NEO4J_DATABASE) as session:
        for stmt in stmts:
            print(f"  -> {stmt[:80].replace('\\n', ' ')}...")
            session.run(stmt)

def main():
    auth = basic_auth(NEO4J_USERNAME, NEO4J_PASSWORD)
    driver = GraphDatabase.driver(NEO4J_URI, auth=auth)
    try:
        for f in CYHER_FILES:
            run_file(driver, f)
    finally:
        driver.close()

if __name__ == "__main__":
    main()
