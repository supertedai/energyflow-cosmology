#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd=None, allow_fail=False):
    """Run a command with optional soft-failure."""
    print(f"\n[full_autosync] Running: {' '.join(cmd)}  (cwd={cwd or ROOT})")

    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else str(ROOT),
        check=False
    )

    if result.returncode != 0:
        print(f"[full_autosync] ERROR: command returned code {result.returncode}")

        if allow_fail:
            print("[full_autosync] allow_fail=True → continuing despite the error.")
            return result.returncode

        print("[full_autosync] Fatal error → stopping autosync.")
        sys.exit(result.returncode)

    return result.returncode


def main():
    print("\n============== EFC FULL AUTOSYNC ==============\n")
    print("[full_autosync] Project root:", ROOT)

    # ----------------------------------------------------
    # 1) FIGSHARE SYNC — SOFT FAILURE
    # ----------------------------------------------------
    print("\n[1] FIGSHARE METADATA SYNC")
    print("[full_autosync] This step may fail without a Figshare token in CI.")
    run(["python", "scripts/fetch_figshare_auto.py"], allow_fail=True)

    # ----------------------------------------------------
    # 2) UPDATE CONCEPTS / SCHEMA / SEMANTIC LAYER
    # ----------------------------------------------------
    print("\n[2] Updating concepts.json + semantic layers")
    run(["python", "scripts/update_concepts.py"])

    # ----------------------------------------------------
    # 3) GENERATE METHODOLOGY API
    # ----------------------------------------------------
    print("\n[3] Regenerating Methodology API")
    run(["python", "scripts/generate_methodology_api.py"])

    # ----------------------------------------------------
    # 4) UPDATE EFC API (api/v1)
    # ----------------------------------------------------
    print("\n[4] Regenerating API v1 (concepts + methodology + meta)")
    run(["python", "scripts/update_efc_api.py"])

    # ----------------------------------------------------
    # 5) GENERATE REPO MAP
    # ----------------------------------------------------
    print("\n[5] Generating repository map")
    run(["python", "scripts/generate_repo_map.py"])

    # ----------------------------------------------------
    # 6) CHECK IMPORTS FOR PYTHON SOURCE CLEANLINESS
    # ----------------------------------------------------
    print("\n[6] Checking Python import integrity")
    run(["python", "scripts/check_imports.py"], allow_fail=True)

    print("\n============== AUTOSYNC COMPLETE ==============\n")


if __name__ == "__main__":
    main()
