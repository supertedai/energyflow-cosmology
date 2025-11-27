from fastapi import APIRouter
from sentence_transformers import SentenceTransformer

router = APIRouter(prefix="/embed")
model = SentenceTransformer("all-MiniLM-L6-v2")

@router.get("/")
def embed(text: str):
    return {"embedding": model.encode(text).tolist()}

