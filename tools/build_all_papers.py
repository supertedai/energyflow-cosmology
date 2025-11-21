#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFC PAPER BUILDER v3.0
======================

Komplett pipeline:

- Bygg PDF (dobbel pdflatex)
- Ekstraher tittel/abstract/keywords
- Robust LaTeX-stripper
- Hent DOI:
    1. metadata.json
    2. jsonld
    3. Figshare API
- Injiser DOI inn i PDF-metadata (LaTeX preamble)
- Oppdater:
    README.md
    metadata.json
    index.json
    <slug>.jsonld
    citations.bib

Idempotent. Trygg å kjøre hver gang.
"""

import os
import re
import json
import subprocess
import requests
from datetime import date


# --------------------------------------------------------------
# Konfig
# --------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(__file__))
DOCS_ROOT = os.path.join(ROOT, "docs", "papers", "efc")

GITHUB_REPO_RAW_BASE = (
    "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main"
)

DOMAIN_DEFAULT = "META-systems"
DOMAIN_BY_SUBDIR = {}

FIGSHARE_API = "https://api.figshare.com/v2"


# --------------------------------------------------------------
# Helper-funksjoner
# --------------------------------------------------------------

def run(cmd, cwd=None):
    res = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(res.stdout)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def latex_build(tex_path):
    tex_dir = os.path.dirname(tex_path)
    tex_file = os.path.basename(tex_path)

    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)
    run(f"pdflatex -interaction=nonstopmode {tex_file}", cwd=tex_dir)

    pdf_path = tex_path.replace(".tex", ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF not produced: {pdf_path}")

    return pdf_path


# --------------------------------------------------------------
# LaTeX-stripper
# --------------------------------------------------------------

def strip_latex(text):
    if not text:
        return text

    # enkel styling
    text = re.sub(r"\\textbf\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\emph\{(.*?)\}", r"\1", text)
    text = re.sub(r"\\textit\{(.*?)\}", r"\1", text)

    # generelle kommandoer
    text = re.sub(r"\\[A-Za-z]+\{(.*?)\}", r"\1", text)

    # fjern \
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# --------------------------------------------------------------
# Ekstraher meta
# --------------------------------------------------------------

def extract_meta(tex_path):
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    def match(cmd):
        m = re.search(rf"\\{cmd}\{{(.*?)\}}", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    title = strip_latex(match("title"))
    if not title:
        title = os.path.splitext(os.path.basename(tex_path))[0]

    author = match("author") or "Morten Magnusson"

    kw_raw = match("keywords")
    keywords = []
    if kw_raw:
        for k in re.split(r"[;,]", kw_raw):
            if k.strip():
                keywords.append(strip_latex(k.strip()))

    m_abs = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL
    )
    abstract = strip_latex(m_abs.group(1)) if m_abs else ""

    return {
        "title": title,
        "author": author,
        "keywords": keywords,
        "abstract": abstract
    }


# --------------------------------------------------------------
# DOI-henting
# --------------------------------------------------------------

def load_existing_doi(dir, slug):
    # metadata.json
    m = os.path.join(dir, "metadata.json")
    if os.path.exists(m):
        try:
            with open(m, "r", encoding="utf-8") as f:
                d = json.load(f)
            if "doi" in d:
                return d["doi"]
        except:
            pass

    # jsonld
    j = os.path.join(dir, f"{slug}.jsonld")
    if os.path.exists(j):
        try:
            with open(j, "r", encoding="utf-8") as f:
                d = json.load(f)
            doi = d.get("identifier")
            if doi and ("10." in doi or doi.startswith("https://doi.org/")):
                return doi
        except:
            pass

    return None


def fetch_doi_from_figshare(title):
    try:
        r = requests.get(
            f"{FIGSHARE_API}/articles/search",
            params={"search_for": title},
            timeout=6
        )
        r.raise_for_status()

        for item in r.json():
            if item.get("title", "").strip().lower() == title.lower().strip():
                if item.get("doi"):
                    return item["doi"]

    except Exception as e:
        print("[builder] Figshare DOI lookup failed:", e)

    return None


# --------------------------------------------------------------
# DOI-injeksjon i LaTeX → PDF metadata
# --------------------------------------------------------------

def inject_doi_into_tex(tex_path, doi):
    if not doi:
        return

    with open(tex_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    injected = False

    for line in lines:
        # injiser etter \documentclass
        new_lines.append(line)
        if not injected and line.strip().startswith("\\documentclass"):
            new_lines.append(f"\\newcommand{{\\paperdoi}}{{{doi}}}\n")
            new_lines.append("\\usepackage{hyperref}\n")
            new_lines.append(
                "\\hypersetup{pdfinfo={DOI={\\paperdoi}}}\n"
            )
            injected = True

    with open(tex_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


# --------------------------------------------------------------
# Domain
# --------------------------------------------------------------

def detect_domain(dir, meta):
    last = os.path.basename(dir)
    for key, domain in DOMAIN_BY_SUBDIR.items():
        if key in last or key in meta["title"]:
            return domain
    return DOMAIN_DEFAULT


def pdf_url(slug):
    return f"{GITHUB_REPO_RAW_BASE}/docs/papers/efc/{slug}/{slug}.pdf"


# --------------------------------------------------------------
# File writers
# --------------------------------------------------------------

def write_readme(dir, slug, meta, domain, doi):
    year = date.today().year
    doi_line = f"DOI: {doi}" if doi else "DOI: pending"

    kw = ", ".join(meta["keywords"]) if meta["keywords"] else "Energy-Flow Cosmology"

    out = f"""# {meta["title"]}

