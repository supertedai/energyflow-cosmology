# FILE: /opt/symbiose/repo/apis/unified_api/routers/ingest.py

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from apis.unified_api.clients.qdrant_client import qdrant_ingest

router = APIRouter(tags=["ingest"])


class IngestTextPayload(BaseModel):
    text: str
    source: str | None = None


@router.post("/")
async def ingest_file(file: UploadFile = File(...)):
    """
    Ingest via filopplasting (f.eks. fra GUI / form-data).
    Route: POST /ingest/
    """
    content = (await file.read()).decode()
    return qdrant_ingest(content, source=file.filename)


@router.post("/text")
async def ingest_text(payload: IngestTextPayload):
    """
    Ingest ren tekst via JSON.
    Route: POST /ingest/text
    """
    return qdrant_ingest(payload.text, source=payload.source or "json")
