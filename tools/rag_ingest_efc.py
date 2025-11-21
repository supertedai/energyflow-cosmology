#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Ingest EFC (Local Embeddings, Qdrant Cloud)
===============================================

- Leser alle PDF-er under docs/papers/efc
- Ekstraherer tekst
- Chunker tekst
- Lager deterministiske hashing-embeddings (ingen OpenAI)
- Tester Qdrant-tilkobling eksplisitt
- Upserter i Qdrant Cloud

Dette er en helt selvstendig ingest-pipeline som fungerer direkte
i GitHub Actions med kun:

    QDRANT_URL
    QDRANT_API_KEY

i GitHub Secrets.
"""

import os
import json
import uuid
import hashlib
import random
from pathlib import Path
from typing import List, Dict

from qdrant_client import QdrantClient
from qdrant_client import models as qm
from pypdf import PdfReader


# ------------------------------------------------------------
# KONFIG
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs" / "papers" / "efc"

EMBED_DIM = 1536  # matcher OpenAI dimensjon, men lokalt generert

DEFAULT_COLLECTION = "efc_rag_local"  # kan endres, men OK som er standard


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

def log(msg: str):
    print(f"[rag-ingest] {msg}", flush=True)


# ------------------------------------------------------------
# PDF-HÅNDTERING
# ------------------------------------------------------------

def iter_pdf_files() -> List[Path]:
    pdfs = sorted(DOCS_ROOT.rglob("*.pdf"))
    log(f"Fant {len(pdfs)} PDF-er under {DOCS_ROOT}")
    return pdfs


def extract_text_from_pdf(pdf: Path) -> str:
    try:
        reader = PdfReader(str(pdf))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception as e:
        log(f"Feil ved lesing av {pdf}: {e}")
        return ""


def chunk_text(text: str, chunk_size=2000, overlap=200) -> List[str]:
    chunks = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap

    return chunks


# ------------------------------------------------------------
# EMBEDDINGS (LOKAL, DETERMINISTISK)
# ------------------------------------------------------------

def deterministic_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]


# ------------------------------------------------------------
# METADATA
# ------------------------------------------------------------

def load_metadata(pdf: Path) -> Dict:
    folder = pdf.parent
    meta_file = folder / "metadata.json"

    if meta_file.exists():
        try:
            with meta_file.open() as f:
                return json.load(f)
        except:
            pass

    # fallback metadata
    return {
        "title": pdf.stem,
        "slug": folder.name,
        "keywords": [],
        "doi": None,
    }


# ------------------------------------------------------------
# QDRANT
# ------------------------------------------------------------

def get_qdrant_client():
    url = os.environ.get("QDRANT_URL")
    api = os.environ.get("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("QDRANT_URL mangler i miljøvariabler.")
    if not api:
        raise RuntimeError("QDRANT_API_KEY mangler i miljøvariabler.")

    return QdrantClient(url=url, api_key=api)


def test_qdrant_connection(client: QdrantClient):
    log("Tester Qdrant-tilkobling...")
    try:
        _ = client.get_collections()
        log("Qdrant-tilkobling OK.")
    except Exception as e:
        raise RuntimeError(f"Klarte ikke å koble til Qdrant: {e}")


def ensure_collection(client: QdrantClient, name: str):
    collections = {c.name for c in client.get_collections().collections}

    if name in collections:
        log(f"Collection '{name}' finnes allerede.")
        return

    log(f"Lager collection '{name}' (dim={EMBED_DIM})...")
    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=EMBED_DIM, distance=qm.Distance.COSINE),
    )
    log("Collection opprettet.")


# ------------------------------------------------------------
# INGEST-LOGIKK
# ------------------------------------------------------------

def ingest_pdf(pdf: Path, client: QdrantClient, collection: str) -> int:
    rel = pdf.relative_to(ROOT)
    log(f"Ingest: {rel}")

    text = extract_text_from_pdf(pdf)
    if not text:
        log("  Ingen tekst – hopper over.")
        return 0

    chunks = chunk_text(text)
    log(f"  {len(chunks)} chunks generert.")

    meta = load_metadata(pdf)

    points = []
    for idx, chunk in enumerate(chunks):
        vec = deterministic_embedding(chunk)

        payload = {
            "path": str(rel),
            "chunk_index": idx,
            "text": chunk,
            "paper_title": meta.get("title"),
            "slug": meta.get("slug"),
            "doi": meta.get("doi"),
            "keywords": meta.get("keywords"),
            "source": "efc_paper"
        }

        points.append(
            qm.PointStruct(
                id=uuid.uuid4().hex,
                vector=vec,
                payload=payload,
            )
        )

    client.upsert(collection_name=collection, points=points, wait=True)

    log(f"  Lagret {len(points)} chunks.")
    return len(points)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    log("Starter lokal RAG-ingest (uten OpenAI).")

    pdfs = iter_pdf_files()
    if not pdfs:
        log("Ingen PDF-er funnet. Avslutter.")
        return

    qc = get_qdrant_client()
    test_qdrant_connection(qc)

    ensure_collection(qc, DEFAULT_COLLECTION)

    total = 0
    for pdf in pdfs:
        total += ingest_pdf(pdf, qc, DEFAULT_COLLECTION)

    log(f"Ferdig. Totalt ingestet: {total} chunks.")


if __name__ == "__main__":
    main()
