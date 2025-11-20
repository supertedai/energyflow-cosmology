#!/usr/bin/env python3
import json
import os
from pathlib import Path

import requests


THIS_ROOT = Path(__file__).resolve().parents[1]  # efc_full_sync/
REPO_ROOT = THIS_ROOT.parents[0]

# Token må alltid komme fra miljøvariabel
FIGSHARE_TOKEN = os.getenv("FIGSHARE_TOKEN", "")


class FigshareError(RuntimeError):
    pass


def publish_pdf_to_figshare(title: str, description: str, keywords: list[str], pdf_path: Path) -> dict | None:
    """
    Publiser PDF til Figshare og returner DOI-info.
    
    Returnerer:
        {
          "doi": "...",
          "version_doi": "...",
          "figshare_id": 12345
        }

    Hvis FIGSHARE_TOKEN ikke finnes -> returnerer None og pipeline går videre uten feil.
    """

    # Ingen token = ingen Figshare-publisering
    if not FIGSHARE_TOKEN:
        return None

    headers = {
        "Authorization": f"token {FIGSHARE_TOKEN}",
        "Content-Type": "application/json",
    }

    # === 1. Opprett Figshare artikkel (draft)
    payload = {
        "title": title,
        "description": description,
        "tags": keywords or [],
        "defined_type": "preprint",
    }

    r = requests.post(
        "https://api.figshare.com/v2/account/articles",
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )
    if r.status_code >= 300:
        raise FigshareError(f"Figshare artikkel-opprett feilet: {r.status_code} {r.text}")

    article_id = r.json().get("entity_id")
    if not article_id:
        raise FigshareError("Figshare ga ikke entity_id tilbake.")

    # === 2. Initier filopplasting
    init_payload = {"name": pdf_path.name}
    r = requests.post(
        f"https://api.figshare.com/v2/account/articles/{article_id}/files",
        headers=headers,
        data=json.dumps(init_payload),
        timeout=60,
    )
    if r.status_code >= 300:
        raise FigshareError(f"Figshare file-init feilet: {r.status_code} {r.text}")

    file_info = r.json()
    upload_url = file_info.get("upload_url")
    file_id = file_info.get("id")
    if not upload_url or not file_id:
        raise FigshareError("Figshare ga ikke upload_url eller file id.")

    # === 3. Last opp fil med PUT
    with pdf_path.open("rb") as f:
        put_r = requests.put(upload_url, data=f, timeout=300)
    if put_r.status_code >= 300:
        raise FigshareError(f"Figshare fil-upload feilet: {put_r.status_code} {put_r.text}")

    # === 4. Fullfør opplasting
    r = requests.post(
        f"https://api.figshare.com/v2/account/articles/{article_id}/files/{file_id}",
        headers=headers,
        timeout=60,
    )
    if r.status_code >= 300:
        raise FigshareError(f"Figshare file-complete feilet: {r.status_code} {r.text}")

    # === 5. Hent info om artikkel (DOI + version DOI)
    r = requests.get(
        f"https://api.figshare.com/v2/account/articles/{article_id}",
        headers=headers,
        timeout=60,
    )
    if r.status_code >= 300:
        raise FigshareError(f"Figshare get-article feilet: {r.status_code} {r.text}")

    article = r.json()

    doi = article.get("doi")
    version_doi = article.get("doi_url")

    if not doi:
        raise FigshareError("Figshare returnerte ikke DOI.")

    return {
        "doi": doi,
        "version_doi": version_doi,
        "figshare_id": article_id,
    }
