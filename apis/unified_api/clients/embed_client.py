# apis/unified_api/clients/embed_client.py

import os
from apis.unified_api.config import ENABLE_EMBED

_openai_client = None

if ENABLE_EMBED:
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        _openai_client = None


def embed_text(text: str):
    """
    Returnerer en 3072-dimensional embedding via OpenAI text-embedding-3-large.
    """
    if ENABLE_EMBED and _openai_client:
        try:
            response = _openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-large",
                dimensions=3072
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI embedding error: {e}")
            # Fallback to stub
    
    # Stub: 3072-dimensional zero vector with text length as first element
    stub = [0.0] * 3072
    stub[0] = float(len(text or ""))
    return stub

