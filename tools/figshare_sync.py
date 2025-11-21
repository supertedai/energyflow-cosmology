#!/usr/bin/env python3
import os
import json
import requests
from pathlib import Path

FIGSHARE_ROOT = Path("figshare")
FILES_ROOT = FIGSHARE_ROOT / "files"
DOI_MAP = FIGSHARE_ROOT / "doi-map.json"

API_BASE = "https://api.figshare.com/v2"

TOKEN = os.getenv("FIGSHARE_TOKEN")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"token {TOKEN}"
}


def safe_write(path: Path, data):
    """Write data to file but ensure it's inside figshare/."""
    assert str(path.resolve()).startswith(str(FIGSHARE_ROOT.resolve()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            f.write(data)


def fetch_article(article_id):
    url = f"{API_BASE}/articles/{article_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def fetch_file(article_id, file_info):
    file_id = file_info["id"]
    file_name = file_info["name"]

    url = f"{API_BASE}/articles/{article_id}/files/{file_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    download_url = r.json()["download_url"]

    out_path = FILES_ROOT / str(article_id) / file_name
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Stream-download
    with requests.get(download_url, stream=True) as dl:
        dl.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in dl.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return str(out_path)


def sync_doi(article_id):
    print(f"[figshare] Syncing article {article_id}")

    data = fetch_article(article_id)

    # Write metadata
    safe_write(FIGSHARE_ROOT / f"{article_id}.json", data)

    # Download files
    downloaded = []
    for f in data.get("files", []):
        path = fetch_file(article_id, f)
        downloaded.append(path)

    # Update doi-map
    try:
        with open(DOI_MAP, "r", encoding="utf-8") as f:
            doi_map = json.load(f)
    except:
        doi_map = {}

    doi_map[data["doi"]] = {
        "article_id": article_id,
        "title": data["title"],
        "files": downloaded
    }

    safe_write(DOI_MAP, doi_map)


def main():
    print("[figshare] Starting sync")

    # List of Figshare IDs to sync — you can expand dynamically later
    ARTICLES = [
        # Add your Figshare article IDs here:
        # Example: 30642497
    ]

    if not TOKEN:
        raise SystemExit("Missing FIGSHARE_TOKEN env variable")

    for aid in ARTICLES:
        sync_doi(aid)

    print("[figshare] Done.")


if __name__ == "__main__":
    main()
