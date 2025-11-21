#!/usr/bin/env python3
import os
import re
import json
import subprocess
from datetime import date
from slugify import slugify

ROOT = os.path.dirname(os.path.dirname(__file__))
DOCS_ROOT = os.path.join(ROOT, "docs", "papers", "efc")


def run(cmd, cwd=None):
    print(f"[builder] Running: {cmd} (cwd={cwd or os.getcwd()})")
    res = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
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


# ------------------------------------------------------
# LATEX CLEANER — ENDGILTIG, DEKNING 100%
# ------------------------------------------------------

def clean_latex(text: str) -> str:
    if not text:
        return ""

    # Fjern LaTeX bold med og uten {}  
    text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textbf\s+([A-Za-z0-9()_\-]+)', r'\1', text)

    # Fjern LaTeX italic
    text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\emph\s+([A-Za-z0-9()_\-]+)', r'\1', text)

    text = re.sub(r'\\textit\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\textit\s+([A-Za-z0-9()_\-]+)', r'\1', text)

    # ------------------------------------------------------
    # 100% FIX: Fjern ren tekst som starter med "textbf"
    # ------------------------------------------------------
    text = re.sub(r'\btextbf\s*', '', text)

    # Generisk \command{...}
    text = re.sub(r'\\[A-Za-z]+\{([^}]*)\}', r'\1', text)

    # Math $...$
    text = re.sub(r'\$([^$]+)\$', r'\1', text)

    # Indeksfix
    text = text.replace("s_0", "s₀")
    text = text.replace("s_1", "s₁")
    text = text.replace("S_0", "S₀")
    text = text.replace("S_1", "S₁")
    text = text.replace("\\_", "_")

    # Fjern backslash som står igjen
    text = re.sub(r'\\+', ' ', text)

    # Fjern braces
    text = text.replace("{", "").replace("}", "")

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# ------------------------------------------------------
# METADATA FRA TEX
# ------------------------------------------------------

def extract_meta_from_tex(tex_path):
    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    def match_cmd(name):
        m = re.search(rf"\\{name}\{{(.*?)\}}", content, re.DOTALL)
        return m.group(1).strip() if m else ""

    raw_title = match_cmd("title") or os.path.splitext(os.path.basename(tex_path))[0]
    raw_author = match_cmd("author") or "Morten Magnusson"
    keywords_raw = match_cmd("keywords")

    if keywords_raw:
        kws = [k.strip() for k in re.split(r"[;,]", keywords_raw) if k.strip()]
        keywords = [clean_latex(k) for k in kws if clean_latex(k)]
    else:
        keywords = []

    m_abs = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", content, re.DOTALL)
    raw_abstract = m_abs.group(1).strip() if m_abs else ""

    title = clean_latex(raw_title)
    author = clean_latex(raw_author)
    abstract = clean_latex(raw_abstract)

    if not keywords:
        keywords = ["Energy-Flow Cosmology", "entropy", "energy flow", "thermodynamics", "cosmology"]

    return {
        "title": title,
        "author": author,
        "abstract": abstract,
        "keywords": keywords,
    }


# ------------------------------------------------------
# WRITE FILES
# ------------------------------------------------------

def write_readme(paper_dir, slug, meta):
    title = meta["title"]
    abstract = meta["abstract"]
    keywords = meta["keywords"]
    domain = "META-systems"

    one_line = abstract or "This paper is part of the Energy-Flow Cosmology (EFC) series."
    kw_str = ", ".join(keywords)

    readme = f"""# {title}

This directory contains the paper **“{title}”**, part of the Energy-Flow Cosmology (EFC) series.

{one_line}

---

## Context in the EFC framework

- **Framework:** Energy-Flow Cosmology (EFC)  
- **Domain:** {domain}  
- **Role:** Links entropic structure, information flow and observable cosmological behaviour.  

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
- `{slug}.jsonld` – Schema.org / JSON-LD description  
- `metadata.json` – internal metadata  
- `index.json` – global index entry  
- `citations.bib` – bibliography  

---

## Citation

If you reference this work:

> Magnusson, M. ({date.today().year}). *{title}.*  
> Energy-Flow Cosmology (EFC) Series.  
> Available via GitHub: `docs/papers/efc/{slug}/{slug}.pdf`
"""

    with open(os.path.join(paper_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)


def write_metadata(paper_dir, slug, meta):
    today = str(date.today())
    data = {
        "id": slug,
        "slug": slug,
        "title": meta["title"],
        "description": meta["abstract"][:500],
        "domain": "META-systems",
        "keywords": meta["keywords"],
        "version": "1.0.0",
        "authors": [{"name": "Morten Magnusson", "orcid": "https://orcid.org/0009-0002-4860-5095"}],
        "files": {
            "pdf": f"{slug}.pdf",
            "tex": f"{slug}.tex",
            "readme": "README.md",
            "jsonld": f"{slug}.jsonld"
        },
        "created": today,
        "updated": today
    }
    with open(os.path.join(paper_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_index(paper_dir, slug, meta):
    today = str(date.today())
    index = {
        "id": slug,
        "slug": slug,
        "title": meta["title"],
        "path": f"docs/papers/efc/{slug}",
        "pdf": f"{slug}.pdf",
        "tex": f"{slug}.tex",
        "readme": "README.md",
        "layer": "docs",
        "domain": "META-systems",
        "type": "paper",
        "version": "1.0.0",
        "keywords": meta["keywords"],
        "summary": meta["abstract"][:300],
        "created": today,
        "updated": today
    }
    with open(os.path.join(paper_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def write_jsonld(paper_dir, slug, meta):
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "identifier": slug,
        "name": meta["title"],
        "description": meta["abstract"],
        "version": "1.0.0",
        "author": [
            {
                "@type": "Person",
                "name": "Morten Magnusson",
                "identifier": "https://orcid.org/0009-0002-4860-5095"
            }
        ],
        "keywords": meta["keywords"],
        "url": f"docs/papers/efc/{slug}/{slug}.pdf",
        "isPartOf": {"@type": "CreativeWorkSeries", "name": "Energy-Flow Cosmology (EFC) Papers"}
    }

    with open(os.path.join(paper_dir, f"{slug}.jsonld"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_citations(paper_dir):
    bib_path = os.path.join(paper_dir, "citations.bib")
    if not os.path.exists(bib_path):
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write("% Bibliography for this EFC paper\n")


def main():
    print(f"[builder] Scanning {DOCS_ROOT}")
    for root, dirs, files in os.walk(DOCS_ROOT):
        tex_files = [f for f in files if f.endswith(".tex")]
        if not tex_files:
            continue

        for tex in tex_files:
            tex_path = os.path.join(root, tex)
            slug = os.path.splitext(tex)[0]

            latex_build(tex_path)
            meta = extract_meta_from_tex(tex_path)

            write_readme(root, slug, meta)
            write_metadata(root, slug, meta)
            write_index(root, slug, meta)
            write_jsonld(root, slug, meta)
            ensure_citations(root)

            print(f"[builder] Done: {slug}")


if __name__ == "__main__":
    main()
