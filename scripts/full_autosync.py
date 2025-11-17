#!/usr/bin/env python3
"""
full_autosync.py — EFC Autosync v2.0

Formål:
- Hente inn alt av verdi (Figshare, schema, meta, API, README)
- Oppdatere alle kart og noder
- Validere hele systemet
- Kjør self-heal
- Commit + push hvis noe faktisk er endret

Ingen PDF, ingen LaTeX, ingen output/-støy.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


REPO_ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    ("Fetch Figshare metadata",       ["python", "scripts/fetch_figshare_auto.py"]),
    ("Update concepts",               ["python", "scripts/update_concepts.py"]),
    ("Update EFC API",                ["python", "scripts/update_efc_api.py"]),
    ("Generate repo map",             ["python", "scripts/generate_repo_map.py"]),
    ("Update all READMEs",            ["python", "scripts/update_all_readmes.py"]),
    ("Validate full system",          ["python", "scripts/validate_all.py"]),
    ("Run self-heal",                 ["python", "scripts/efc_self_heal.py"]),
]


def run(cmd, cwd=None, check=True):
    """Run a shell command with live output."""
    print(f"\n──▶ Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        print(f"✖ Command failed with code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result.returncode


def run_step(name, cmd):
    """Run a named step and log it."""
    print("\n" + "=" * 80)
    print(f"STEP: {name}")
    print("=" * 80)
    # Hvis scriptet ikke finnes, hopp over men ikke feile hele autosync
    script_path = REPO_ROOT / cmd[1]
    if not script_path.exists():
        print(f"⚠ Script not found, skipping: {script_path}")
        return
    run(cmd, cwd=REPO_ROOT, check=True)


def git_status_porcelain():
    """Return raw git status --porcelain output."""
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        print("⚠ git status failed, continuing without commit.")
        return ""
    return completed.stdout.strip()


def configure_git_user():
    """Ensure git user is set (works both locally og i GitHub Actions)."""
    run(["git", "config", "user.name", "github-actions"], cwd=REPO_ROOT, check=False)
    run(
        ["git", "config", "user.email", "github-actions@users.noreply.github.com"],
        cwd=REPO_ROOT,
        check=False,
    )


def git_commit_and_push():
    """Add, commit og push hvis det er endringer."""
    status = git_status_porcelain()
    if not status:
        print("\n✅ Ingen endringer etter autosync. Ingenting å committe.")
        return

    print("\n📄 Git status (endringer funnet):")
    print(status)

    configure_git_user()

    # Viktig: ikke referer til 'output/' eksplisitt → .gitignore håndterer det
    run(["git", "add", "-A"], cwd=REPO_ROOT, check=True)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    message = f"Autosync: system updated [{timestamp}] [skip ci]"
    run(["git", "commit", "-m", message], cwd=REPO_ROOT, check=True)

    # Bruk standard remote (GitHub Actions har allerede token via checkout)
    run(["git", "push"], cwd=REPO_ROOT, check=True)
    print("\n🚀 Autosync: endringer pushet til origin.")


def main():
    print("=== EFC Autosync v2.0 — start ===")

    for name, cmd in STEPS:
        run_step(name, cmd)

    git_commit_and_push()

    print("\n=== EFC Autosync v2.0 — done ===")


if __name__ == "__main__":
    main()
