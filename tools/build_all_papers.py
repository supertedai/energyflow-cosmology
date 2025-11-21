#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC PAPER BUILDER v2
====================

Gjør for hver .tex-fil under docs/papers/efc/:

- Bygger PDF (dobbel pdflatex)
- Leser ut title, author, abstract, keywords fra LaTeX
- Henter eksisterende DOI om det finnes (fra metadata.json eller <slug>.jsonld)
- Skriver/oppdaterer:
    - README.md
    - metadata.json
    - index.json
    - <slug>.jsonld
    - citations.bib

Design:
- Trygt å kjøre om igjen (idempotent på filnivå)
- Overstyrer ikke eksisterende DOI-felt, bare fyller inn hvis tomt
"""

import os
import re
import json
import subprocess
from datetime import date
from slugify import slugify
from pathlib import Path

# --------------------------- Konfig ---------------------------

ROOT = os.path.dirname(os.path.dirname(__file__))  # repo-root/efc_full_sync/tools/.. -> repo-root
DOCS_ROOT = os.path.join(ROOT, "docs", "papers", "efc")

# Default GitHub-URL til repoet – kan overstyres via env
GITHUB_REPO_RAW_BASE = os.environ.get(
    "EFC_GITHUB_RAW_BASE",
    "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main",
)

# Enkel domain-mapping: du kan utvide denne etter behov
DOMAIN_DEFAULT = "META-systems"
DOMAIN_BY_SUBDIR = {
    # eksempel:
    # "AUTH-Layer": "AUTH-layer",
    # "Grid-Higgs": "Grid-Higgs",
}


# --------------------------- Helpers ---------------------------

def run(cmd, cwd=None):
    print(f"[builder] Running: {cmd} (cwd={cwd or os.getcwd()})")
    res = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(res.stdout)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def latex_build(tex_path):
    """Build PDF from a single .tex file (double pdflatex)."""
    tex_dir = os.path.dirname(tex_path)
    tex_file = os.path.basename(tex_path)
    base = os.path.splitext(tex_file)[0]

    print(f"[builder] Building {tex_path}")
    # kjør pdflatex to ganger for å få referanser / TOC riktig
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)

    pdf_path = os.path.join(tex_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF not found after build: {pdf_path}")
    print(f"[builder] PDF OK: {pdf_path}")
    return pdf_path


def extract_meta_from_tex(tex_path):
    """Leser ut title, author, abstract, keywords fra LaTeX."""
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    def match_cmd(name):
        m = re.search(rf"\\{name}\{{(.*?)\}}", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    title = match_cmd("title") or os.path.splitext(os.path.basename(tex_path))[0]
    author = match_cmd("author") or "Morten Magnusson"
    keywords_raw = match_cmd("keywords")
    if keywords_raw:
        keywords = [k.strip() for k in re.split(r"[;,]", keywords_raw) if k.strip()]
    else:
        keywords = []

    m_abs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
    abstract = m_abs.group(1).strip() if m_abs else ""

    return {
        "title": title,
        "author": author,
        "abstract": abstract,
        "keywords": keywords,
    }


def detect_domain(paper_dir, meta):
    """
    Enkel heuristikk for domain:
    - Sjekker siste del av pathen opp mot DOMAIN_BY_SUBDIR
    - Faller tilbake til DOMAIN_DEFAULT
    """
    last_dir = os.path.basename(paper_dir)
    for key, domain in DOMAIN_BY_SUBDIR.items():
        if key in last_dir or key in meta["title"]:
            return domain
    return DOMAIN_DEFAULT


def load_existing_doi(paper_dir, slug):
    """
    Prøver å hente DOI fra:
    1) metadata.json
    2) <slug>.jsonld
    Returnerer None hvis ingenting funnet.
    """
    # 1) metadata.json
    meta_path = os.path.join(paper_dir, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doi = data.get("doi")
            if doi:
                print(f"[builder] Found existing DOI in metadata.json: {doi}")
                return doi
        except Exception as e:
            print(f"[builder] Warning: could not read existing metadata.json: {e}")

    # 2) <slug>.jsonld
    jsonld_path = os.path.join(paper_dir, f"{slug}.jsonld")
    if os.path.exists(jsonld_path):
        try:
            with open(jsonld_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doi = data.get("identifier")
            # Noen ganger kan identifier være noe annet enn DOI, så vi er litt forsiktige:
            if doi and isinstance(doi, str) and ("10." in doi or doi.startswith("https://doi.org/")):
                print(f"[builder] Found existing DOI in jsonld: {doi}")
                return doi
        except Exception as e:
            print(f"[builder] Warning: could not read existing jsonld: {e}")

    return None


def build_pdf_url(slug):
    """
    Lager full raw GitHub-URL til PDF-en.
    """
    relative = f"docs/papers/efc/{slug}/{slug}.pdf"
    # Sørger for at det ikke blir doble slasher
    return f"{GITHUB_REPO_RAW_BASE.rstrip('/')}/{relative}"


# ----------------------- Writers -----------------------

def write_readme(paper_dir, slug, meta, domain, doi):
    title = meta["title"]
    abstract = meta["abstract"]
    keywords = meta["keywords"]
    year = date.today().year

    one_line = abstract.split("\n")[0] if abstract else (
        "This paper is part of the Energy-Flow Cosmology (EFC) series."
    )

    kw_str = ", ".join(keywords) if keywords else "Energy-Flow Cosmology, entropy, thermodynamics, cosmology"

    doi_line = f"DOI: {doi}" if doi else "DOI: _pending_"

    readme = f"""# {title}

