#!/usr/bin/env python3
"""
EFC Full Sync Builder — komplett versjon
Oppdatert for Docker-basert Mermaid-rendering.
Ingen lokal mmdc. Workflow genererer SVG/PNG.
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# -----------------------------------------------------
# PATHS
# -----------------------------------------------------

THIS_ROOT = Path(__file__).resolve().parents[1]       # efc_full_sync/
REPO_ROOT = THIS_ROOT.parents[0]                     # repo/
PROD_LATEX = THIS_ROOT / "production" / "latex"      # produksjonsflate
SCHEMA_GLOBAL = THIS_ROOT / "schema" / "efc_full_sync_global_schema.json"
SCHEMA_MAP = THIS_ROOT / "schema" / "efc_full_sync_schema_map.json"
META_MAP = THIS_ROOT / "meta" / "EFC_FULL_SYNC_META_MAP.json"

DOCS_ROOT = REPO_ROOT / "docs" / "papers" / "efc"    # der ferdig artikkel havner
TEMPLATES = THIS_ROOT / "templates"

# -----------------------------------------------------
# UTILITY
# -----------------------------------------------------

def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def run(cmd):
    """Brukes kun for LaTeX / systemkall — IKKE for mermaid."""
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"[efc_full_sync] Kommando feilet: {cmd}\n"
            f"STDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout

# -----------------------------------------------------
# VALIDATOR — henter inn ekstern fil
# -----------------------------------------------------

from efc_full_sync_validator import validate_basic

# -----------------------------------------------------
# MERMAID — Docker-rendering
# -----------------------------------------------------

def build_mermaid_figures():
    """
    Workflow (GitHub Actions) rendrer alle .mmd → .svg/.png via Docker.
    Her sjekker vi bare at workflowen har produsert filene.
    """
    figdir = PROD_LATEX / "figures"
    if not figdir.exists():
        print("[efc_full_sync] Ingen figures/ mappe — hopper over mermaid.")
        return

    for mmd in figdir.glob("*.mmd"):
        svg = mmd.with_suffix(".svg")
        png = mmd.with_suffix(".png")

        if not svg.exists() or not png.exists():
            raise FileNotFoundError(
                f"[efc_full_sync] Mermaid-render mangler for {mmd.name}. "
                f"SVG eller PNG ikke funnet. Workflow må generere disse."
            )

    print("[efc_full_sync] Mermaid-figurer OK (docker-render).")

# -----------------------------------------------------
# LATEX → PDF
# -----------------------------------------------------

def build_pdf(slug):
    tex = PROD_LATEX / "paper.tex"
    if not tex.exists():
        raise FileNotFoundError(f"[efc_full_sync] paper.tex mangler: {tex}")

    # bygg i produksjonsmappen
    run(f"cd {PROD_LATEX} && latexmk -pdf -halt-on-error paper.tex")

    pdf = PROD_LATEX / "paper.pdf"
    if not pdf.exists():
        raise RuntimeError("[efc_full_sync] PDF ble ikke generert.")

    print("[efc_full_sync] PDF OK:", pdf)
    return pdf

# -----------------------------------------------------
# TEMPLATE RENDERING
# -----------------------------------------------------

def render_template(path, context):
    from jinja2 import Template
    tmpl = Template(path.read_text(encoding="utf-8"))
    return tmpl.render(context)

def generate_outputs(meta):
    slug = meta["slug"]
    outdir = DOCS_ROOT / slug
    outdir.mkdir(parents=True, exist_ok=True)

    context = {
        "meta": meta,
        "created": datetime.utcnow().isoformat() + "Z"
    }

    # Markdown (paper)
    md_tmpl = TEMPLATES / "efc_full_sync_paper.md.j2"
    (outdir / f"{slug}.md").write_text(render_template(md_tmpl, context), encoding="utf-8")

    # README
    readme_tmpl = TEMPLATES / "efc_full_sync_readme.md.j2"
    (outdir / "README.md").write_text(render_template(readme_tmpl, context), encoding="utf-8")

    # JSON-LD
    jsonld_tmpl = TEMPLATES / "efc_full_sync_jsonld.json.j2"
    jsonld = render_template(jsonld_tmpl, context)
    (outdir / f"{slug}.jsonld").write_text(jsonld, encoding="utf-8")

    # index.json
    index_tmpl = TEMPLATES / "efc_full_sync_index.json.j2"
    (outdir / "index.json").write_text(render_template(index_tmpl, context), encoding="utf-8")

    # schema.json
    schema_tmpl = TEMPLATES / "efc_full_sync_schema.json.j2"
    (outdir / "schema.json").write_text(render_template(schema_tmpl, context), encoding="utf-8")

    # citations.bib
    bib_tmpl = TEMPLATES / "efc_full_sync_citations.bib.j2"
    (outdir / "citations.bib").write_text(render_template(bib_tmpl, context), encoding="utf-8")

    # kopier figurer
    figout = outdir / "figures"
    figout.mkdir(exist_ok=True)

    for f in (PROD_LATEX / "figures").glob("*.*"):
        shutil.copy(f, figout / f.name)

    print("[efc_full_sync] Templates, metadata og figurer generert i:", outdir)

# -----------------------------------------------------
# FIGSHARE
# -----------------------------------------------------

from efc_full_sync_figshare import publish_pdf_to_figshare

# -----------------------------------------------------
# GLOBAL MAPS
# -----------------------------------------------------

def update_global_maps(meta):
    slug = meta["slug"]

    # schema map
    schema_map = load_json(SCHEMA_MAP, {"items": []})
    if slug not in [i.get("slug") for i in schema_map["items"]]:
        schema_map["items"].append({"slug": slug})
        save_json(SCHEMA_MAP, schema_map)

    # meta map
    meta_map = load_json(META_MAP, {"items": []})
    if slug not in [i.get("slug") for i in meta_map["items"]]:
        meta_map["items"].append({"slug": slug})
        save_json(META_MAP, meta_map)

    print("[efc_full_sync] Global maps oppdatert.")

# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():
    print("[efc_full_sync] Starter full pipeline…")

    # 1) Valider alt
    meta = validate_basic()

    # 2) Sjekk mermaid (svg/png generert av workflow)
    build_mermaid_figures()

    # 3) Lag PDF
    pdf_path = build_pdf(meta["slug"])

    # 4) Last opp til Figshare (dersom token)
    doi_info = publish_pdf_to_figshare(
        title=meta["title"],
        description=meta["description"],
        keywords=meta["keywords"],
        pdf_path=pdf_path
    )

    if doi_info:
        meta["doi"] = doi_info.get("doi")
        meta["version_doi"] = doi_info.get("version_doi")
        meta["figshare_id"] = doi_info.get("figshare_id")

        # skriv tilbake metadata.json → oppdatert
        save_json(PROD_LATEX / "metadata.json", meta)

    # 5) Generer alt
    generate_outputs(meta)

    # 6) Oppdater globale kart
    update_global_maps(meta)

    print("[efc_full_sync] ✔ Ferdig.")


if __name__ == "__main__":
    main()
