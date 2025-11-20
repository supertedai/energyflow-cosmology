#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from efc_full_sync_validator import validate_basic
from efc_full_sync_figshare import publish_pdf_to_figshare


THIS_ROOT = Path(__file__).resolve().parents[1]  # efc_full_sync/
REPO_ROOT = THIS_ROOT.parents[0]

PROD_LATEX = THIS_ROOT / "production" / "latex"
TEMPLATE_ROOT = THIS_ROOT / "templates"

DOCS_EFC_ROOT = REPO_ROOT / "docs" / "papers" / "efc"
META_MAP_PATH = THIS_ROOT / "meta" / "EFC_FULL_SYNC_META_MAP.json"
SCHEMA_MAP_PATH = THIS_ROOT / "schema" / "efc_full_sync_schema_map.json"

DOI_SYNC_URL = os.getenv("DOI_SYNC_URL", "")


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_subprocess(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=isinstance(cmd, str),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"[efc_full_sync] Kommando feilet: {cmd}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout


def build_mermaid_figures():
    fig_dir = PROD_LATEX / "figures"
    if not fig_dir.exists():
        return
    for mmd in fig_dir.glob("*.mmd"):
        svg = mmd.with_suffix(".svg")
        png = mmd.with_suffix(".png")
        run_subprocess(f"mmdc -i {mmd} -o {svg}")
        run_subprocess(f"mmdc -i {mmd} -o {png}")


def build_pdf(slug: str, out_dir: Path) -> Path:
    cmd = "latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex"
    run_subprocess(cmd, cwd=PROD_LATEX)

    pdf_source = PROD_LATEX / "paper.pdf"
    if not pdf_source.exists():
        pdfs = list(PROD_LATEX.glob("*.pdf"))
        if not pdfs:
            raise FileNotFoundError("[efc_full_sync] Fant ingen PDF etter bygg.")
        pdf_source = pdfs[0]

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{slug}.pdf"
    shutil.copy2(pdf_source, target)

    if target.stat().st_size == 0:
        raise RuntimeError("[efc_full_sync] Generert PDF er tom.")

    return target


def copy_figures(out_dir: Path, meta: dict):
    src = PROD_LATEX / "figures"
    if not src.exists():
        return
    dst = out_dir / "figures"
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)


def render_templates(meta: dict, doi_info: dict | None, out_dir: Path):
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_ROOT)))
    now_iso = datetime.utcnow().isoformat() + "Z"
    slug = meta["slug"]

    ctx = {
        "slug": slug,
        "title": meta["title"],
        "version": meta["version"],
        "authors": meta["authors"],
        "description": meta["description"],
        "keywords": meta["keywords"],
        "figures": meta.get("figures", []),
        "timestamp": now_iso,
        "doi": (doi_info or {}).get("doi"),
        "version_doi": (doi_info or {}).get("version_doi"),
        "figshare_id": (doi_info or {}).get("figshare_id"),
    }

    def render(name_j2: str, target: str):
        tmpl = env.get_template(name_j2)
        text = tmpl.render(**ctx)
        target_path = out_dir / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as f:
            f.write(text)

    render("efc_full_sync_readme.md.j2", "README.md")
    render("efc_full_sync_paper.md.j2", f"{slug}.md")
    render("efc_full_sync_jsonld.json.j2", f"{slug}.jsonld")
    render("efc_full_sync_index.json.j2", "index.json")
    render("efc_full_sync_schema.json.j2", "schema.json")
    render("efc_full_sync_citations.bib.j2", "citations.bib")


def update_global_maps(meta: dict, doi_info: dict | None):
    slug = meta["slug"]
    now_iso = datetime.utcnow().isoformat() + "Z"

    entry = {
        "slug": slug,
        "title": meta["title"],
        "version": meta["version"],
        "path": f"docs/papers/efc/{slug}/",
        "pdf": f"{slug}.pdf",
        "jsonld": f"{slug}.jsonld",
        "updated": now_iso,
    }
    if doi_info:
        entry["doi"] = doi_info.get("doi")
        entry["version_doi"] = doi_info.get("version_doi")
        entry["figshare_id"] = doi_info.get("figshare_id")

    meta_map = load_json(META_MAP_PATH, [])
    meta_map = [e for e in meta_map if e.get("slug") != slug]
    meta_map.append(entry)
    save_json(META_MAP_PATH, meta_map)

    schema_map = load_json(SCHEMA_MAP_PATH, [])
    schema_map = [e for e in schema_map if e.get("slug") != slug]
    schema_map.append(entry)
    save_json(SCHEMA_MAP_PATH, schema_map)


def send_doi_to_sync_api(meta: dict, doi_info: dict | None):
    if not DOI_SYNC_URL or not doi_info:
        return
    import requests

    payload = {
        "slug": meta["slug"],
        "doi": doi_info.get("doi"),
        "version_doi": doi_info.get("version_doi"),
        "figshare_id": doi_info.get("figshare_id"),
    }
    r = requests.post(DOI_SYNC_URL, json=payload, timeout=30)
    r.raise_for_status()


def main():
    # 1) Valider alt "billig"
    meta = validate_basic()
    slug = meta["slug"]

    # 2) Mermaid-figurer
    build_mermaid_figures()

    # 3) Bygg PDF + kopier figurer
    out_dir = DOCS_EFC_ROOT / slug
    pdf_path = build_pdf(slug, out_dir)
    copy_figures(out_dir, meta)

    # 4) Figshare (hvis token satt)
    doi_info = publish_pdf_to_figshare(
        title=meta["title"],
        description=meta["description"],
        keywords=meta.get("keywords", []),
        pdf_path=pdf_path,
    )

    # 5) Templates
    render_templates(meta, doi_info, out_dir)

    # 6) Globale kart
    update_global_maps(meta, doi_info)

    # 7) Oppdater metadata.json med DOI
    if doi_info:
        meta["doi"] = doi_info.get("doi")
        meta["version_doi"] = doi_info.get("version_doi")
        meta["figshare_id"] = doi_info.get("figshare_id")
        meta_path = PROD_LATEX / "metadata.json"
        save_json(meta_path, meta)

        # 8) DOI-sync API (valgfritt)
        send_doi_to_sync_api(meta, doi_info)

    print(f"[efc_full_sync] Ferdig bygget paper for slug: {slug}")


if __name__ == "__main__":
    main()
