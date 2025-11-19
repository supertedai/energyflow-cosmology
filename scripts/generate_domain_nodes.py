#!/usr/bin/env python3
import json
from pathlib import Path

TEMPLATE_DIR = Path("scripts/templates/domain_template")

def load_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[OK] wrote {path}")

def generate_node(path: Path, title: str, id_value: str, node_type: str):
    # index.md
    md_template = load_template("template_index.md")
    md_filled = md_template.replace("{TITLE}", title)
    write(path / "index.md", md_filled)

    # index.jsonld
    json_template = load_template("template_index.jsonld")
    json_filled = (
        json_template
        .replace("{TITLE}", title)
        .replace("{ID}", id_value)
        .replace("{TYPE}", node_type)
    )
    write(path / "index.jsonld", json_filled)

    # schema.json
    schema_template = load_template("template_schema.json")
    write(path / "schema.json", schema_template)

def main():
    repo = Path(".").resolve()

    # Domain map (all missing nodes will be created)
    DOMAINS = {
        "meta/meta-process/pattern": ("Pattern Layer", "meta-pattern-layer", "DefinedTerm"),
        "meta/meta-process/topology": ("Topology Layer", "meta-topology-layer", "DefinedTerm"),
        "meta/meta-process/integration": ("Integration Layer", "meta-integration-layer", "DefinedTerm"),
        "meta/metascope": ("Metascope", "meta-metascope", "Dataset"),
        "meta/symbiosis": ("Symbiosis Layer", "meta-symbiosis-layer", "DefinedTerm"),
        "meta-graph": ("EFC Semantic Graph Root", "efc-semantic-graph", "Dataset"),
        "auth": ("EFC Authorship Root", "efc-auth-root", "Person"),
        "schema": ("Schema Layer", "efc-schema-root", "Dataset"),
        "theory/formal": ("Formal Theory Specification", "efc-formal-spec", "CreativeWork"),
    }

    for rel_path, (title, identifier, type_) in DOMAINS.items():
        node_path = repo / rel_path

        if not (node_path / "index.jsonld").exists():
            print(f"[CREATE] {rel_path}")
            generate_node(node_path, title, identifier, type_)
        else:
            print(f"[SKIP] {rel_path} already exists")

    print("\n[DONE] Domain placeholders are generated.")

if __name__ == "__main__":
    main()
