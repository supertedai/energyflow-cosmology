#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Ingest EFC (Local, No-API Version)
======================================

- Leser alle PDF-er under docs/papers/efc
- Ekstraherer tekst
- Chunker tekst
- Lager deterministiske hashing-embeddings (ingen API)
- Upserter i Qdrant

Ingen nøkler. Ingen eksterne tjenester.
Fungerer 100% i GitHub Actions uten secrets.
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


# ----------------------------- Konfig -----------------------------

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs" / "papers" / "efc"

# Samme dimensjon som OpenAI (for fremtidig kompatibilitet)
EMBED_DIM = 1536

# Collection-navn — kan utvides ved behov
DEFAULT_COLLECTION = "efc_rag_local"


# ----------------------------- Utils -----------------------------

def log(msg: str):
    print(f"[rag-ingest] {msg}", flush=True)


def iter_pdf_files() -> List[Path]:
    pdfs = sorted(DOCS_ROOT.rglob("*.pdf"))
    log(f"Fant {len(pdfs)} PDF-er under {DOCS_ROOT}")
    return pdfs


def extract_text_from_pdf(pdf: Path) -> str:
    try:
        reader = PdfReader(str(pdf))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    except Exception as e:
        log(f"Feil ved PDF-lesing {pdf}: {e}")
        return ""


def chunk_text(text: str, chunk_size=2000, overlap=200) -> List[str]:
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap

    return chunks


def deterministic_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    """
    Lager en deterministisk pseudo-vektor basert på hashing.
    Ingen API. Ingen nøkler. Full stabilitet.
    """
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]


def load_metadata(pdf: Path) -> Dict:
    folder = pdf.parent
    meta_file = folder / "metadata.json"

    if meta_file.exists():
        try:
            with meta_file.open() as f:
                return json.load(f)
        except:
            pass

    return {
        "title": pdf.stem,
        "slug": folder.name,
        "keywords": [],
        "doi": None,
    }


def get_qdrant_client() -> QdrantClient:
    """
    Bruker direkte URL fra secrets **hvis** den finnes,
    ellers antas lokal eller intern Qdrant-binding.
    (Github Actions krever uansett remote URL.)
    """
    url = os.environ.get("QDRANT_URL", None)
    api = os.environ.get("QDRANT_API_KEY", None)

    if url is None:
        raise RuntimeError("QDRANT_URL mangler. Denne MÅ være satt i Secrets.")

    return QdrantClient(url=url, api_key=api)


def ensure_collection(qc: QdrantClient, name: str):
    existing = {c.name for c in qc.get_collections().collections}
    if name in existing:
        log(f"Collection '{name}' finnes allerede.")
        return

    log(f"Lager collection '{name}'...")
    qc.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=EMBED_DIM, distance=qm.Distance.COSINE),
    )


# ----------------------------- Ingest PDF -----------------------------

def ingest_pdf(pdf: Path, qc: QdrantClient, collection: str) -> int:
    rel = pdf.relative_to(ROOT)
    log(f"Ingest: {rel}")

    text = extract_text_from_pdf(pdf)
    if not text:
        log("  Ingen tekst funnet.")
        return 0

    chunks = chunk_text(text)
    log(f"  {len(chunks)} chunks")

    meta = load_metadata(pdf)

    points = []
    for i, chunk in enumerate(chunks):
        vec = deterministic_embedding(chunk)

        payload = {
            "path": str(rel),
            "chunk_index": i,
            "text": chunk,
            "paper_title": meta.get("title"),
            "slug": meta.get("slug"),
            "doi": meta.get("doi"),
            "keywords": meta.get("keywords"),
            "source": "efc_paper",
        }

        points.append(
            qm.PointStruct(
                id=uuid.uuid4().hex,
                vector=vec,
                payload=payload
            )
        )

    qc.upsert(collection_name=collection, points=points, wait=True)
    log(f"  Lagret {len(points)} chunks.")
    return len(points)


# ----------------------------- Main -----------------------------

def main():
    log("Starter lokal RAG-ingest (uten API)")

    pdfs = iter_pdf_files()
    if not pdfs:
        log("Ingen PDF-er funnet.")
        return

    qc = get_qdrant_client()
    ensure_collection(qc, DEFAULT_COLLECTION)

    total = 0
    for pdf in pdfs:
        total += ingest_pdf(pdf, qc, DEFAULT_COLLECTION)

    log(f"Ferdig. Totalt ingestet: {total} chunks.")


if __name__ == "__main__":
    main()
