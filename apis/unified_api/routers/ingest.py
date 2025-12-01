# apis/unified_api/routers/ingest.py

from fastapi import APIRouter, UploadFile, File
from apis.unified_api.clients.qdrant_client import qdrant_ingest

router = APIRouter()

@router.post("/")
async def ingest_file(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    return qdrant_ingest(content, source=file.filename)

