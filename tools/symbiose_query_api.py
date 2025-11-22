#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

GNN_OUTPUT_DIR = Path(os.getenv("GNN_OUTPUT_DIR", "symbiose_gnn_output"))
EMBEDDINGS_PATH = GNN_OUTPUT_DIR / "node_embeddings.json"
MAPPING_PATH = GNN_OUTPUT_DIR / "node_mapping.json"

app = FastAPI(
    title="Symbiose Graph / GNN Query API",
    description=(
        "Spørrings-API for EFC / Symbiose-grafen basert på GNN-embeddings. "
        "Gir deg nærmeste noder i grafens embedding-rom."
    ),
    version="0.1.0",
)

# ------------------------- Datamodeller -------------------------


class NearestRequest(BaseModel):
    node_index: int
    top_k: int = 10
    label_filter: Optional[List[str]] = None  # f.eks ["EFCPaper", "MetaNode"]


class NearestNode(BaseModel):
    node_index: int
    neo_id: Optional[int] = None
    labels: Optional[List[str]] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    score: float


class NearestResponse(BaseModel):
    query_node_index: int
    results: List[NearestNode]


class NodeInfo(BaseModel):
    node_index: int
    neo_id: Optional[int] = None
    labels: Optional[List[str]] = None
    slug: Optional[str] = None
    title: Optional[str] = None
    raw: Dict[str, Any]


# ------------------------- Lasting av data -------------------------

_embeddings: Optional[np.ndarray] = None
_embeddings_norm: Optional[np.ndarray] = None
_mapping: Optional[Dict[int, Dict[str, Any]] = None]


def _load_embeddings() -> np.ndarray:
    if not EMBEDDINGS_PATH.exists():
        raise RuntimeError(f"Fant ikke embeddings-fil: {EMBEDDINGS_PATH}")
    with EMBEDDINGS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # forventer: {"0": [...], "1": [...], ...} eller [ [...], [...], ... ]
    if isinstance(data, dict):
        # sortér på nøkkel for deterministisk rekkefølge
        items = [data[str(i)] for i in sorted(map(int, data.keys()))]
    else:
        items = data

    arr = np.asarray(items, dtype=np.float32)
    if arr.ndim != 2:
        raise RuntimeError(f"Forventet 2D-embeddings, fikk shape={arr.shape}")
    return arr


def _load_mapping() -> Dict[int, Dict[str, Any]]:
    if not MAPPING_PATH.exists():
        raise RuntimeError(f"Fant ikke mapping-fil: {MAPPING_PATH}")
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    mapping: Dict[int, Dict[str, Any]] = {}
    if isinstance(data, dict):
        # forventer {"0": {...}, "1": {...}, ...}
        for k, v in data.items():
            mapping[int(k)] = v
    elif isinstance(data, list):
        for idx, v in enumerate(data):
            mapping[idx] = v
    else:
        raise RuntimeError("Ukjent format på node_mapping.json")

    return mapping


def _ensure_loaded():
    global _embeddings, _embeddings_norm, _mapping
    if _embeddings is None or _embeddings_norm is None or _mapping is None:
        emb = _load_embeddings()
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb_norm = emb / norms

        _embeddings = emb
        _embeddings_norm = emb_norm
        _mapping = _load_mapping()


# ------------------------- Hjelpefunksjoner -------------------------


def _cosine_top_k(
    query_index: int,
    top_k: int,
    label_filter: Optional[List[str]] = None,
) -> List[NearestNode]:
    _ensure_loaded()
    emb_norm = _embeddings_norm
    mapping = _mapping

    if query_index < 0 or query_index >= emb_norm.shape[0]:
        raise HTTPException(status_code=400, detail="node_index utenfor gyldig område")

    q = emb_norm[query_index : query_index + 1, :]
    scores = (emb_norm @ q.T).reshape(-1)  # cos-sim mot alle

    # sorter synkende
    order = np.argsort(-scores)

    results: List[NearestNode] = []
    for idx in order:
        if int(idx) == int(query_index):
            continue  # hopp over seg selv

        meta = mapping.get(int(idx), {})

        labels = meta.get("labels") or meta.get("label") or None
        if isinstance(labels, str):
            labels = [labels]

        # label-filtering
        if label_filter and labels:
            if not any(l in labels for l in label_filter):
                continue

        node = NearestNode(
            node_index=int(idx),
            neo_id=meta.get("neo_id") or meta.get("id"),
            labels=labels,
            slug=meta.get("slug"),
            title=meta.get("title"),
            score=float(scores[idx]),
        )
        results.append(node)
        if len(results) >= top_k:
            break

    return results


def _node_info(idx: int) -> NodeInfo:
    _ensure_loaded()
    mapping = _mapping

    if idx < 0 or idx >= _embeddings.shape[0]:
        raise HTTPException(status_code=404, detail="node_index ikke funnet")

    meta = mapping.get(idx, {})
    labels = meta.get("labels") or meta.get("label") or None
    if isinstance(labels, str):
        labels = [labels]

    return NodeInfo(
        node_index=idx,
        neo_id=meta.get("neo_id") or meta.get("id"),
        labels=labels,
        slug=meta.get("slug"),
        title=meta.get("title"),
        raw=meta,
    )


# ------------------------- Endepunkter -------------------------


@app.get("/health")
def health():
    ok = True
    errors = []

    if not EMBEDDINGS_PATH.exists():
        ok = False
        errors.append(f"Mangler {EMBEDDINGS_PATH}")
    if not MAPPING_PATH.exists():
        ok = False
        errors.append(f"Mangler {MAPPING_PATH}")

    status = "ok" if ok else "error"
    return {
        "status": status,
        "embeddings_path": str(EMBEDDINGS_PATH),
        "mapping_path": str(MAPPING_PATH),
        "errors": errors,
    }


@app.get("/node/{node_index}", response_model=NodeInfo)
def get_node(node_index: int):
    """
    Returner metadata for en node gitt dens embedding-indeks.
    """
    return _node_info(node_index)


@app.post("/nearest", response_model=NearestResponse)
def nearest(req: NearestRequest):
    """
    Finn nærmeste noder i GNN-embedding-rommet.
    """
    results = _cosine_top_k(
        query_index=req.node_index,
        top_k=req.top_k,
        label_filter=req.label_filter,
    )
    return NearestResponse(
        query_node_index=req.node_index,
        results=results,
    )
