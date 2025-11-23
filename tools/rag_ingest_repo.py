#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Ingest – Repository (tekstlig innhold til Qdrant, collection 'efc')
=====================================================================

- Leser tekstlige filer i hele repoet (unntatt noen støy-mapper)
- Ekstraherer innhold
- Chunker tekst
- Lager deterministiske hashing-embeddings (samme stil som EFC-PDF-ingest)
- Upserter alt i Qdrant collection 'efc' med tydelig payload:

    source:  'repo'
    path:    relativ sti
    topic:   øverste mappenavn (meta, docs, schema, osv.)
    slug:    filnavn uten suffix

Bruker:

    QDRANT_URL
    QDRANT_API_KEY

fra miljø / GitHub Secrets.
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

# ------------------------------------------------------------
# KONFIG
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

# Mapper vi vil ha med
INCLUDE_DIRS = [
    "docs",
    "meta",
    "methodology",
    "schema",
    "api",
    "figshare",
    "symbiosis",
    "cognition",
    "theory",
]

# Mapper vi vil hoppe over helt (bygg, cache, .git osv.)
EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "build",
    "dist",
    ".idea",
    ".vscode",
}

# Filtyper vi anser som "tekstlig innhold"
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonld",
    ".yml",
    ".yaml",
    ".py",
    ".tex",
}

EMBED_DIM = 1536  # matcher EFC-ingest
DEFAULT_COLLECTION = "efc"


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

def log(msg: str):
    print(f"[rag-ingest-repo] {msg}", flush=True)


# ------------------------------------------------------------
# EMBEDDINGS (LOKAL, DETERMINISTISK – SAMME PRINSIPP SOM PDF-SCRIPTET)
# ------------------------------------------------------------

def deterministic_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]


# ------------------------------------------------------------
# QDRANT
# ------------------------------------------------------------

def get_qdrant_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api = os.environ.get("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("QDRANT_URL mangler i miljøvariabler.")
    if not api:
        raise RuntimeError("QDRANT_API_KEY mangler i miljøvariabler.")

    return QdrantClient(url=url, api_key=api)


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
# FIL-ITERERING
# ------------------------------------------------------------

def iter_repo_text_files() -> List[Path]:
    paths: List[Path] = []

    for inc in INCLUDE_DIRS:
        base = ROOT / inc
        if not base.exists():
            continue

        for path in base.rglob("*"):
            if not path.is_file():
                continue

            # Sjekk ekskluderte mapper
            if any(part in EXCLUDE_DIRS for part in path.relative_to(ROOT).parts):
                continue

            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue

            paths.append(path)

    log(f"Fant {len(paths)} tekstfiler i repoet.")
    return sorted(paths)


# ------------------------------------------------------------
# TEKSTUTTREKK
# ------------------------------------------------------------

def load_text(path: Path) -> str:
    try:
        # Enkel heuristikk for JSON-filer – vi kan lagre pent formaterte strenger
        if path.suffix.lower() in {".json", ".jsonld"}:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                obj = json.load(f)
            return json.dumps(obj, indent=2, ensure_ascii=False)

        # Andre filer: ren tekst
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    except Exception as e:
        log(f"Feil ved lesing av {path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    text = text.strip()
    if not text:
        return []

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
# METADATA
# ------------------------------------------------------------

def build_payload(path: Path, chunk: str, chunk_index: int) -> Dict:
    rel = path.relative_to(ROOT)
    parts = rel.parts

    topic = parts[0] if parts else "root"
    slug = path.stem

    return {
        "source": "repo",
        "path": str(rel),
        "topic": topic,
        "slug": slug,
        "chunk_index": chunk_index,
        "text": chunk,
    }


# ------------------------------------------------------------
# INGEST-LOGIKK
# ------------------------------------------------------------

def ingest_file(path: Path, client: QdrantClient, collection: str) -> int:
    rel = path.relative_to(ROOT)
    log(f"Ingest: {rel}")

    text = load_text(path)
    if not text:
        log("  Ingen tekst – hopper over.")
        return 0

    chunks = chunk_text(text)
    log(f"  {len(chunks)} chunks generert.")

    points = []
    for idx, ch in enumerate(chunks):
        vec = deterministic_embedding(ch)
        payload = build_payload(path, ch, idx)

        points.append(
            qm.PointStruct(
                id=uuid.uuid4().hex,
                vector=vec,
                payload=payload,
            )
        )

    if points:
        client.upsert(collection_name=collection, points=points, wait=True)
        log(f"  Lagret {len(points)} chunks.")
    return len(points)


def main():
    log("Starter RAG-ingest for repo-tekst (collection 'efc').")

    files = iter_repo_text_files()
    if not files:
        log("Ingen tekstfiler funnet. Avslutter.")
        return

    client = get_qdrant_client()
    ensure_collection(client, DEFAULT_COLLECTION)

    total_chunks = 0
    total_files = 0

    for path in files:
        total_files += 1
        total_chunks += ingest_file(path, client, DEFAULT_COLLECTION)

    log(f"Ferdig. Antall filer: {total_files}, totalt chunks: {total_chunks}.")


if __name__ == "__main__":
    main()
