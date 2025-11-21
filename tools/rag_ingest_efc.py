#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Ingest EFC
==============

- Går gjennom alle PDF-er under docs/papers/efc
- Leser tekst per PDF
- Chunker tekst i biter
- Lager embeddings med OpenAI
- Lagrer chunks som punkter i Qdrant

Forventer:
    OPENAI_API_KEY
    QDRANT_URL
    QDRANT_API_KEY

Valgfritt:
    RAG_COLLECTION_NAME  (default: "efc_rag")
    RAG_EMBED_MODEL      (default: "text-embedding-3-large")
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict

from qdrant_client import QdrantClient
from qdrant_client import models as qm
from pypdf import PdfReader

try:
    from openai import OpenAI
except ImportError:
    # Backward-compat for eldre openai-bibliotek
    import openai
    OpenAI = None


# ------------------------- Konfig -------------------------

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs" / "papers" / "efc"

DEFAULT_COLLECTION = os.environ.get("RAG_COLLECTION_NAME", "efc_rag")
EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "text-embedding-3-large")


# ------------------------- Hjelpefunksjoner -------------------------


def log(msg: str) -> None:
    print(f"[rag-ingest] {msg}", flush=True)


def load_rag_profile() -> Dict:
    """
    Leser auth/rag-profile.json om den finnes.
    Brukes kun som ekstra metadata / evt. default collection navn.
    """
    profile_path = ROOT / "auth" / "rag-profile.json"
    if not profile_path.exists():
        return {}

    try:
        with profile_path.open("r", encoding="utf-8") as f:
            profile = json.load(f)
    except Exception as e:
        log(f"Advarsel: Klarte ikke å lese rag-profile.json: {e}")
        return {}

    return profile or {}


