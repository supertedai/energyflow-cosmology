from fastapi import APIRouter, UploadFile, File
from apis.unified_api.clients.qdrant_client import qdrant_ingest

router = APIRouter(tags=["ingest"])

@router.post("/")
async def ingest_file(file: UploadFile = File(...)):
    """
    Lag 1A – Qdrant-ingest stub.
    Leser filinnhold og sender det til qdrant_ingest (stub).
    """
    content = (await file.read()).decode()
    return qdrant_ingest(content)

