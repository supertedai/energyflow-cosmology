#!/usr/bin/env python3
"""
Figshare integration for EFC Full Sync
Oppdatert: må inkludere filstørrelse ("size") i file-init for Figshare API.
"""

import os
import requests

FIGSHARE_TOKEN = os.getenv("FIGSHARE_TOKEN", "").strip()


class FigshareError(Exception):
    pass


def publish_pdf_to_figshare(title, description, keywords, pdf_path):
    """
    Publiser PDF til Figshare som draft.
    Returnerer DOI-informasjon hvis FIGSHARE_TOKEN finnes, ellers None.
    """

    if not FIGSHARE_TOKEN:
        print("[efc_full_sync] FIGSHARE_TOKEN mangler – hopper over Figshare.")
        return None

    print("[efc_full_sync] Publiserer til Figshare…")

    headers = {
        "Authorization": f"token {FIGSHARE_TOKEN}",
        "Content-Type": "application/json"
    }

    # ---------------------------------------------------------------
    # 1. Opprett artikkel (draft)
    # ---------------------------------------------------------------
    article_data = {
        "title": title,
        "description": description,
        "keywords": keywords,
        "defined_type": "preprint",
        "categories": [],
        "references": [],
        "funding": []
    }

    r = requests.post(
        "https://api.figshare.com/v2/account/articles",
        headers=headers,
        json=article_data
    )

    if r.status_code not in (201, 202):
        raise FigshareError(f"Figshare artikkel-init feilet: {r.status_code} {r.text}")

    article_id = r.json()["location"].split("/")[-1]
    print(f"[efc_full_sync] Figshare artikkel opprettet: {article_id}")

    # ---------------------------------------------------------------
    # 2. Last opp PDF
    # ---------------------------------------------------------------
    pdf_size = os.path.getsize(pdf_path)

    file_init = {
        "name": os.path.basename(pdf_path),
        "size": pdf_size
    }

    r = requests.post(
        f"https://api.figshare.com/v2/account/articles/{article_id}/files",
        headers=headers,
        json=file_init
    )

    if r.status_code not in (201, 202):
        raise FigshareError(f"Figshare file-init feilet: {r.status_code} {r.text}")

    file_info = r.json()
    file_id = file_info["id"]
    upload_url = file_info["upload_url"]

    print(f"[efc_full_sync] Fil-init OK. file_id={file_id}, size={pdf_size}")

    # ---------------------------------------------------------------
    # 3. Last opp selve filen (multipart upload)
    # ---------------------------------------------------------------
    with open(pdf_path, "rb") as f:
        r = requests.put(upload_url, data=f)

    if r.status_code not in (200, 201, 202):
        raise FigshareError(f"Figshare upload feilet: {r.status_code} {r.text}")

    print("[efc_full_sync] PDF upload fullført.")

    # ---------------------------------------------------------------
    # 4. Ferdigstill file
    # ---------------------------------------------------------------
    r = requests.post(
        f"https://api.figshare.com/v2/account/articles/{article_id}/files/{file_id}",
        headers=headers
    )

    if r.status_code not in (200, 202):
        raise FigshareError(f"Figshare file-complete feilet: {r.status_code} {r.text}")

    print("[efc_full_sync] File complete OK.")

    # ---------------------------------------------------------------
    # 5. Hent DOI
    # ---------------------------------------------------------------
    r = requests.get(
        f"https://api.figshare.com/v2/account/articles/{article_id}",
        headers=headers
    )

    if r.status_code != 200:
        raise FigshareError(f"Figshare DOI-fetch feilet: {r.status_code} {r.text}")

    data = r.json()

    return {
        "figshare_id": article_id,
        "doi": data.get("doi"),
        "version_doi": data.get("doi_url")
    }