This directory contains the paper **“{title}”**, part of the Energy-Flow Cosmology (EFC) series.

{one_line}

---

## Context in the EFC framework

- **Framework:** Energy-Flow Cosmology (EFC)  
- **Domain:** {domain}  
- **Role:** Links entropic structure, information flow and observable cosmological behaviour.  
- **{doi_line}**

---

## Abstract

{abstract or "_No abstract extracted from the LaTeX source yet._"}

---

## Keywords

{kw_str}

---

## File overview

- `{slug}.tex` – LaTeX source  
- `{slug}.pdf` – compiled paper  
- `{slug}.jsonld` – Schema.org / JSON-LD description of the work  
- `metadata.json` – internal EFC metadata for indexing and automation  
- `index.json` – entry used by the global EFC semantic index  
- `citations.bib` – bibliography used in the LaTeX source  

---

## Citation

If you reference this work:

> Magnusson, M. ({year}). *{title}.*  
> Energy-Flow Cosmology (EFC) Series.  
> {doi_line}  
> Available via GitHub: `docs/papers/efc/{slug}/{slug}.pdf`
"""
    with open(os.path.join(paper_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)


def write_metadata(paper_dir, slug, meta, domain, doi):
    today = str(date.today())
    description = (meta["abstract"] or "")[:500]

    data = {
        "id": slug,
        "slug": slug,
        "title": meta["title"],
        "description": description,
        "domain": domain,
        "keywords": meta["keywords"],
        "version": "1.0.0",
        "authors": [
            {
                "name": "Morten Magnusson",
                "orcid": "https://orcid.org/0009-0002-4860-5095",
            }
        ],
        "files": {
            "pdf": f"{slug}.pdf",
            "tex": f"{slug}.tex",
            "readme": "README.md",
            "jsonld": f"{slug}.jsonld",
        },
        "created": today,
        "updated": today,
    }

    if doi:
        data["doi"] = doi

    with open(os.path.join(paper_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_index(paper_dir, slug, meta, domain, doi):
    today = str(date.today())
    summary = (meta["abstract"] or "")[:300]

    index = {
        "id": slug,
        "slug": slug,
        "title": meta["title"],
        "path": f"docs/papers/efc/{slug}",
        "pdf": f"{slug}.pdf",
        "tex": f"{slug}.tex",
        "readme": "README.md",
        "layer": "docs",
        "domain": domain,
        "type": "paper",
        "version": "1.0.0",
        "keywords": meta["keywords"],
        "summary": summary,
        "created": today,
        "updated": today,
    }

    if doi:
        index["doi"] = doi

    with open(os.path.join(paper_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def write_jsonld(paper_dir, slug, meta, domain, doi):
    pdf_url = build_pdf_url(slug)

    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "identifier": doi or slug,
        "name": meta["title"],
        "description": meta["abstract"],
        "version": "1.0.0",
        "author": [
            {
                "@type": "Person",
                "name": "Morten Magnusson",
                "identifier": "https://orcid.org/0009-0002-4860-5095",
            }
        ],
        "keywords": meta["keywords"],
        "url": pdf_url,
        "isPartOf": {
            "@type": "CreativeWorkSeries",
            "name": "Energy-Flow Cosmology (EFC) Papers",
        },
        "about": {
            "@type": "Thing",
            "name": domain,
        },
    }

    with open(os.path.join(paper_dir, f"{slug}.jsonld"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_citations(paper_dir):
    bib_path = os.path.join(paper_dir, "citations.bib")
    if not os.path.exists(bib_path):
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write("% Bibliography for this EFC paper\n")
        print(f"[builder] Created empty citations.bib in {paper_dir}")


# ----------------------- Main flow -----------------------

def process_tex_file(tex_path):
    tex_path = os.path.abspath(tex_path)
    paper_dir = os.path.dirname(tex_path)
    slug = os.path.splitext(os.path.basename(tex_path))[0]

    print(f"[builder] Processing {tex_path}")

    # 1) Build PDF
    latex_build(tex_path)

    # 2) Extract meta from tex
    meta = extract_meta_from_tex(tex_path)

    # 3) Finn domain
    domain = detect_domain(paper_dir, meta)

    # 4) Hent eksisterende DOI hvis finnes
    doi = load_existing_doi(paper_dir, slug)

    # 5) Skriv companion-filer
    write_readme(paper_dir, slug, meta, domain, doi)
    write_metadata(paper_dir, slug, meta, domain, doi)
    write_index(paper_dir, slug, meta, domain, doi)
    write_jsonld(paper_dir, slug, meta, domain, doi)
    ensure_citations(paper_dir)

    print(f"[builder] Done: {slug} (domain={domain}, doi={doi or 'none'})")


def main():
    print(f"[builder] Scanning {DOCS_ROOT}")
    for root, dirs, files in os.walk(DOCS_ROOT):
        tex_files = [f for f in files if f.endswith(".tex")]
        if not tex_files:
            continue

        for tex in tex_files:
            tex_path = os.path.join(root, tex)
            process_tex_file(tex_path)


if __name__ == "__main__":
    main()
