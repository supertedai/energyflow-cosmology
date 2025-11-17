#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, allow_fail=False, label=None):
    print("\n-------------------------------------------")
    if label:
        print(f"▶ {label}")
    print(f"→ {cmd}")

    code = subprocess.call(cmd, shell=True)
    if code != 0 and not allow_fail:
        print(f"❌ Fatal error: {cmd}")
        sys.exit(code)
    if code != 0 and allow_fail:
        print(f"⚠️ Non-critical error — continuing (exit {code})")
    return code

# ====================================================
# 0. ENSURE REQUIRED PYTHON PACKAGES ARE INSTALLED
# ====================================================

print("\n================== SELF-HEAL ==================\n")
pkgs = ["requests", "pyvis", "PyYAML", "markdown", "pydantic", "python-dotenv"]

for p in pkgs:
    print(f"Checking package: {p}")
    try:
        __import__(p)
        print(f"✓ {p} OK")
    except ImportError:
        print(f"→ Installing {p} …")
        subprocess.call(f"pip install {p}", shell=True)

# ====================================================
# 1. ENSURE METHODOLOGY FILES EXIST
# ====================================================

METH = ROOT / "methodology"
METH.mkdir(exist_ok=True)

missing = [
    "symbiosis-interface.md",
    "symbiotic-process.md",
    "symbiotic-process-llm.md",
    "symbiotic-process-summary.md",
]

print("\n▶ Checking methodology files…")
placeholder = "# Auto-generated placeholder\n"

for f in missing:
    path = METH / f
    if not path.exists():
        print(f"→ Creating {f}")
        path.write_text(placeholder)
    else:
        print(f"✓ {f} exists")

# ====================================================
# 2. RUN ALL AUTOSYNC STAGES
# ====================================================

print("\n================= AUTOSYNC =====================\n")

run(
    f"python3 {ROOT}/scripts/fetch_figshare_auto.py",
    allow_fail=True,
    label="Fetch Figshare metadata (may fail without token)"
)

run(
    f"python3 {ROOT}/scripts/update_concepts.py",
    allow_fail=False,
    label="Update concepts"
)

run(
    f"python3 {ROOT}/scripts/generate_methodology_api.py",
    allow_fail=False,
    label="Generate Methodology API"
)

run(
    f"python3 {ROOT}/scripts/update_efc_api.py",
    allow_fail=False,
    label="Update EFC API"
)

# Repo-map MUST NOT STOP AUTOSYNC
run(
    f"python3 {ROOT}/scripts/generate_repo_map.py",
    allow_fail=True,
    label="Generate Repo Map (fallback mode)"
)

print("\n================ AUTOSYNC COMPLETE ================")
print("All steps completed. Self-heal applied. Repo map fallback enabled.\n")
