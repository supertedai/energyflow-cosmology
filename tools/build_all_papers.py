#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC PAPER BUILDER v2.4
======================

For hver .tex:

- Bygger PDF
- Leser tittel/abstract/keywords
- Stripper LaTeX
- Henter DOI fra:
    1. metadata.json
    2. jsonld
    3. Figshare API (automatisk lookup via tittel)
- Oppdaterer:
    README.md
    metadata.json
    index.json
    <slug>.jsonld
    citations.bib

Filen er idempotent – trygg å kjøre mange ganger.
"""

import os
import re
import json
import subprocess
import requests
from datetime import date

ROOT = os.path.dirname(os.path.dirname(__file__))          # repo-root
DOCS_ROOT = os.path.join(ROOT, "docs", "papers", "efc")

GITHUB_REPO_RAW_BASE = os.environ.get(
    "EFC_GITHUB_RAW_BASE",
    "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main"
)

DOMAIN_DEFAULT = "META-systems"
DOMAIN_BY_SUBDIR = {}

FIGSHARE_API = "https://api.figshare.com/v2"


# ------------------------------------------------------------
# SYSTEM HELPERS
# ------------------------------------------------------------

def run(cmd, cwd=None):
    print(f"[builder] Running: {cmd} (cwd={cwd or os.getcwd()})")
    res = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(res.stdout)
    if res.returncode != 0:
        raise RuntimeError(f"[builder] Failed: {cmd}")


def latex_build(tex_path):
    tex_dir = os.path.dirname(tex_path)
    tex_file = os.path.basename(tex_path)
    base = os.path.splitext(tex_file)[0]

    print(f"[builder] Building PDF for {tex_file}")
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)

    pdf_path = os.path.join(tex_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"[builder] PDF missing: {pdf_path}")

    return pdf_path


# ------------------------------------------------------------
# LATEX STRIPPER
# ------------------------------------------------------------

def strip_latex(text):
    if not text:
        return text

    text = re.sub(r"\\textbf\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\emph\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\textit\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\{(.*?)\}", r"\1", text)
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ------------------------------------------------------------
# EXTRACT META FROM LATEX
# ------------------------------------------------------------

def extract_meta_from_tex(tex_path):
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    def match(cmd):
        m = re.search(rf"\\{cmd}\{{(.*?)\}}", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    title = match("title")
    author = match("author") or "Morten Magnusson"
    kw_raw = match("keywords")

    keywords = []
    if kw_raw:
        for k in re.split(r"[;,]", kw_raw):
            if k.strip():
                keywords.append(strip_latex(k.strip()))

    m_abs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
    abstract = m_abs.group(1).strip() if m_abs else ""

    # strip LaTeX
    title = strip_latex(title)
    abstract = strip_latex(abstract)

    return {
        "title": title or os.path.splitext(os.path.basename(tex_path))[0],
        "author": author,
        "abstract": abstract,
        "keywords": keywords
    }


# ------------------------------------------------------------
# DOI-LOADERS
# ------------------------------------------------------------

def load_existing_doi(paper_dir, slug):
    # metadata.json
    meta = os.path.join(paper_dir, "metadata.json")
    if os.path.exists(meta):
        try:
            with open(meta, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "doi" in data:
                print(f"[builder] DOI found in metadata.json: {data['doi']}")
                return data["doi"]
        except:
            pass

    # jsonld
    jsonld = os.path.join(paper_dir, f"{slug}.jsonld")
    if os.path.exists(jsonld):
        try:
            with open(jsonld, "r", encoding="utf-8") as f:
                data = json.load(f)
            doi = data.get("identifier")
            if doi and ("10." in doi or doi.startswith("https://doi.org")):
                print(f"[builder] DOI found in jsonld: {doi}")
                return doi
        except:
            pass

    return None


def fetch_doi_from_figshare(title):
    """Henter DOI fra Figshare ved tittelmatch."""
    try:
        params = {"search_for": title}
        r = requests.get(f"{FIGSHARE_API}/articles/search", params=params, timeout=5)
        r.raise_for_status()
        results = r.json()

        for item in results:
            if "title" in item and item["title"].strip().lower() == title.lower().strip():
                doi = item.get("doi")
                if doi:
                    print(f"[builder] DOI found on Figshare: {doi}")
                    return doi
    except Exception as e:
        print(f"[builder] Figshare lookup failed: {e}")

    return None


# ------------------------------------------------------------
# DOMAIN + PDF-URL
# ------------------------------------------------------------

def detect_domain(paper_dir, meta):
    last = os.path.basename(paper_dir)
    for key, domain in DOMAIN_BY_SUBDIR.items():
        if key in last or key in meta["title"]:
            return domain
    return DOMAIN_DEFAULT


def build_pdf_url(slug):
    rel = f"docs/papers/efc/{slug}/{slug}.pdf"
    return f"{GITHUB_REPO_RAW_BASE.rstrip('/')}/{rel}"


# ------------------------------------------------------------
# FILE WRITERS
# ------------------------------------------------------------

def write_readme(dir, slug, meta, domain, doi):
    year = date.today().year
    abstract = meta["abstract"] or "_No abstract found._"
    kw = ", ".join(meta["keywords"]) if meta["keywords"] else "Energy-Flow Cosmology, entropy"

    doi_line = f"DOI: {doi}" if doi else "DOI: pending"

    out = f"""# {meta["title"]}

