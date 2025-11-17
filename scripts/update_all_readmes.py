#!/usr/bin/env python3
"""
update_all_readmes.py

EFC — Universal README Generator
--------------------------------
Dette scriptet gjør tre ting:

1. Oppdaterer ALLE README.md filer i repoet
2. Oppretter README.md i ALLE mapper som mangler
3. Sørger for at fremtidige mapper ALLTID får README automatisk

Kjører trygt i GitHub Actions og manuelt.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def scan_directory(path: Path):
    """Returnerer mapper og filer i gitt katalog."""
    dirs = []
    files = []
    for p in sorted(path.iterdir()):
        if p.is_dir() and not p.name.startswith(".") and p.name not in ["__pycache__", ".git", ".github"]:
            dirs.append(p)
        elif p.is_file() and not p.name.endswith("README.md"):
            files.append(p)
    return dirs, files


def generate_readme_for_folder(folder: Path):
    """Genererer README-innhold basert på faktisk struktur."""
    dirs, files = scan_directory(folder)

    title = folder.name if folder != ROOT else "Energy-Flow Cosmology Repository"

    text = f"# {title}\n\n"
    text += "Automatisk generert README via `update_all_readmes.py`.\n\n"

    if dirs:
        text += "## 📁 Undermapper\n"
        for d in dirs:
            text += f"- `{d.name}/`\n"
        text += "\n"

    if files:
        text += "## 📄 Filer\n"
        for f in files:
            text += f"- `{f.name}`\n"
        text += "\n"

    # Spesialhåndtering
    if folder.name == "api":
        text += "### 🔬 API-lag\nDenne mappen inneholder EFC API.\n\n"

    if folder.name.lower() == "docs":
        text += "### 📚 Dokumentasjon\nRepo-genererte filer, HTML o.l.\n\n"

    if folder.name.lower() == "methodology":
        text += "### 🧠 Methodology\nMetodologifiler brukt av EFC-systemet.\n\n"

    text += "*Denne README oppdateres automatisk.*\n"

    return text


def write_readme(folder: Path):
    """Oppretter eller oppdaterer README.md i gitt folder."""
    readme_path = folder / "README.md"
    content = generate_readme_for_folder(folder)
    readme_path.write_text(content)
    print(f"✓ Oppdatert README: {readme_path}")


# =========================================================
# MAIN
# =========================================================

def update_all_readmes():
    print("\n================= UPDATE ALL READMEs =================\n")

    # 1. Oppdater README i rot
    write_readme(ROOT)

    # 2. Gå rekursivt gjennom repoet
    for current, dirs, files in os.walk(ROOT):
        current_path = Path(current)

        # Skip .git, .github
        if any(skip in current_path.parts for skip in [".git", ".github"]):
            continue

        # Oppdater / opprett README i alle mapper
        write_readme(current_path)

    print("\nFullført: Alle README-filer opprettet og oppdatert.\n")


if __name__ == "__main__":
    update_all_readmes()
