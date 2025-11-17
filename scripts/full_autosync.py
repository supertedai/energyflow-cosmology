#!/usr/bin/env python3
"""
Full autosync for Energy-Flow Cosmology (EFC).

Kjører hele kjeden:
- Figshare → figshare/
- Schema → schema/
- Concepts + methodology → api/v1/
- Repo-map → repo_structure.txt / meta-index.json
- TeX builds → theory/formal + docs

Kjør lokalt eller via GitHub Actions:
    python scripts/full_autosync.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd=None):
    print(f"\n[full_autosync] Running: {' '.join(cmd)}  (cwd={cwd or ROOT})")
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else str(ROOT),
        check=False,
    )
    if result.returncode != 0:
        print(f"[full_autosync] ERROR: command failed with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    # 1) Figshare → figshare/*.json + meta.json
    try:
        run(["python", "scripts/fetch_figshare_auto.py"])
    except FileNotFoundError:
        print("[full_autosync] Skipping fetch_figshare_auto.py (not found)")

    # 2) Schema → schema/*.json (docs-index, methodology-index, site-graph, schema-map, etc.)
    schema_script = ROOT / "schema" / "update-schema.sh"
    if schema_script.exists():
        run(["bash", "schema/update-schema.sh"])
    else:
        print("[full_autosync] Skipping schema/update-schema.sh (not found)")

    # 3) Concepts / methodology / meta → api/v1/*
    #    (bruker eksisterende scripts, ingen nye formater)
    try:
        run(["python", "scripts/update_concepts.py"])
    except FileNotFoundError:
        print("[full_autosync] Skipping update_concepts.py (not found)")

    try:
        run(["python", "scripts/generate_methodology_api.py"])
    except FileNotFoundError:
        print("[full_autosync] Skipping generate_methodology_api.py (not found)")

    try:
        run(["python", "scripts/update_efc_api.py"])
    except FileNotFoundError:
        print("[full_autosync] Skipping update_efc_api.py (not found)")

    # 4) Repo-kart / meta-indeks
    try:
        run(["python", "scripts/generate_repo_map.py"])
    except FileNotFoundError:
        print("[full_autosync] Skipping generate_repo_map.py (not found)")

    # 5) TeX builds (formal spec + master docs)
    theory_formal = ROOT / "theory" / "formal" / "efc_formal_spec.tex"
    if theory_formal.exists():
        run(["latexmk", "-pdf", "efc_formal_spec.tex"], cwd=theory_formal.parent)
    else:
        print("[full_autosync] Skipping theory/formal build (efc_formal_spec.tex not found)")

    docs_master = ROOT / "docs" / "efc_master.tex"
    if docs_master.exists():
        run(["latexmk", "-pdf", "efc_master.tex"], cwd=docs_master.parent)
    else:
        print("[full_autosync] Skipping docs build (efc_master.tex not found)")

    # 6) (valgfritt) kjør validering – slå på hvis du vil
    RUN_VALIDATION = False
    if RUN_VALIDATION:
        try:
            run(["python", "scripts/validate_efc.py"])
        except FileNotFoundError:
            print("[full_autosync] Skipping validate_efc.py (not found)")

    print("\n[full_autosync] Done. All sync steps completed.")


if __name__ == "__main__":
    main()
