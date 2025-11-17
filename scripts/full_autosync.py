#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, allow_fail=False, label=None):
    print("\n-------------------------------------------")
    if label:
        print(f"▶ {label}")
    print(f"→ {cmd}")

    code = subprocess.call(cmd, shell=True)

    if code != 0 and not allow_fail:
        print(f"❌ Fatal error → stopping\nCommand: {cmd}")
        sys.exit(code)

    if code != 0 and allow_fail:
        print(f"⚠️ Non-critical error → continuing (exit {code})")

    return code


print("\n================== EFC FULL AUTOSYNC ==================")
print(f"Timestamp: {datetime.datetime.now().isoformat()}")
print("========================================================\n")


# -------------------------------------------------------
# 0. SELF-HEAL
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/efc_self_heal.py",
    allow_fail=False,
    label="Self-Heal: pakker, metodologi, fallback-kart"
)

# -------------------------------------------------------
# 1. FIGSHARE SYNC
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/fetch_figshare_auto.py",
    allow_fail=True,
    label="Figshare metadata sync (may fail without token)"
)

# -------------------------------------------------------
# 2. UPDATE CONCEPTS
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/update_concepts.py",
    allow_fail=False,
    label="Oppdaterer konsepter"
)

# -------------------------------------------------------
# 3. GENERATE METHODOLOGY API
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/generate_methodology_api.py",
    allow_fail=False,
    label="Genererer Methodology API"
)

# -------------------------------------------------------
# 4. UPDATE EFC API
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/update_efc_api.py",
    allow_fail=False,
    label="Oppdaterer EFC API"
)

# -------------------------------------------------------
# 5. GENERATE REPO MAP
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/generate_repo_map.py",
    allow_fail=True,
    label="Genererer repo-kart"
)

# -------------------------------------------------------
# 6. UPDATE **ALL** READMEs REKURSIVT ← HER MANGLET DET
# -------------------------------------------------------
run(
    f"python3 {ROOT}/scripts/update_all_readmes.py",
    allow_fail=False,
    label="Oppdaterer alle README-filer (rekursivt)"
)

print("\n========================================================")
print("EFC FULL AUTOSYNC FULLFØRT")
print("--------------------------------------------------------")
print("✓ Miljø reparert")
print("✓ Semantikk og API oppdatert")
print("✓ Figshare synkronisert (hvis token var aktivt)")
print("✓ Repo-kart generert")
print("✓ Alle README.md opprettet og oppdatert")
print("--------------------------------------------------------")
print("Systemet er nå i synk og selvreparerende.")
print("========================================================\n")