def iter_pdf_files() -> List[Path]:
    if not DOCS_ROOT.exists():
        log(f"Fant ikke katalog: {DOCS_ROOT}")
        return []

    pdfs = sorted(DOCS_ROOT.rglob("*.pdf"))
    log(f"Fant {len(pdfs)} PDF-er under {DOCS_ROOT}")
    return pdfs


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt:
            parts.append(txt)
    return "\n".join(parts).strip()


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Enkel char-basert chunking.
    """
    chunks = []
    if not text:
        return chunks

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


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY mangler i miljøvariabler")

    if OpenAI is not None:
        return OpenAI(api_key=api_key)

    # Fallback for gammel openai-klient
    openai.api_key = api_key
    return openai


def get_embedding_dim(client) -> int:
    """
    Hent dimensjonen ved å gjøre ett dummy-kall.
    """
    dummy_text = "Energy-Flow Cosmology"
    log(f"Henter embedding-dimensjon fra modell '{EMBED_MODEL}'...")
    if OpenAI is not None and isinstance(client, OpenAI):
        resp = client.embeddings.create(model=EMBED_MODEL, input=[dummy_text])
        vec = resp.data[0].embedding
    else:
        resp = client.Embedding.create(model=EMBED_MODEL, input=[dummy_text])
        vec = resp["data"][0]["embedding"]
    dim = len(vec)
    log(f"Embedding-dimensjon: {dim}")
    return dim


def embed_texts(client, texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    if OpenAI is not None and isinstance(client, OpenAI):
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
        return [d.embedding for d in resp.data]

    # gammel klient
    resp = client.Embedding.create(model=EMBED_MODEL, input=texts)
    return [d["embedding"] for d in resp["data"]]


def get_qdrant_client() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("QDRANT_URL mangler i miljøvariabler")
    if not api_key:
        raise RuntimeError("QDRANT_API_KEY mangler i miljøvariabler")

    log(f"Kobler til Qdrant @ {url}")
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    collections = client.get_collections().collections
    existing = {c.name for c in collections}

    if name in existing:
        log(f"Collection '{name}' finnes allerede.")
        return

    log(f"Lager ny collection '{name}' (dim={vector_size})...")
    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(
            size=vector_size,
            distance=qm.Distance.COSINE,
        ),
    )
    log(f"Collection '{name}' opprettet.")


def load_paper_metadata(pdf_path: Path) -> Dict:
    """
    Forsøker å hente metadata fra metadata.json eller .jsonld i samme mappe.
    """
    meta = {}

    folder = pdf_path.parent

    cand_files = [
        folder / "metadata.json",
        *folder.glob("*.jsonld"),
    ]

    for mpath in cand_files:
        if not mpath.exists():
            continue
        try:
            with mpath.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # lagre "flate" felt vi bryr oss om
            for key in ("title", "slug", "doi", "keywords", "description"):
                if key in data:
                    meta[key] = data[key]
            # prøv typecase keywords
            if "keywords" in meta and isinstance(meta["keywords"], str):
                meta["keywords"] = [k.strip() for k in meta["keywords"].split(",") if k.strip()]
            break
        except Exception as e:
            log(f"Advarsel: Klarte ikke å lese metadata fra {mpath}: {e}")

    if "slug" not in meta:
        # bruk mappenavn som slug
        meta["slug"] = folder.name

    if "title" not in meta:
        meta["title"] = pdf_path.stem

    return meta


def ingest_pdf(
    pdf_path: Path,
    openai_client,
    qdrant_client: QdrantClient,
    collection_name: str,
    extra_profile: Dict,
    vector_dim: int,
) -> int:
    rel_path = pdf_path.relative_to(ROOT)
    log(f"Ingest: {rel_path}")

    text = extract_text_from_pdf(pdf_path)
    if not text:
        log(f"  Ingen tekst hentet fra {rel_path}, hopper over.")
        return 0

    chunks = chunk_text(text)
    log(f"  {len(chunks)} chunks generert.")

    if not chunks:
        return 0

    embeddings = embed_texts(openai_client, chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("Antall embeddings != antall chunks")

    points = []
    paper_meta = load_paper_metadata(pdf_path)

    for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
        if len(vec) != vector_dim:
            raise RuntimeError(
                f"Embedding-dimensjon mismatch: forventet {vector_dim}, fikk {len(vec)}"
            )

        payload = {
            "path": str(rel_path),
            "chunk_index": idx,
            "text": chunk,
            "paper_title": paper_meta.get("title"),
            "slug": paper_meta.get("slug"),
            "doi": paper_meta.get("doi"),
            "keywords": paper_meta.get("keywords"),
            "source": "efc_paper",
        }

        # legg til info fra rag-profile (f.eks. domain, project, etc.)
        for k, v in extra_profile.items():
            if k not in payload:
                payload[k] = v

        point_id = uuid.uuid4().hex
        points.append(
            qm.PointStruct(
                id=point_id,
                vector=vec,
                payload=payload,
            )
        )

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )

    log(f"  Lagret {len(points)} chunks i collection '{collection_name}'.")
    return len(points)


# ------------------------- Main -------------------------


def main() -> None:
    log("Starter RAG-ingest for EFC...")

    pdf_files = iter_pdf_files()
    if not pdf_files:
        log("Ingen PDF-er å ingest'e. Avslutter.")
        return

    rag_profile = load_rag_profile()
    collection_name = rag_profile.get("collection_name", DEFAULT_COLLECTION)

    openai_client = get_openai_client()
    qdrant_client = get_qdrant_client()

    # finn vektordimensjon én gang
    vector_dim = get_embedding_dim(openai_client)

    # sørg for at collection finnes
    ensure_collection(qdrant_client, collection_name, vector_dim)

    total_chunks = 0
    for pdf in pdf_files:
        try:
            total_chunks += ingest_pdf(
                pdf_path=pdf,
                openai_client=openai_client,
                qdrant_client=qdrant_client,
                collection_name=collection_name,
                extra_profile=rag_profile,
                vector_dim=vector_dim,
            )
        except Exception as e:
            log(f"Feil under ingest av {pdf}: {e}")

    log(f"Ferdig. Totalt lagret {total_chunks} chunks i Qdrant.")


if __name__ == "__main__":
    main()
