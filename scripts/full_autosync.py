#!/usr/bin/env python3
"""
update_all_readmes.py

EFC — Universal README Generator (English Version)
--------------------------------------------------

This script:

1. Updates README.md in every directory.
2. Creates README.md where missing.
3. Generates an intelligent abstract for each folder based on:
   - folder purpose inferred from name
   - file types inside
   - first lines of text files (if any)
4. Ensures consistent structure across the entire repository.

Safe for GitHub Actions and manual execution.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# =========================================================
# ABSTRACT GENERATOR
# =========================================================

def infer_abstract(folder: Path, dirs, files):
    """Generate a short abstract describing what the folder contains."""

    name = folder.name.lower()
    abstract = ""

    # 1) Semantic interpretation based on folder name
    if name in ["api", "v1"]:
        abstract = "This folder contains machine-readable API definitions for the Energy-Flow Cosmology semantic layer."
    elif name == "docs":
        abstract = "This folder contains generated documentation, repo maps, visual outputs, and supporting reference files."
    elif name == "meta":
        abstract = "This folder contains meta-level documents, conceptual structures, epistemology, and research reflections."
    elif name == "schema":
        abstract = "This folder contains schema definitions, JSON-LD mappings, ontology files, and structural metadata."
    elif name == "scripts":
        abstract = "This folder contains automation scripts, build logic, update routines, and self-healing tools."
    elif name == "src":
        abstract = "This folder contains source code, computational models, simulations, and core EFC components."
    elif name == "theory":
        abstract = "This folder contains theoretical notes, derivations, mathematical material, and conceptual frameworks."
    elif name == "notebooks":
        abstract = "This folder contains Jupyter notebooks, computational experiments, and numerical exploration tools."
    elif name == "methodology":
        abstract = "This folder documents the scientific methodology, reflective framework, meta-procedures, and research process."
    else:
        abstract = f"This folder contains files and substructures related to '{folder.name}', automatically analyzed."

    # 2) Add file-based hints
    if files:
        exts = sorted(set([f.suffix.lower() for f in files]))
        if exts:
            extlist = ", ".join(exts)
            abstract += f" It includes the following file types: {extlist}."

    # 3) Try to extract first line of text files for additional semantic cues
    for f in files:
        if f.suffix.lower() in [".md", ".txt", ".json", ".py"]:
            try:
                first_line = f.read_text().strip().split("\n")[0]
                if first_line:
                    abstract += f" A representative file begins with: \"{first_line[:120]}\"."
                break
            except:
                pass

    return abstract


# =========================================================
# README GENERATION
# =========================================================

def scan_directory(path: Path):
    dirs = []
    files = []
    for p in sorted(path.iterdir()):
        if p.is_dir() and not p.name.startswith(".") and p.name not in ["__pycache__", ".git", ".github"]:
            dirs.append(p)
        elif p.is_file() and p.name != "README.md":
            files.append(p)
    return dirs, files


def generate_readme(folder: Path):
    dirs, files = scan_directory(folder)
    title = folder.name if folder != ROOT else "Energy-Flow Cosmology — Repository"

    abstract = infer_abstract(folder, dirs, files)

    text = f"# {title}\n\n"
    text += f"**Abstract:** {abstract}\n\n"

    if dirs:
        text += "## 📁 Subdirectories\n"
        for d in dirs:
            text += f"- `{d.name}/`\n"
        text += "\n"

    if files:
        text += "## 📄 Files\n"
        for f in files:
            text += f"- `{f.name}`\n"
        text += "\n"

    text += "*This README is automatically generated.*\n"
    return text


def write_readme(folder: Path):
    readme_path = folder / "README.md"
    content = generate_readme(folder)
    readme_path.write_text(content)
    print(f"✓ Updated README: {readme_path}")


# =========================================================
# MAIN
# =========================================================

def update_all_readmes():
    print("\n========= UPDATE ALL READMEs (ENGLISH VERSION) =========\n")

    # Root README
    write_readme(ROOT)

    # Recursive
    for current, dirs, files in os.walk(ROOT):
        current_path = Path(current)

        if any(skip in current_path.parts for skip in [".git", ".github"]):
            continue

        write_readme(current_path)

    print("\nDone: All READMEs updated.\n")


if __name__ == "__main__":
    update_all_readmes()
