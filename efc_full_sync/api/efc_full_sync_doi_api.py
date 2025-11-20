#!/usr/bin/env python3
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

THIS_ROOT = Path(__file__).resolve().parents[1]  # efc_full_sync/
REPO_ROOT = THIS_ROOT.parents[0]

DOCS_EFC_ROOT = REPO_ROOT / "docs" / "papers" / "efc"
META_MAP_PATH = THIS_ROOT / "meta" / "EFC_FULL_SYNC_META_MAP.json"
SCHEMA_MAP_PATH = THIS_ROOT / "schema" / "efc_full_sync_schema_map.json"

app = FastAPI(title="EFC Full Sync DOI API")


class DOIPayload(BaseModel):
    slug: str
    doi: str | None = None
    version_doi: str | None = None
    figshare_id: int | None = None


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.post("/efc_full_sync/doi-sync")
def doi_sync(payload: DOIPayload):
    slug = payload.slug
    paper_dir = DOCS_EFC_ROOT / slug
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail=f"Paper dir not found for slug: {slug}")

    doi = payload.doi
    version_doi = payload.version_doi
    figshare_id = payload.figshare_id

    # index.json
    index_path = paper_dir / "index.json"
    index_data = load_json(index_path, {})
    if doi:
        index_data["doi"] = doi
    if version_doi:
        index_data["version_doi"] = version_doi
    if figshare_id is not None:
        index_data["figshare_id"] = figshare_id
    save_json(index_path, index_data)

    # schema.json
    schema_path = paper_dir / "schema.json"
    schema_data = load_json(schema_path, {})
    if doi:
        schema_data["doi"] = doi
    save_json(schema_path, schema_data)

    # META map
    meta_map = load_json(META_MAP_PATH, [])
    for e in meta_map:
        if e.get("slug") == slug:
            if doi:
                e["doi"] = doi
            if version_doi:
                e["version_doi"] = version_doi
            if figshare_id is not None:
                e["figshare_id"] = figshare_id
    save_json(META_MAP_PATH, meta_map)

    # schema map
    schema_map = load_json(SCHEMA_MAP_PATH, [])
    for e in schema_map:
        if e.get("slug") == slug:
            if doi:
                e["doi"] = doi
            if version_doi:
                e["version_doi"] = version_doi
            if figshare_id is not None:
                e["figshare_id"] = figshare_id
    save_json(SCHEMA_MAP_PATH, schema_map)

    return {"status": "ok", "slug": slug, "doi": doi, "version_doi": version_doi}
