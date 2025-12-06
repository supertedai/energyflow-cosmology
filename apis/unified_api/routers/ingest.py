# FILE: /opt/symbiose/repo/apis/unified_api/routers/ingest.py

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from apis.unified_api.clients.qdrant_client import qdrant_ingest

router = APIRouter(tags=["ingest"])


class IngestTextPayload(BaseModel):
    text: str
    source: str | None = None
    layer: str | None = None
    doi: str | None = None
    title: str | None = None
    description: str | None = None
    summary: str | None = None
    source_type: str | None = None
    section: str | None = None
    node_id: str | None = None  # 🔗 Neo4j node ID for GNN hybrid scoring


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
    Ingest ren tekst via JSON med full metadata.
    Route: POST /ingest/text
    
    Example payload:
    {
        "text": "Your content here",
        "source": "papers/efc-v2.md",
        "layer": "theory",
        "doi": "10.6084/m9.figshare.123456",
        "title": "Energy Flow Cosmology v2.0",
        "source_type": "paper"
    }
    """
    metadata = {
        "layer": payload.layer,
        "doi": payload.doi,
        "title": payload.title,
        "description": payload.description,
        "summary": payload.summary,
        "source_type": payload.source_type,
        "section": payload.section,
        "node_id": payload.node_id,  # 🔗 BRIDGE
    }
    return qdrant_ingest(
        payload.text, 
        source=payload.source or "json",
        metadata=metadata
    )
