# models/embed.py
#
# Deterministic dummy embedding for v0.3.
# - Dimension is controlled by EMBEDDING_DIM (env), default 1536.
# - Same input text -> same vector.
# - Works with Qdrant as long as collection dimension matches EMBEDDING_DIM.

from __future__ import annotations

import hashlib
import os
from typing import List

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))


def _hash_to_float(seed: bytes, idx: int) -> float:
    """
    Simple deterministic float generator in [-1, 1] based on SHA256.
    """
    h = hashlib.sha256(seed + idx.to_bytes(4, "little")).digest()
    # Use first 8 bytes as integer, scale to [0, 1)
    v = int.from_bytes(h[:8], "little") / 2**64
    # Shift to [-1, 1]
    return 2.0 * v - 1.0


def embed_text(text: str) -> List[float]:
    """
    Return a deterministic dummy embedding for the given text.

    This is NOT semantic, but:
    - It is stable.
    - It has fixed length = EMBEDDING_DIM.
    - It allows Qdrant to be fully activated without OpenAI / HF models.
    """
    if text is None:
        text = ""

    seed = text.encode("utf-8")
    return [_hash_to_float(seed, i) for i in range(EMBEDDING_DIM)]

