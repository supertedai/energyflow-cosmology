# apis/unified_api/clients/embed_client.py

from apis.unified_api.config import ENABLE_EMBED

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("all-MiniLM-L6-v2") if ENABLE_EMBED else None
except Exception:
    _model = None


def embed_text(text: str):
    """Returnerer en embedding (ekte eller stub)."""

    if ENABLE_EMBED and _model:
        vec = _model.encode(text)
        return vec.tolist()

    # Stub (3D vector)
    l = float(len(text or ""))
    return [l, l/2.0, l/3.0]

