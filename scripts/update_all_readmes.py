#!/usr/bin/env python3
"""
update_all_readmes.py

EFC — Orientation-Style README Generator
----------------------------------------

Generates README.md in every directory, using an orientation-guide style similar
to START-HERE:

- <Folder> — Orientation Guide
- 1. What this folder is
- 2. If you're new — start with these
- 3. Main tracks
- 4. Recommended reading / usage order
- 5. Why this folder exists
- 6. Next steps

All text is in English.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ========================= helpers =========================

def scan_directory(path: Path):
    dirs = []
    files = []
    for p in sorted(path.iterdir()):
        if p.is_dir() and not p.name.startswith(".") and p.name not in [".git", ".github", "__pycache__"]:
            dirs.append(p)
        elif p.is_file() and p.name != "README.md":
            files.append(p)
    return dirs, files


def infer_role(folder: Path) -> str:
    name = folder.name.lower()
    parts = [p.lower() for p in folder.parts]

    # coarse role mapping based on folder name / path
    if "theory" in parts:
        return "Theory Layer — formal definitions, derivations, and core cosmological structure."
    if "src" in parts:
        return "Source Code Layer — models, simulations, and core implementation of EFC."
    if "docs" in parts:
        return "Documentation Layer — rendered outputs, web-facing material, and human-readable summaries."
    if "api" in parts:
        return "Semantic API Layer — machine-readable concepts, terms, and metadata."
    if "meta" in parts:
        return "Meta / Cognition / Symbiosis Layer — reflective process, methodology, and cognitive structure."
    if "methodology" in parts:
        return "Methodology Layer — scientific process, epistemic scaffolding, and reflective framework."
    if "notebooks" in parts:
        return "Notebook Layer — exploratory computations, validation experiments, and interactive analysis."
    if "output" in parts or "data" in parts:
        return "Validation / Data Layer — empirical fits, figures, and datasets used to test the theory."
    if folder == ROOT:
        return "Top-level integration of theory, validation, meta, and semantic layers for Energy-Flow Cosmology."

    return f"This folder is part of the Energy-Flow Cosmology repository and groups related files under '{folder.name}'."


def choose_highlight_files(files, max_items=4):
    """Pick a small set of 'start here' files."""
    # prioritise .md / .pdf / .tex
    scored = []
    for f in files:
        score = 0
        n = f.name.lower()
        if n.endswith((".md", ".pdf", ".tex")):
            score += 3
        if "readme" in n:
            score += 4
        if "start" in n or "guide" in n:
            score += 3
        if "spec" in n or "formal" in n or "master" in n:
            score += 2
        scored.append((score, f))

    scored.sort(key=lambda x: (-x[0], x[1].name))
    return [f for score, f in scored[:max_items] if score > 0] or files[:max_items]


def choose_recommended_order(highlights):
    """For now, just reuse highlights as recommended order."""
    return highlights


def infer_next_steps(folder: Path):
    """Simple generic next-step text depending on layer."""
    parts = [p.lower() for p in folder.parts]
    if folder == ROOT:
        return [
            "Read the formal EFC specification under `theory/formal/`.",
            "Explore validation outputs under `output/` and `notebooks/`.",
            "Inspect meta and cognition layers under `meta/`.",
            "Follow links from `schema/` and `api/` if you need machine-readable views."
        ]
    if "theory" in parts:
        return [
            "Follow references from the main specification into submodules.",
            "Compare theoretical curves with validation outputs under `output/` or `notebooks/`."
        ]
    if "meta" in parts or "methodology" in parts:
        return [
            "Read the top-level meta or methodology README first.",
            "Cross-reference this layer with the formal theory and validation layers."
        ]
    if "docs" in parts:
        return [
            "Open the main rendered specification (HTML or PDF).",
            "Follow internal links to theory and API layers."
        ]
    if "api" in parts:
        return [
            "Inspect the JSON files to understand the semantic graph.",
            "Use these endpoints as a machine-readable entry point into EFC."
        ]
    return [
        "Explore the listed files and subdirectories.",
        "Follow links back to theory, validation, meta, or API layers as needed."
    ]


# ========================= core generation =========================

def generate_readme(folder: Path) -> str:
    dirs, files = scan_directory(folder)
    title = "Energy-Flow Cosmology — Orientation Guide" if folder == ROOT else f"{folder.name} — Orientation Guide"

    role = infer_role(folder)
    highlights = choose_highlight_files(files)
    recommended = choose_recommended_order(highlights)
    next_steps = infer_next_steps(folder)

    # --- build text ---
    out = []

    out.append(f"# {title}\n")
    out.append(f"This folder is part of the Energy-Flow Cosmology (EFC) repository.\n")
    out.append("This page gives you a quick orientation so you can understand what lives here and how to use it.\n")

    # 1. What this folder is
    out.append("\n## 1. What this folder is\n")
    out.append(f"{role}\n")

    if dirs or files:
        out.append("\nThis directory contains:\n")
        if dirs:
            out.append("- one or more subdirectories that further structure this layer\n")
        if files:
            out.append("- local files that implement, document, or validate this layer\n")

    # 2. If you're new — start with these
    out.append("\n## 2. If you’re new — start with these\n")
    if highlights:
        out.append("Read or inspect the following items first:\n\n")
        for i, f in enumerate(highlights, start=1):
            out.append(f"{i}. `{f.relative_to(folder)}`\n")
    else:
        out.append("There are no obvious entry files yet. Browse the file list below.\n")

    # 3. Main tracks (subdirectories)
    out.append("\n## 3. Main tracks inside this folder\n")
    if dirs:
        out.append("The main subdirectories are:\n\n")
        for d in dirs:
            out.append(f"- `{d.name}/`\n")
    else:
        out.append("This folder has no subdirectories; it is a leaf node.\n")

    # 4. Recommended reading / usage order
    out.append("\n## 4. Recommended reading / usage order\n")
    if recommended:
        out.append("A reasonable order is:\n\n")
        for i, f in enumerate(recommended, start=1):
            out.append(f"{i}. `{f.relative_to(folder)}`\n")
    else:
        out.append("There is no strict order here; inspect files as needed.\n")

    # 5. Why this folder exists
    out.append("\n## 5. Why this folder exists in the repository\n")
    if folder == ROOT:
        out.append(
            "The root of the repository ties together theory, validation, meta/cognition, and semantic layers into a "
            "coherent open science system for Energy-Flow Cosmology.\n"
        )
    else:
        out.append(
            "This folder groups a coherent piece of the EFC system (theory, validation, meta, API, or tooling) so that "
            "it can be understood, extended, and referenced as a unit.\n"
        )

    # 6. Next steps
    out.append("\n## 6. Next steps after this folder\n")
    for step in next_steps:
        out.append(f"- {step}\n")

    # inventory at the end
    out.append("\n---\n\n")
    out.append("## Inventory\n")

    if dirs:
        out.append("\n### Subdirectories\n")
        for d in dirs:
            out.append(f"- `{d.name}/`\n")

    if files:
        out.append("\n### Files\n")
        for f in files:
            out.append(f"- `{f.name}`\n")

    out.append("\n*This README is automatically generated by `update_all_readmes.py`.*\n")

    return "".join(out)


def write_readme(folder: Path):
    readme_path = folder / "README.md"
    content = generate_readme(folder)
    readme_path.write_text(content)
    print(f"✓ Updated README: {readme_path}")


def update_all_readmes():
    print("\n========= UPDATE ALL ORIENTATION READMEs =========\n")

    # root first
    write_readme(ROOT)

    # then recursively
    for current, dirs, files in os.walk(ROOT):
        current_path = Path(current)
        if any(skip in current_path.parts for skip in [".git", ".github", "__pycache__"]):
            continue
        write_readme(current_path)

    print("\nDone: All READMEs updated in orientation style.\n")


if __name__ == "__main__":
    update_all_readmes()
