#!/usr/bin/env python3
"""
RAG ingest direkte til Qdrant Cloud.

Leser relevante .md-filer fra repoet,
chunker tekst, lager embeddings og skriver til Qdrant.
"""

import os
import uuid
from pathlib import Path
from typing import List

from qdrant_client import QdrantClient, models
from openai import OpenAI


# === ENV ===
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# --- Viktig: EFC er eneste gyldige collection ---
QDRANT_COLLECTION = "efc"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3072"))

ROOT = Path(__file__).resolve().parent.parent

INCLUDE_DIRS = [
    "theory",
    "meta",
]

MAX_CHARS = 1500  # enkel chunksize per tekstbit


def log(msg: str) -> None:
    print(f"[INGEST] {msg}", flush=True)


def iter_files() -> List[Path]:
    for rel_dir in INCLUDE_DIRS:
        base = ROOT / rel_dir
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            yield path


def chunk_text(text: str, max_chars: int = MAX_CHARS) -> List[str]:
    text = text.replace("\r\n", "\n")
    paragraphs = text.split("\n\n")
    chunks = []
    buf = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 2 <= max_chars:
            buf = (buf + "\n\n" + para) if buf else para
        else:
            if buf:
                chunks.append(buf.strip())
            buf = para
    if buf:
        chunks.append(buf.strip())
    return chunks


def ensure_collection(client: QdrantClient) -> None:
    log(f"Recreate collection {QDRANT_COLLECTION} @ {QDRANT_URL}")
    client.recreate_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=EMBEDDING_DIM,
            distance=models.Distance.COSINE,
        ),
    )


def embed_texts(client: OpenAI, texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    fixed_vectors = []
    for d in resp.data:
        vec = d.embedding

        # --- SAFEGUARD: Tving embedding til korrekt dimensjon ---
        if len(vec) > EMBEDDING_DIM:
            vec = vec[:EMBEDDING_DIM]
        elif len(vec) < EMBEDDING_DIM:
            vec = vec + [0.0] * (EMBEDDING_DIM - len(vec))

        fixed_vectors.append(vec)

    return fixed_vectors


def main() -> None:
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL og QDRANT_API_KEY må være satt.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY må være satt.")

    log(f"ROOT={ROOT}")
    log(f"QDRANT_URL={QDRANT_URL}")
    log(f"COLLECTION={QDRANT_COLLECTION}")
    log(f"EMBEDDING_MODEL={EMBEDDING_MODEL} dim={EMBEDDING_DIM}")

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        prefer_grpc=False,
    )
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    ensure_collection(qdrant)

    files = list(iter_files())
    log(f"Filer funnet: {len(files)}")

    total_chunks = 0
    points_batch: List[models.PointStruct] = []
    BATCH_SIZE = 64

    for path in files:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        if not chunks:
            continue

        log(f"{rel} → {len(chunks)} chunks")
        vectors = embed_texts(openai_client, chunks)

        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            chunk_id = str(uuid.uuid4())  # <-- UUID fix

            payload = {
                "text": chunk,
                "source": str(rel),
                "chunk_id": chunk_id,
                "file_path": str(rel),
            }

            pt = models.PointStruct(
                id=chunk_id,
                vector=vec,
                payload=payload,
            )

            points_batch.append(pt)
            total_chunks += 1

            if len(points_batch) >= BATCH_SIZE:
                qdrant.upsert(
                    collection_name=QDRANT_COLLECTION,
                    points=points_batch,
                )
                log(f"Upsert batch, total so far: {total_chunks}")
                points_batch = []

    if points_batch:
        qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points_batch,
        )
        log(f"Upsert siste batch. Total chunks: {total_chunks}")

    log(f"Done. Files: {len(files)}, chunks: {total_chunks}")


if __name__ == "__main__":
    main()
