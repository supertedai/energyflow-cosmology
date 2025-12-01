#!/usr/bin/env python
import os
from pathlib import Path
import textwrap
import requests

API_URL = os.getenv("API_URL", "http://localhost:8080")
COLLECTION = os.getenv("QDRANT_COLLECTION", "efc_docs")

# Mapper vi faktisk vil ingest'e fra
BASE_DIRS = [
    Path("docs"),
    Path("meta"),
    Path("symbiosis"),
    Path("theory"),
]

MAX_CHARS = 1200
OVERLAP = 200


def iter_source_files():
    """
    Gir liste over filer som skal ingestes.
    Filtrerer bort draft, old, tmp, etc.
    """
    for base in BASE_DIRS:
        if not base.exists():
            continue
        for ext in ("*.md", "*.txt"):
            for path in base.rglob(ext):
                name = path.name.lower()
                if any(tag in name for tag in ("draft", "old", "tmp")):
                    continue
                yield path


def chunk_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP):
    """
    Chunker tekst:
    - splitter på avsnitt
    - bygger chunks innenfor grensen
    - legger inn overlapp for kontekst
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        candidate = (current + "\n\n" + para).strip() if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            if len(para) > max_chars:
                for wrapped in textwrap.wrap(para, max_chars):
                    chunks.append(wrapped.strip())
                current = ""
            else:
                current = para

    if current:
        chunks.append(current.strip())

    # overlapp mellom chunks
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
            else:
                prev = overlapped[-1]
                tail = prev[-overlap:]
                merged = (tail + "\n\n" + ch).strip()
                overlapped.append(merged)
        chunks = overlapped

    return chunks


def ingest_chunk(text: str, source: str):
    """
    Sender chunk til unified-api /ingest som multipart/form-data.

    Antatt serversignatur (typisk FastAPI):
        file: UploadFile = File(...)
        source: str = Form(...)
        collection: str = Form(...)
    """

    # Fil-innholdet er bare selve teksten
    files = {
        "file": ("chunk.txt", text.encode("utf-8"), "text/plain")
    }

    data = {
        "source": source,
        "collection": COLLECTION,
    }

    resp = requests.post(f"{API_URL}/ingest", data=data, files=files, timeout=60)

    if not resp.ok:
        raise RuntimeError(
            f"Ingest failed for {source}: {resp.status_code} {resp.text}"
        )


def main():
    print(f"[INGEST] API_URL={API_URL} COLLECTION={COLLECTION}")
    total_files = 0
    total_chunks = 0

    for path in iter_source_files():
        rel = path.relative_to(Path("."))
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            continue

        chunks = chunk_text(text)
        if not chunks:
            continue

        total_files += 1

        for i, ch in enumerate(chunks):
            source = f"{rel}#chunk={i:04d}"
            ingest_chunk(ch, source)
            total_chunks += 1

        print(f"[INGEST] {rel} → {len(chunks)} chunks")

    print(f"[INGEST] Done. Files: {total_files}, chunks: {total_chunks}")


if __name__ == "__main__":
    main()
