# FILE: /opt/symbiose/repo/apis/unified_api/routers/embed.py

from fastapi import APIRouter
from apis.unified_api.clients.embed_client import embed_text

# Ingen prefix her – prefix settes i main.py
router = APIRouter(tags=["embed"])

@router.post("/")
def embed_root(payload: dict):
    text = payload.get("text", "")
    return {
        "embedding": embed_text(text),
        "length": len(text),
        "status": "ok"
    }
