from fastapi import APIRouter
from apis.unified_api.clients.embed_client import embed_text

router = APIRouter(prefix="/embed", tags=["embed"])

@router.post("/")
def embed_endpoint(payload: dict):
    text = payload.get("text", "")
    return {
        "embedding": embed_text(text),
        "length": len(text),
        "status": "ok"
    }