This directory contains the paper **“{meta["title"]}”**, part of the EFC series.

{abstract.split("\n")[0]}

---

## Context in the EFC framework

- **Framework:** Energy-Flow Cosmology (EFC)
- **Domain:** {domain}
- **Role:** Links entropic structure, information flow and observable cosmological behaviour.
- **{doi_line}**

---

## Abstract

{abstract}

---

## Keywords
{kw}

---

## Files
- `{slug}.tex`
- `{slug}.pdf`
- `{slug}.jsonld`
- `metadata.json`
- `index.json`
- `citations.bib`

---

## Citation

> Magnusson, M. ({year}). *{meta["title"]}.*  
> {doi_line}  
> GitHub: docs/papers/efc/{slug}/{slug}.pdf

"""
    with open(os.path.join(dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(out)


def write_metadata(dir, slug, meta, domain, doi):
    now = str(date.today())
    data = {
        "id": slug,
        "slug": slug,
        "title": meta["title"],
        "description": meta["abstract"][:500],
        "domain": domain,
        "keywords": meta["keywords"],
        "version": "1.0.0",
        "authors": [{
            "name": "Morten Magnusson",
            "orcid": "https://orcid.org/0009-0002-4860-5095"
        }],
        "files": {
            "pdf": f"{slug}.pdf",
            "tex": f"{slug}.tex",
            "readme": "README.md",
            "jsonld": f"{slug}.jsonld"
        },
        "created": now,
        "updated": now
    }
    if doi:
        data["doi"] = doi

    with open(os.path.join(dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_index(dir, slug, meta, domain, doi):
    now = str(date.today())
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
        "summary": meta["abstract"][:300],
        "created": now,
        "updated": now
    }
    if doi:
        data["doi"] = doi

    with open(os.path.join(dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_jsonld(dir, slug, meta, domain, doi):
    pdf_url = build_pdf_url(slug)
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "identifier": doi or slug,
        "name": meta["title"],
        "description": meta["abstract"],
        "version": "1.0.0",
        "author": [{
            "@type": "Person",
            "name": "Morten Magnusson",
            "identifier": "https://orcid.org/0009-0002-4860-5095"
        }],
        "keywords": meta["keywords"],
        "url": pdf_url,
        "isPartOf": {
            "@type": "CreativeWorkSeries",
            "name": "Energy-Flow Cosmology (EFC) Papers"
        },
        "about": {
            "@type": "Thing",
            "name": domain
        }
    }
    with open(os.path.join(dir, f"{slug}.jsonld"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_citations(dir):
    bib = os.path.join(dir, "citations.bib")
    if not os.path.exists(bib):
        with open(bib, "w", encoding="utf-8") as f:
            f.write("% Bibliography for this EFC paper\n")


# ------------------------------------------------------------
# MAIN PROCESS
# ------------------------------------------------------------

def process_tex_file(tex_path):
    tex_path = os.path.abspath(tex_path)
    dir = os.path.dirname(tex_path)
    slug = os.path.splitext(os.path.basename(tex_path))[0]

    print(f"[builder] Processing {slug}")

    latex_build(tex_path)
    meta = extract_meta_from_tex(tex_path)
    domain = detect_domain(dir, meta)

    # DOI → metadata → jsonld → Figshare
    doi = load_existing_doi(dir, slug)
    if not doi:
        doi = fetch_doi_from_figshare(meta["title"])

    write_readme(dir, slug, meta, domain, doi)
    write_metadata(dir, slug, meta, domain, doi)
    write_index(dir, slug, meta, domain, doi)
    write_jsonld(dir, slug, meta, domain, doi)
    ensure_citations(dir)

    print(f"[builder] DONE {slug} (doi={doi or 'pending'})")


def main():
    print(f"[builder] Scanning {DOCS_ROOT}")
    for root, dirs, files in os.walk(DOCS_ROOT):
        for f in files:
            if f.endswith(".tex"):
                process_tex_file(os.path.join(root, f))


if __name__ == "__main__":
    main()
