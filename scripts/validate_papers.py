#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED_FILES = [
    "README.md",
    "schema.json",
    "citations.bib",
]

REQUIRED_JSONLD_FIELDS = [
    "@context",
    "@type",
    "identifier",
    "name",
    "version",
    "author"
]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"JSON_ERROR: {e}"


def validate_jsonld(path: Path, folder_name: str, errors: list):
    data = load_json(path)
    if isinstance(data, str):  # error message
        errors.append(f"Invalid JSON-LD ({path.name}): {data}")
        return None

    # required fields
    for field in REQUIRED_JSONLD_FIELDS:
        if field not in data:
            errors.append(f"Missing required field '{field}' in JSON-LD")

    # id consistency
    if data.get("identifier") != folder_name:
        errors.append(
            f"Identifier mismatch: JSON-LD '{data.get('identifier')}' != folder '{folder_name}'"
        )

    # author validity
    author = data.get("author", {})
    if "name" not in author:
        errors.append("JSON-LD author missing name")

    if "version" not in data:
        errors.append("JSON-LD missing version")

    return data


def validate_index(path: Path, folder_name: str, errors: list):
    data = load_json(path)
    if isinstance(data, str):
        errors.append(f"Invalid index.json: {data}")
        return None

    if data.get("id") != folder_name:
        errors.append(
            f"index.json id mismatch: '{data.get('id')}' != '{folder_name}'"
        )

    if "keywords" not in data or not data["keywords"]:
        errors.append("index.json missing keywords list")

    if "version" not in data:
        errors.append("index.json missing version")

    return data


def validate_citations(path: Path, folder_name: str, errors: list):
    content = path.read_text(encoding="utf-8")
    if folder_name.lower().replace(" ", "") not in content.lower().replace(" ", ""):
        errors.append("citations.bib does not appear to contain correct ID or bibkey")
    return True


def validate_paper_dir(paper_dir: Path):
    folder_name = paper_dir.name
    errors = []
    warnings = []
    passed = True

    print(f"\n=== Validating {folder_name} ===")

    # Required basic files
    for req in REQUIRED_FILES:
        if not (paper_dir / req).exists():
            errors.append(f"Missing required file: {req}")

    # JSON-LD
    jsonld_path = paper_dir / f"{folder_name}.jsonld"
    if not jsonld_path.exists():
        errors.append(f"Missing JSON-LD file: {jsonld_path.name}")
        jsonld = None
    else:
        jsonld = validate_jsonld(jsonld_path, folder_name, errors)

    # index.json
    index_path = paper_dir / "index.json"
    if not index_path.exists():
        errors.append("Missing index.json")
        index_json = None
    else:
        index_json = validate_index(index_path, folder_name, errors)

    # citations
    bib_path = paper_dir / "citations.bib"
    if bib_path.exists():
        validate_citations(bib_path, folder_name, errors)

    # PDF
    pdf_path = paper_dir / f"{folder_name}.pdf"
    if not pdf_path.exists():
        warnings.append("PDF missing (expected for drafts)")

    # MD
    md_path = paper_dir / f"{folder_name}.md"
    if not md_path.exists():
        warnings.append("Markdown missing (expected for drafts)")

    # schema.json validity
    schema_path = paper_dir / "schema.json"
    if schema_path.exists():
        schema_data = load_json(schema_path)
        if isinstance(schema_data, str):
            errors.append(f"schema.json invalid JSON: {schema_data}")
    else:
        errors.append("Missing schema.json")

    # Final report
    if errors:
        passed = False
        print("✖ ERRORS:")
        for e in errors:
            print("  -", e)
    else:
        print("✔ No structural errors")

    if warnings:
        print("! WARNINGS:")
        for w in warnings:
            print("  -", w)

    print(f"Result: {'PASS' if passed else 'FAIL'}")
    return passed


def main():
    repo_root = Path(__file__).resolve().parent.parent
    papers_root = repo_root / "docs" / "papers" / "efc"

    if not papers_root.exists():
        print(f"[ERROR] Papers directory not found: {papers_root}")
        sys.exit(1)

    paper_dirs = [d for d in papers_root.iterdir() if d.is_dir()]
    if not paper_dirs:
        print("[ERROR] No paper directories found.")
        sys.exit(1)

    print(f"[INFO] Validating {len(paper_dirs)} papers in {papers_root}")

    total = len(paper_dirs)
    failures = 0

    for d in paper_dirs:
        if not validate_paper_dir(d):
            failures += 1

    print("\n----------------------------------")
    print(f"Validated: {total} papers")
    print(f"Failures:  {failures}")
    print(f"Passed:    {total - failures}")
    print("----------------------------------")

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
