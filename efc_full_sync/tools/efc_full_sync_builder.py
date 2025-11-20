#!/usr/bin/env python3
import os
import json
import subprocess
import sys

from efc_full_sync_zenodo import publish_pdf_to_zenodo


def run(cmd, cwd=None):
    print(f"[efc_full_sync] Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")


def load_metadata():
    with open("../config/paper_metadata.json") as f:
        return json.load(f)


def main():
    print("[efc_full_sync] Starter full pipeline…")

    meta = load_metadata()

    paper_title = meta["title"]
    paper_description = meta["description"]
    paper_keywords = meta["keywords"]

    # 1. Render Mermaid figures
    print("[efc_full_sync] Rendrer Mermaid…")
    run("python3 render_mermaid.py", cwd=".")

    # 2. Build PDF
    print("[efc_full_sync] Bygger PDF…")
    run("python3 build_pdf.py", cwd=".")

    pdf_path = "../production/latex/paper.pdf"
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF ikke funnet: {pdf_path}")

    print(f"[efc_full_sync] PDF OK: {pdf_path}")

    # 3. Publish to Zenodo
    print("[efc_full_sync] Laster opp til Zenodo…")

    doi_url = publish_pdf_to_zenodo(
        pdf_path=pdf_path,
        metadata={
            "token": os.environ["ZENODO_TOKEN"],
            "zenodo": {
                "title": paper_title,
                "upload_type": "publication",
                "publication_type": "article",
                "description": paper_description,
                "creators": [
                    {
                        "name": "Magnusson, Morten",
                        "orcid": "0009-0002-4860-5095"
                    }
                ],
                "keywords": paper_keywords
            }
        }
    )

    print(f"[efc_full_sync] Zenodo OK: {doi_url}")
    print("[efc_full_sync] FERDIG.")


if __name__ == "__main__":
    main()
