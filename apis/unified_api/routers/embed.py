from fastapi import APIRouter

router = APIRouter(prefix="/embed", tags=["embed"])

@router.get("/")
def embed_stub():
    return {"status": "embed_disabled_in_lag_1a"}

