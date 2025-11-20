#!/usr/bin/env python3
import os
import subprocess
import sys


def run(cmd, cwd=None):
    print(f"[efc_full_sync] Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def main():
    print("[efc_full_sync] Starter full pipeline…")

    # 1. Mermaid
    print("[efc_full_sync] Rendrer Mermaid…")
    run("python3 render_mermaid.py", cwd=".")

    # 2. PDF
    print("[efc_full_sync] Bygger PDF…")
    run("python3 build_pdf.py", cwd=".")

    # 3. Sjekk PDF
    pdf_path = "../production/latex/paper.pdf"
    if not os.path.exists(pdf_path):
        print(f"[efc_full_sync] ADVARSEL: Fant ikke PDF på {pdf_path}")
        sys.exit(1)

    print(f"[efc_full_sync] PDF OK: {pdf_path}")
    print("[efc_full_sync] FERDIG. Ingen automatisk publisering (manuell Figshare/Zenodo).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[efc_full_sync] FEIL: {e}")
        sys.exit(1)
