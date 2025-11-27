from fastapi import APIRouter, UploadFile, File
from clients.qdrant_client import qdrant_ingest

router = APIRouter(prefix="/ingest")

@router.post("/")
async def ingest_file(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    return qdrant_ingest(content)

