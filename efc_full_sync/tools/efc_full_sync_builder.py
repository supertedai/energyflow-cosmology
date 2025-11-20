#!/usr/bin/env python3
import os
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

def run(cmd, cwd=None):
    print(f"[efc_full_sync] Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

def load_metadata():
    meta_path = "../config/paper_metadata.json"
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Mangler metadatafil: {meta_path}")
    with open(meta_path) as f:
        return json.load(f)

def main():
    print("[efc_full_sync] Starter full pipeline…")

    meta = load_metadata()
    title = meta["title"]

    # 1. Mermaid
    print("[efc_full_sync] Rendrer Mermaid…")
    run("python3 render_mermaid.py", cwd=".")

    # 2. PDF
    print("[efc_full_sync] Bygger PDF…")
    run("python3 build_pdf.py", cwd=".")

    pdf_path = "../production/latex/paper.pdf"
    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF ble ikke laget.")

    print(f"[efc_full_sync] PDF OK: {pdf_path}")

    # 3. Generer komplett paper-pakke
    print("[efc_full_sync] Genererer paper-pakke…")
    run("python3 generate_paper_package.py", cwd=".")

    print("[efc_full_sync] FERDIG. PDF + full pakke generert.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[efc_full_sync] FEIL: {e}")
        sys.exit(1)
