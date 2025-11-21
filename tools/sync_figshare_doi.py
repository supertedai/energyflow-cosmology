#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SYNC FIGSHARE DOI → REPO
========================

Gjør:

- Henter alle artikler fra Figshare-kontoen (account/articles)
- Matcher dem mot EFC-papers i docs/papers/efc/<slug>/
- Leser DOI fra Figshare-artikkelen
- Skriver DOI inn i:
    - metadata.json  (felt: "doi")
    - <slug>.jsonld  (felt: "doi")

Oppdaterer KUN hvis:
    - doi mangler, eller
    - doi == "pending"

Forventer miljøvariabel:
    FIGSHARE_TOKEN
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = ROOT / "docs" / "papers" / "efc"

FIGSHARE_API = "https://api.figshare.com/v2"


def log(msg: str) -> None:
    print(f"[sync-figshare-doi] {msg}", flush=True)


def get_figshare_token() -> str:
    token = os.environ.get("FIGSHARE_TOKEN")
    if not token:
        raise RuntimeError("FIGSHARE_TOKEN mangler i miljøvariabler.")
    return token


def fetch_all_account_articles(token: str) -> List[Dict[str, Any]]:
    """
    Henter alle artikler fra kontoen via /account/articles (paginert).
    """
    headers = {"Authorization": f"token {token}"}
    page = 1
    page_size = 100
    all_articles: List[Dict[str, Any]] = []

    log("Henter artikler fra Figshare-kontoen...")
    while True:
        resp = requests.get(
            f"{FIGSHARE_API}/account/articles",
            headers=headers,
            params={"page": page, "page_size": page_size},
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break
        all_articles.extend(items)
        page += 1

    log(f"Fant {len(all_articles)} artikler i Figshare-kontoen.")
    return all_articles


def normalize_slug(s: str) -> str:
    return (
        s.strip()
        .lower()
        .replace(" ", "-")
        .replace("_", "-")
    )


def find_article_for_slug(
    slug: str,
    articles: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Enkelt match:
    - slug i tittel (case-insensitive, normalisert)
    """
    norm_slug = normalize_slug(slug)

    candidates: List[Dict[str, Any]] = []
    for art in articles:
        title = art.get("title", "") or ""
        norm_title = normalize_slug(title)
        if norm_slug in norm_title:
            candidates.append(art)

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    # flere treff – ta den første, men logg
    log(f"Advarsel: Flere Figshare-artikler matcher slug '{slug}', velger første.")
    return candidates[0]


def load_metadata(paper_dir: Path) -> Dict[str, Any]:
    meta_path = paper_dir / "metadata.json"
    if not meta_path.exists():
        return {}
    try:
        with meta_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Advarsel: Klarte ikke å lese {meta_path}: {e}")
        return {}


def save_metadata(paper_dir: Path, data: Dict[str, Any]) -> None:
    meta_path = paper_dir / "metadata.json"
    try:
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        log(f"Oppdatert {meta_path} med DOI={data.get('doi')!r}.")
    except Exception as e:
        log(f"Feil ved skriving av {meta_path}: {e}")


def update_jsonld_doi(paper_dir: Path, doi: str) -> None:
    """
    Oppdaterer første .jsonld i mappen med feltet "doi".
    Hvis ingen .jsonld → gjør ingenting.
    """
    jsonld_files = sorted(paper_dir.glob("*.jsonld"))
    if not jsonld_files:
        return

    jsonld_path = jsonld_files[0]
    try:
        with jsonld_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log(f"Advarsel: Klarte ikke å lese {jsonld_path}: {e}")
        return

    # enkel: legg til / overskriv toppnivå-felt "doi"
    if isinstance(data, dict):
        data["doi"] = doi
    else:
        # vi forventer dict, men hvis ikke – ikke rør
        log(f"Advarsel: {jsonld_path} er ikke et JSON-objekt, hopper over DOI-oppdatering.")
        return

    try:
        with jsonld_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        log(f"Oppdatert {jsonld_path} med DOI={doi!r}.")
    except Exception as e:
        log(f"Feil ved skriving av {jsonld_path}: {e}")


def should_update_doi(current: Optional[str]) -> bool:
    """
    Vi oppdaterer hvis:
    - ingen DOI
    - DOI == 'pending' (case-insensitive)
    """
    if not current:
        return True
    if isinstance(current, str) and current.strip().lower() == "pending":
        return True
    return False


def sync_one_paper(
    slug: str,
    paper_dir: Path,
    articles: List[Dict[str, Any]],
) -> None:
    meta = load_metadata(paper_dir)
    current_doi = meta.get("doi")

    if not should_update_doi(current_doi):
        log(f"[{slug}] Har allerede DOI={current_doi!r}, hopper over.")
        return

    art = find_article_for_slug(slug, articles)
    if not art:
        log(f"[{slug}] Fant ingen Figshare-artikkel som matcher slug, hopper over.")
        return

    # noen ganger ligger DOI bare i detalj-endepunktet:
    token = get_figshare_token()
    headers = {"Authorization": f"token {token}"}
    art_id = art.get("id")
    if not art_id:
        log(f"[{slug}] Figshare-artikkel mangler id, hopper over.")
        return

    resp = requests.get(f"{FIGSHARE_API}/account/articles/{art_id}", headers=headers, timeout=30)
    resp.raise_for_status()
    art_full = resp.json()
    doi = art_full.get("doi") or art_full.get("doi_url")

    if not doi:
        log(f"[{slug}] Fant ingen DOI for Figshare-artikkel id={art_id}, hopper over.")
        return

    meta["doi"] = doi
    save_metadata(paper_dir, meta)
    update_jsonld_doi(paper_dir, doi)


def iter_paper_dirs() -> List[Path]:
    if not PAPERS_ROOT.exists():
        log(f"Fant ikke PAPERS_ROOT: {PAPERS_ROOT}")
        return []
    dirs = [p for p in PAPERS_ROOT.iterdir() if p.is_dir()]
    log(f"Fant {len(dirs)} paper-mapper under {PAPERS_ROOT}.")
    return sorted(dirs)


def main() -> None:
    log("Starter Figshare DOI-sync → repo...")

    token = get_figshare_token()
    articles = fetch_all_account_articles(token)
    paper_dirs = iter_paper_dirs()

    if not paper_dirs:
        log("Ingen papers å prosessere. Avslutter.")
        return

    for paper_dir in paper_dirs:
        slug = paper_dir.name
        log(f"--- Behandler slug: {slug} ---")
        try:
            sync_one_paper(slug, paper_dir, articles)
        except Exception as e:
            log(f"Feil ved sync av slug={slug}: {e}")

    log("Figshare DOI-sync ferdig.")


if __name__ == "__main__":
    main()
