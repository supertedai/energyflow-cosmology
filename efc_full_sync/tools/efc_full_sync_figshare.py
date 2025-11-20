#!/usr/bin/env python3
"""
Figshare publishing module for EFC Full Sync Pipeline.
Handles:
- Article creation
- Metadata upload
- File upload (multipart)
- Final publish
- Error validation
"""

import json
import time
import requests
from pathlib import Path

FIGSHARE_API = "https://api.figshare.com/v2"


# -------------------------------
# Exceptions
# -------------------------------

class FigshareError(Exception):
    pass


# -------------------------------
# Utility functions
# -------------------------------

def _check_response(r, context=""):
    if not r.ok:
        raise FigshareError(
            f"{context} feilet: {r.status_code} {r.text}"
        )
    return r.json() if r.text else {}


# -------------------------------
# Article creation
# -------------------------------

def create_article(token: str, metadata: dict):
    """
    Creates a new Figshare article.
    Makes sure metadata obeys Figshare schema.
    """

    # --- Fix schema fields ---
    # funding must be a STRING, not a list
    if "funding" not in metadata or metadata["funding"] in (None, [], {}):
        metadata["funding"] = ""  # Empty string is valid

    # Convert list fields → valid format
    list_fields = ["tags", "keywords", "categories"]

    for field in list_fields:
        if field in metadata and isinstance(metadata[field], list):
            metadata[field] = [str(x) for x in metadata[field]]

    # Construct minimal required metadata
    article_payload = {
        "title": metadata.get("title", "EFC Paper"),
        "description": metadata.get("description", ""),
        "keywords": metadata.get("keywords", []),
        "categories": metadata.get("categories", []),
        "funding": metadata.get("funding", ""),
        "defined_type": metadata.get("defined_type", "preprint"),
        "is_metadata_record": False
    }

    headers = {"Authorization": f"token {token}"}
    r = requests.post(f"{FIGSHARE_API}/account/articles", json=article_payload, headers=headers)

    data = _check_response(r, "Artikkel-init")
    article_id = data["location"].split("/")[-1]

    return article_id


# -------------------------------
# File upload (multipart)
# -------------------------------

def upload_file(token: str, article_id: str, filepath: Path):
    """
    Uploads PDF to Figshare using multipart upload.
    """

    headers = {"Authorization": f"token {token}"}

    # 1. Initiate file upload
    init_payload = {"name": filepath.name}
    r = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/files",
        json=init_payload,
        headers=headers
    )
    file_info = _check_response(r, "File-init")
    file_id = file_info["location"].split("/")[-1]

    # 2. Get upload parts
    r = requests.get(
        f"{FIGSHARE_API}/account/articles/{article_id}/files/{file_id}",
        headers=headers
    )
    parts = _check_response(r, "Hent file parts")["upload_url"]

    # 3. Upload single-part file directly
    with open(filepath, "rb") as f:
        r = requests.put(parts, data=f)
        if not r.ok:
            raise FigshareError(f"File upload feilet: {r.status_code} {r.text}")

    # 4. Mark file as complete
    r = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/files/{file_id}",
        headers=headers
    )
    _check_response(r, "File-complete")

    return file_id


# -------------------------------
# Final publish
# -------------------------------

def publish_article(token: str, article_id: str):
    headers = {"Authorization": f"token {token}"}
    r = requests.post(
        f"{FIGSHARE_API}/account/articles/{article_id}/publish",
        headers=headers
    )
    _check_response(r, "Publish")


# -------------------------------
# Public function called by pipeline
# -------------------------------

def publish_pdf_to_figshare(pdf_path: str, metadata_path: str, figshare_token: str):
    """
    Main entrypoint used by efc_full_sync_builder.py.
    Handles:
    - Read metadata
    - Create article
    - Upload PDF
    - Publish
    Returns article ID and metadata for logging.
    """

    pdf_path = Path(pdf_path)
    metadata_path = Path(metadata_path)

    if not pdf_path.exists():
        raise FigshareError(f"PDF ikke funnet: {pdf_path}")

    if not metadata_path.exists():
        raise FigshareError(f"Metadata ikke funnet: {metadata_path}")

    with metadata_path.open() as f:
        metadata = json.load(f)

    # 1. Create article
    article_id = create_article(figshare_token, metadata)

    # 2. Upload file
    upload_file(figshare_token, article_id, pdf_path)

    # 3. Publish
    publish_article(figshare_token, article_id)

    return {
        "article_id": article_id,
        "url": f"https://figshare.com/account/articles/{article_id}"
    }
