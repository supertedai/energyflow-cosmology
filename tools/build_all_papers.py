#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC PAPER BUILDER v2.2
======================

Som v2, men med robust LaTeX-stripper i extract_meta_from_tex().
Ingen andre endringer i logikk, struktur eller metadata.
"""

import os
import re
import json
import subprocess
from datetime import date
from slugify import slugify
from pathlib import Path

# --------------------------- Konfig ---------------------------

ROOT = os.path.dirname(os.path.dirname(__file__))  # repo-root
DOCS_ROOT = os.path.join(ROOT, "docs", "papers", "efc")

GITHUB_REPO_RAW_BASE = os.environ.get(
    "EFC_GITHUB_RAW_BASE",
    "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main",
)

DOMAIN_DEFAULT = "META-systems"

DOMAIN_BY_SUBDIR = {
    # legg til ved behov
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
    tex_dir = os.path.dirname(tex_path)
    tex_file = os.path.basename(tex_path)
    base = os.path.splitext(tex_file)[0]

    print(f"[builder] Building {tex_path}")
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)

    pdf_path = os.path.join(tex_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF not found after build: {pdf_path}")
    print(f"[builder] PDF OK: {pdf_path}")
    return pdf_path


# --------------------------- LaTeX-stripper ---------------------------

def strip_latex(text: str) -> str:
    """Fjerner LaTeX-makroer som \textbf{...}, \emph{...}, \command{...} og backslashes."""

    if not text:
        return text

    # Fjern spesifikke stilkommandoer
    text = re.sub(r"\\textbf\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\emph\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\textit\{(.*?)\}", r"\1", text)

    # Generell regel for \kommando{...}
    text = re.sub(r"\\[A-Za-z]+\{(.*?)\}", r"\1", text)

    # Fjern enslige LaTeX backslashes
    text = text.replace("\\", "")

    # Fjern dobbelspacing
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --------------------------- Meta-extractor ---------------------------

def extract_meta_from_tex(tex_path):
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    def match_cmd(name):
        m = re.search(rf"\\{name}\{{(.*?)\}}", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    title = match_cmd("title") or os.path.splitext(os.path.basename(tex_path))[0]
    author = match_cmd("author") or "Morten Magnusson"

    keywords_raw = match_cmd("keywords")
    if keywords_raw:
        keywords = [strip_latex(k.strip()) for k in re.split(r"[;,]", keywords_raw) if k.strip()]
    else:
        keywords = []

    m_abs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
    abstract = m_abs.group(1).strip() if m_abs else ""

    # STRIP LATEX:
    title = strip_latex(title)
    abstract = strip_latex(abstract)

    return {
        "title": title,
        "author": author,
        "abstract": abstract,
        "keywords": keywords,
    }


def detect_domain(paper_dir, meta):
    last = os.path.basename(paper_dir)
    for key, domain in DOMAIN_BY_SUBDIR.items():
        if key in last or key in meta["title"]:
            return domain
    return DOMAIN_DEFAULT


def load_existing_doi(paper_dir, slug):
    meta_path = os.path.join(paper_dir, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doi = data.get("doi")
            if doi:
                print(f"[builder] Found DOI in metadata.json: {doi}")
                return doi
        except Exception:
            pass

    jsonld_path = os.path.join(paper_dir, f"{slug}.jsonld")
    if os.path.exists(jsonld_path):
        try:
            with open(jsonld_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            doi = data.get("identifier")
            if doi and ("10." in doi or doi.startswith("https://doi.org")):
                print(f"[builder] Found DOI in jsonld: {doi}")
                return doi
        except Exception:
            pass

    return None


def build_pdf_url(slug):
    rel = f"docs/papers/efc/{slug}/{slug}.pdf"
    return f"{GITHUB_REPO_RAW_BASE.rstrip('/')}/{rel}"


# --------------------------- Writers ---------------------------

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

    out = f"""# {title}

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

- `{slug}.tex`
- `{slug}.pdf`
- `{slug}.jsonld`
- `metadata.json`
- `index.json`
- `citations.bib`

---

## Citation

> Magnusson, M. ({year}). *{title}.*  
> Energy-Flow Cosmology (EFC) Series.  
> {doi_line}  
> GitHub: `docs/papers/efc/{slug}/{slug}.pdf`

"""
    with open(os.path.join(paper_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(out)


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

    data = {
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
        data["doi"] = doi

    with open(os.path.join(paper_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


# --------------------------- Main logic ---------------------------

def process_tex_file(tex_path):
    tex_path = os.path.abspath(tex_path)
    paper_dir = os.path.dirname(tex_path)
    slug = os.path.splitext(os.path.basename(tex_path))[0]

    print(f"[builder] Processing {tex_path}")

    latex_build(tex_path)

    meta = extract_meta_from_tex(tex_path)
    domain = detect_domain(paper_dir, meta)
    doi = load_existing_doi(paper_dir, slug)

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
            process_tex_file(os.path.join(root, tex))


if __name__ == "__main__":
    main()
