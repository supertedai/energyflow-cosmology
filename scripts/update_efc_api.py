
Innhold:

```python
"""
update_efc_api.py
Auto-generates JSON-LD API endpoints under api/v1/ from schema/concepts.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILE = ROOT / "schema" / "concepts.json"
API_DIR = ROOT / "api" / "v1"


def main():
    print("🔄 Updating EFC Semantic API ...")

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Missing {SCHEMA_FILE}")

    API_DIR.mkdir(parents=True, exist_ok=True)

    # Load concept dataset
    data = json.loads(SCHEMA_FILE.read_text())

    if "@graph" not in data:
        raise ValueError("concepts.json must contain @graph")

    # Write index file
    index_path = API_DIR / "terms.json"
    index = [{"id": c.get("@id"), "name": c.get("name")} for c in data["@graph"]]
    index_path.write_text(json.dumps(index, indent=2))
    print(f"✓ Wrote term index: {index_path}")

    # Write individual concept files
    for c in data["@graph"]:
        cid = c["@id"].split("/")[-1]
        out = API_DIR / f"{cid}.json"
        out.write_text(json.dumps(c, indent=2))
        print(f"✓ Wrote concept: {out}")

    print("✨ API update complete.")


if __name__ == "__main__":
    main()
