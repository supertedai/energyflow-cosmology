# -------------------------------------------------------------
# EFC Full Sync — Figshare Upload Helper
# Version: 2.0
# -------------------------------------------------------------

import requests
import json
import os
from pathlib import Path

FIGSHARE_API = "https://api.figshare.com/v2"
TOKEN = os.environ.get("FIGSHARE_TOKEN")

class FigshareError(Exception):
    pass

def _auth_headers():
    if not TOKEN:
        raise FigshareError("FIGSHARE_TOKEN is not set")
    return {
        "Authorization": f"token {TOKEN}",
        "Content-Type": "application/json"
    }

# -------------------------------------------------------------
# Create a new Figshare article (draft)
# -------------------------------------------------------------
def create_article(title, description, categories=None, tags=None, doi=None):
    payload = {
        "title": title,
        "description": description,
        "defined_type": "dataset"
    }

    if categories:
        payload["categories"] = categories

    if tags:
        payload["tags"] = tags

    if doi:
        payload["custom_fields"] = {"doi": doi}

    r = requests.post(
        f"{FIGSHARE_API}/account/articles",
        headers=_auth_headers(),
        data=json.dumps(payload)
    )

    if r.status_code not in (200, 201):
        raise FigshareError(f"Article creation failed: {r.status_code} {r.text}")

    return r.json()["location"], r.json()["entity_id"]

# -------------------------------------------------------------
# Upload a file to an article
# -------------------------------------------------------------
def upload_file(article_id, file_path):
    file_name = Path(file_path).name

    # 1. Init upload
    r = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/files",
        headers=_auth_headers(),
        data=json.dumps({"name": file_name})
    )
    if r.status_code not in (200, 201):
        raise FigshareError(f"Init upload failed: {r.status_code} {r.text}")

    file_info = r.json()
    file_id = file_info["id"]
    upload_url = file_info["upload_url"]

    # 2. Upload actual bytes
    with open(file_path, "rb") as f:
        r2 = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": "application/pdf"}
        )

    if r2.status_code not in (200, 201):
        raise FigshareError(f"Upload failed: {r2.status_code} {r2.text}")

    # 3. Mark upload complete
    r3 = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/files/{file_id}",
        headers=_auth_headers()
    )
    if r3.status_code not in (200, 201):
        raise FigshareError(f"Completion failed: {r3.status_code} {r3.text}")

# -------------------------------------------------------------
# Publish the article and return metadata
# -------------------------------------------------------------
def publish_article(article_id):
    r = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/publish",
        headers=_auth_headers()
    )
    if r.status_code not in (200, 201):
        raise FigshareError(f"Publish failed: {r.status_code} {r.text}")

    # Fetch final metadata
    meta = requests.get(
        f"{FIGSHARE_API}/account/articles/{article_id}",
        headers=_auth_headers()
    ).json()

    return {
        "id": article_id,
        "doi": meta.get("doi"),
        "published_date": meta.get("published_date"),
        "url": meta.get("url")
    }

# -------------------------------------------------------------
# Main wrapper used by builder
# -------------------------------------------------------------
def publish_pdf_to_figshare(pdf_path, title, description, categories=None, tags=None, doi=None):

    if not Path(pdf_path).exists():
        raise FigshareError(f"PDF not found: {pdf_path}")

    # Create draft
    location, article_id = create_article(
        title=title,
        description=description,
        categories=categories,
        tags=tags,
        doi=doi
    )

    # Upload PDF
    upload_file(article_id, pdf_path)

    # Publish and return metadata
    meta = publish_article(article_id)

    # Store latest metadata for autosync
    out = Path("figshare/latest.json")
    out.parent.mkdir(exist_ok=True)

    with open(out, "w") as f:
        json.dump(meta, f, indent=2)

    return meta
