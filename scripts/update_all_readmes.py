#!/usr/bin/env python3
"""
update_all_readmes.py — v2 (Paper-Aware Version)

Generates README.md for every folder in the repository, with special handling for
EFC papers in docs/papers/efc/<paper-name>.

Features:
- Full scientific README for papers (Title, DOI, Abstract, Keywords, Files)
- Reads metadata automatically from JSON-LD
- Links PDF + JSON-LD
- Protects root README.md
- Idempotent and safe for GitHub Actions + local runs
"""

import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_README = ROOT / "README.md"


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------

def load_jsonld(path: Path):
    """Safely load JSON-LD metadata."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_paper_folder(folder: Path):
    """Detect if folder is a paper folder."""
    return (
        "docs" in folder.parts
        and "papers" in folder.parts
        and "efc" in folder.parts
        and folder.is_dir()
        and any(f.suffix == ".jsonld" for f in folder.iterdir())
    )


# -------------------------------------------------------------
# Paper README generator
# -------------------------------------------------------------

def generate_paper_readme(folder: Path):
    """Create a scientific README.md for a paper folder."""
    jsonld_files = [f for f in folder.iterdir() if f.suffix == ".jsonld"]
    pdf_files = [f for f in folder.iterdir() if f.suffix == ".pdf"]

    if not jsonld_files:
        return None

    meta = load_jsonld(jsonld_files[0]) or {}

    title = meta.get("name", folder.name)
    doi = meta.get("identifier", "N/A")
    abstract = meta.get("description", "No abstract available.")
    keywords = meta.get("keywords", [])

    text = f"# {title}\n\n"
    text += f"**Scientific Publication — Energy-Flow Cosmology (EFC)**\n\n"

    text += f"**DOI:** {doi}\n\n"
    text += f"## Abstract\n{abstract}\n\n"

    if keywords:
        text += "## Keywords\n"
        for kw in keywords:
            text += f"- {kw}\n"
        text += "\n"

    text += "## Files\n"
    for pdf in pdf_files:
        text += f"- 📄 **PDF:** `{pdf.name}`\n"
    for js in jsonld_files:
        text += f"- 🧩 **JSON-LD:** `{js.name}`\n"

    return text


# -------------------------------------------------------------
# Generic folder README
# -------------------------------------------------------------

def folder_category(path: Path):
    """Returns semantic category based on folder name."""
    name = path.name.lower()

    if name in ["meta", "cognition", "symbiosis", "reflection", "meta-process"]:
        return "Meta–Cognition Layer — reflective process and symbiosis architecture."
    if name == "schema":
        return "Schema Layer — JSON-LD, ontology, semantic graph."
    if name == "api":
        return "API Layer — machine-readable endpoints for EFC concepts."
    if name == "scripts":
        return "Automation scripts."
    if name == "docs":
        return "Documentation — rendered content."
    if name == "papers":
        return "Scientific publications and preprints."
    if name == "efc":
        return "EFC papers collection."

    return "Repository folder."


def scan_directory(path: Path):
    dirs, files = [], []
    for p in sorted(path.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            dirs.append(p)
        elif p.is_file() and p.name != "README.md":
            files.append(p)
    return dirs, files


def generate_generic_readme(folder: Path):
    """Generic fallback README."""
    dirs, files = scan_directory(folder)
    title = folder.name

    text = f"# {title}\n\n"
    text += f"**{folder_category(folder)}**\n\n"
    text += "This README is auto-generated.\n\n"

    if dirs:
        text += "## 📁 Subfolders\n"
        for d in dirs:
            text += f"- `{d.name}/`\n"
        text += "\n"

    if files:
        text += "## 📄 Files\n"
        for f in files:
            text += f"- `{f.name}`\n"
        text += "\n"

    text += "_Automatically maintained._\n"
    return text


# -------------------------------------------------------------
# Main writer
# -------------------------------------------------------------

def write_readme(folder: Path):
    """Write README.md for a folder, special-casing paper folders."""
    readme_path = folder / "README.md"

    # Protect root README
    if folder == ROOT:
        print(f"⏭️ Skipping root README (protected).")
        return

    # Paper README
    if is_paper_folder(folder):
        content = generate_paper_readme(folder)
        if content:
            readme_path.write_text(content)
            print(f"✓ Paper README updated: {readme_path}")
            return

    # Generic README
    content = generate_generic_readme(folder)
    readme_path.write_text(content)
    print(f"✓ Generic README updated: {readme_path}")


# -------------------------------------------------------------
# Main routine
# -------------------------------------------------------------

def update_all_readmes():
    print("\n========= UPDATE ALL READMEs — PAPER-AWARE =========\n")

    for current, dirs, files in os.walk(ROOT):
        folder = Path(current)

        if any(skip in folder.parts for skip in [".git", ".github"]):
            continue

        write_readme(folder)

    print("\nDone.\n")


if __name__ == "__main__":
    update_all_readmes()