This directory contains the paper **“{meta["title"]}”**, part of the EFC series.

{meta["abstract"].split("\n")[0]}

---

## Context in the EFC framework

- Framework: Energy-Flow Cosmology (EFC)
- Domain: {domain}
- Role: Links entropic structure, information flow and observable cosmological behaviour.
- {doi_line}

---

## Abstract

{meta["abstract"]}

---

## Keywords
{kw}

---

## Files
- {slug}.tex
- {slug}.pdf
- {slug}.jsonld
- metadata.json
- index.json
- citations.bib

---

## Citation

Magnusson, M. ({year}). *{meta["title"]}*.  
{doi_line}  
GitHub: docs/papers/efc/{slug}/{slug}.pdf
"""
    with open(os.path.join(dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(out)


def write_metadata(dir, slug, meta, domain, doi):
    now = str(date.today())

    d = {
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
        d["doi"] = doi

    with open(os.path.join(dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def write_index(dir, slug, meta, domain, doi):
    now = str(date.today())
    d = {
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
        d["doi"] = doi

    with open(os.path.join(dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def write_jsonld(dir, slug, meta, domain, doi):
    d = {
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
        "url": pdf_url(slug),
        "isPartOf": {
            "@type": "CreativeWorkSeries",
            "name": "Energy-Flow Cosmology (EFC) Papers"
        },
        "about": {"@type": "Thing", "name": domain}
    }

    with open(os.path.join(dir, f"{slug}.jsonld"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def ensure_citations(dir):
    p = os.path.join(dir, "citations.bib")
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("% bibliography\n")


# --------------------------------------------------------------
# Hovedprosess
# --------------------------------------------------------------

def process_file(tex_path):
    tex_path = os.path.abspath(tex_path)
    dir = os.path.dirname(tex_path)
    slug = os.path.splitext(os.path.basename(tex_path))[0]

    print(f"\n[builder] Processing: {slug}\n")

    # 1. Ekstraher metadata (før injeksjon)
    meta = extract_meta(tex_path)
    domain = detect_domain(dir, meta)

    # 2. DOI fra lokale filer
    doi = load_existing_doi(dir, slug)

    # 3. DOI fra Figshare hvis nødvendig
    if not doi:
        doi = fetch_doi_from_figshare(meta["title"])

    # 4. Injiser DOI i .tex → for å få DOI inn i PDF metadata
    inject_doi_into_tex(tex_path, doi)

    # 5. Bygg PDF
    latex_build(tex_path)

    # 6. Skriv metadatafiler
    write_readme(dir, slug, meta, domain, doi)
    write_metadata(dir, slug, meta, domain, doi)
    write_index(dir, slug, meta, domain, doi)
    write_jsonld(dir, slug, meta, domain, doi)
    ensure_citations(dir)

    print(f"[builder] DONE — {slug} (DOI={doi or 'pending'})")


def main():
    print(f"[builder] Scanning {DOCS_ROOT}")
    for root, dirs, files in os.walk(DOCS_ROOT):
        for f in files:
            if f.endswith(".tex"):
                process_file(os.path.join(root, f))


if __name__ == "__main__":
    main()
