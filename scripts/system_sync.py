#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYSTEM SYNC — Deep Sync Layer
==============================

Formål:
- Oppdatere concepts
- Oppdatere API
- Oppdatere repo map
- Validere alt
- Commit + push

Kalles av system_sync.yml ved:
- push
- workflow_dispatch
"""

import subprocess
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Update concepts", ["python", "scripts/update_concepts.py"]),
    ("Update EFC API", ["python", "scripts/update_efc_api.py"]),
    ("Generate repo map", ["python", "scripts/generate_repo_map.py"]),
    ("Validate system", ["python", "scripts/validate_all.py"]),
]


def run_step(name, cmd):
    print(f"\n=== {name} ===")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"✖ Failed: {name}")
        sys.exit(r.returncode)


def git_changes():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def commit_and_push():
    if not git_changes():
        print("No changes to commit.")
        return

    subprocess.run(["git", "add", "-A"], cwd=ROOT)
    msg = f"System sync update — {datetime.utcnow()} [skip ci]"
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT)
    print("✓ Pushed.")


def main():
    print("=== System Sync start ===")

    for name, cmd in STEPS:
        run_step(name, cmd)

    commit_and_push()

    print("=== System Sync done ===")


if __name__ == "__main__":
    main()
