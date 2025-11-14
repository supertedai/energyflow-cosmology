"""
update_efc_api.py
Auto-generates JSON-LD API endpoints under api/v1/ from schema/concepts.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "schema" / "concepts.json"
API_DIR = ROOT / "api" / "v1"


def extract_concepts(data):
    # Primary: @graph (JSON-LD canonical)
    if "@graph" in data:
        return data["@graph"]

    # Schema.org DefinedTermSet
    if "hasDefinedTerm" in data:
        return data["hasDefinedTerm"]

    # If data is a list
    if isinstance(data, list):
        return data

    # Nested DefinedTermSet
    for k, v in data.items():
        if isinstance(v, dict) and "hasDefinedTerm" in v:
            return v["hasDefinedTerm"]

    raise ValueError("Could not find concepts in concepts.json")


def main():
    print("🔄 Updating EFC Semantic API ...")

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Missing {SCHEMA_FILE}")

    API_DIR.mkdir(parents=True, exist_ok=True)

    data = json.loads(SCHEMA_FILE.read_text())

    concepts = extract_concepts(data)

    # Write index
    index_path = API_DIR / "terms.json"
    index = [{"id": c.get("@id"), "name": c.get("name")} for c in concepts]
    index_path.write_text(json.dumps(index, indent=2))
    print(f"✓ Wrote term index: {index_path}")

    # Write each concept
    for c in concepts:
        cid = c["@id"].split("/")[-1]
        out = API_DIR / f"{cid}.json"
        out.write_text(json.dumps(c, indent=2))
        print(f"✓ Wrote concept: {out}")

    print("✨ API update complete.")


if __name__ == "__main__":
    main()
