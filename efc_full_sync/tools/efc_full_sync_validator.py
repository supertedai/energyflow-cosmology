#!/usr/bin/env python3
import json
import re
from pathlib import Path


THIS_ROOT = Path(__file__).resolve().parents[1]  # efc_full_sync/
REPO_ROOT = THIS_ROOT.parents[0]

PROD_LATEX = THIS_ROOT / "production" / "latex"
SCHEMA_GLOBAL_PATH = THIS_ROOT / "schema" / "efc_full_sync_global_schema.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_metadata_structure(meta: dict):
    required = ["slug", "title", "version", "authors", "description", "keywords"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise ValueError(f"[efc_full_sync] metadata.json mangler felt: {', '.join(missing)}")

    slug = meta["slug"]
    if not isinstance(slug, str) or not re.fullmatch(r"[A-Za-z0-9\-]+", slug):
        raise ValueError(f"[efc_full_sync] slug '{slug}' er ugyldig. Kun A–Z, a–z, 0–9 og '-' tillatt.")

    if not isinstance(meta["title"], str) or len(meta["title"].strip()) < 3:
        raise ValueError("[efc_full_sync] title er for kort eller mangler.")

    if not isinstance(meta["version"], str) or not re.fullmatch(r"\d+\.\d+", meta["version"]):
        raise ValueError("[efc_full_sync] version må være på formen 'X.Y' f.eks. '1.0'.")

    authors = meta["authors"]
    if not isinstance(authors, list) or len(authors) == 0:
        raise ValueError("[efc_full_sync] authors må være en ikke-tom liste.")
    for a in authors:
        if "name" not in a or not a["name"]:
            raise ValueError("[efc_full_sync] Hver author må ha 'name'.")
        if "orcid" in a and a["orcid"]:
            if "orcid.org" not in a["orcid"]:
                raise ValueError(f"[efc_full_sync] ORCID ser rar ut: {a['orcid']}")

    desc = meta["description"]
    if not isinstance(desc, str) or len(desc.strip()) < 10:
        raise ValueError("[efc_full_sync] description er for kort.")

    keywords = meta["keywords"]
    if not isinstance(keywords, list) or len(keywords) < 3:
        raise ValueError("[efc_full_sync] keywords må være en liste med minst 3 elementer.")


def validate_figures_exist(meta: dict):
    fig_dir = PROD_LATEX / "figures"
    if not fig_dir.exists():
        return
    declared = meta.get("figures", [])
    for rel in declared:
        p = PROD_LATEX / rel
        if not p.exists():
            raise ValueError(f"[efc_full_sync] Figur oppgitt i metadata finnes ikke: {rel}")


def validate_schema(meta: dict):
    schema = load_json(SCHEMA_GLOBAL_PATH, {})
    if not schema:
        # Ingen global schema definert ennå -> hopp over
        return
    required_fields = schema.get("required_fields", [])
    missing = [k for k in required_fields if k not in meta]
    if missing:
        raise ValueError(
            f"[efc_full_sync] metadata mangler felt i henhold til efc_full_sync_global_schema.json: {missing}"
        )


def validate_tex_present():
    tex_file = PROD_LATEX / "paper.tex"
    if not tex_file.exists():
        raise FileNotFoundError(f"[efc_full_sync] paper.tex mangler i {PROD_LATEX}")


def validate_basic():
    """
    Kjør alle "billige" valideringer:
    - metadata-struktur
    - schema-krav
    - figurer finnes
    - paper.tex finnes
    """
    meta_path = PROD_LATEX / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"[efc_full_sync] metadata.json mangler i {PROD_LATEX}")
    meta = load_json(meta_path, None)
    if meta is None:
        raise RuntimeError("[efc_full_sync] metadata.json kunne ikke leses som JSON.")

    validate_metadata_structure(meta)
    validate_schema(meta)
    validate_figures_exist(meta)
    validate_tex_present()

    return meta  # returner for videre bruk


if __name__ == "__main__":
    # Enkel testkjøring
    m = validate_basic()
    print("[efc_full_sync] metadata OK for slug:", m["slug"])
