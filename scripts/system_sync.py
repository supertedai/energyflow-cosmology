#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEM SYNC — Deep Sync Layer (Stable Version)
=============================================

Formål:
- Oppdatere EFC concepts
- Oppdatere EFC Semantic API
- Validere systemet
- Commit + push hvis noe har endret seg

Ingen repo-map.
Ingen pyvis.
Ingen eksterne avhengigheter.
Ikke koblet til Figshare eller instance-sync.

Kalles av system_sync.yml ved:
- push
- workflow_dispatch
"""

import subprocess
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# ------------------------------------------------------------
# DEFINER STEG: Disse er sikre og avhengighetsfrie
# ------------------------------------------------------------

STEPS = [
    ("Update concepts", ["python", "scripts/update_concepts.py"]),
    ("Update EFC API", ["python", "scripts/update_efc_api.py"]),
    ("Validate system", ["python", "scripts/validate_all.py"]),
]


# ------------------------------------------------------------
# HELPER FUNKSJONER
# ------------------------------------------------------------

def run_step(name, cmd):
    """Kjør et enkelt steg og stopp hvis det feiler."""
    print(f"\n=== {name} ===")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"✖ Failed: {name}")
        sys.exit(result.returncode)


def git_status():
    """Returnerer 'git status --porcelain' som string."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        capture_output=True
    )
    return result.stdout.strip()


def commit_and_push():
    """Commit og push kun hvis det er endringer."""
    status = git_status()

    if not status:
        print("✓ No changes to commit.")
        return

    print("\n📄 Changes detected:")
    print(status)

    subprocess.run(["git", "add", "-A"], cwd=ROOT)

    msg = f"System sync update — {datetime.utcnow().isoformat()} [skip ci]"
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT)

    print("🚀 System sync pushed successfully.")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    print("=== System Sync start ===")

    for name, cmd in STEPS:
        run_step(name, cmd)

    commit_and_push()

    print("\n=== System Sync complete ===")


if __name__ == "__main__":
    main()
