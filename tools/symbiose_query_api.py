from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict
from pathlib import Path
from datetime import datetime
import json

app = FastAPI(title="symbiose-query-api-v1")

SEMANTIC_INDEX_PATH = Path("semantic-search-index.json")
NODE_EMBEDDINGS_PATH = Path("symbiose_gnn_output/node_embeddings.json")
NODE_MAPPING_PATH = Path("symbiose_gnn_output/node_mapping.json")

semantic_index: List[Dict[str, Any]] = []
node_embeddings: Dict[str, Any] | None = None
node_mapping: Dict[str, Any] | None = None


class QueryRequest(BaseModel):
    text: str
    limit: int = 5


class Match(BaseModel):
    id: Any | None = None
    text: str
    score: float | None = None
    metadata: Dict[str, Any] | None = None


class QueryResponse(BaseModel):
    timestamp: str
    query: str
    matches: List[Match]


@app.on_event("startup")
def load_data() -> None:
    global semantic_index, node_embeddings, node_mapping

    # Semantic index
    if SEMANTIC_INDEX_PATH.exists():
        try:
            semantic_index = json.loads(SEMANTIC_INDEX_PATH.read_text())
        except Exception as e:
            print(f"[WARN] Failed to load semantic index: {e}")
            semantic_index = []
    else:
        print("[WARN] semantic-search-index.json not found")
        semantic_index = []

    # GNN data (valgfritt – vi bare laster, bruker ikke aktivt ennå)
    if NODE_EMBEDDINGS_PATH.exists():
        try:
            node_embeddings = json.loads(NODE_EMBEDDINGS_PATH.read_text())
        except Exception as e:
            print(f"[WARN] Failed to load node embeddings: {e}")

    if NODE_MAPPING_PATH.exists():
        try:
            node_mapping = json.loads(NODE_MAPPING_PATH.read_text())
        except Exception as e:
            print(f"[WARN] Failed to load node mapping: {e}")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "api": "symbiose-query-api-v1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "semantic_index_loaded": bool(semantic_index),
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if not semantic_index:
        raise HTTPException(status_code=500, detail="Semantic index not loaded")

    q = req.text.strip().lower()
    if not q:
        raise HTTPException(status_code=400, detail="Empty query text")

    scored: List[tuple[float, Dict[str, Any]]] = []

    # veldig enkel scoring: substring-count
    for item in semantic_index:
        text = str(
            item.get("text")
            or item.get("content")
            or item.get("chunk")
            or ""
        )
        if not text:
            continue

        t_lower = text.lower()
        score = t_lower.count(q)
        if score > 0:
            scored.append((float(score), item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: req.limit]

    matches: List[Match] = []
    for score, item in top:
        text = str(
            item.get("text")
            or item.get("content")
            or item.get("chunk")
            or ""
        )
        meta = {
            k: v
            for k, v in item.items()
            if k not in {"id", "text", "content", "chunk"}
        }
        matches.append(
            Match(
                id=item.get("id"),
                text=text,
                score=score,
                metadata=meta or None,
            )
        )

    return QueryResponse(
        timestamp=datetime.utcnow().isoformat() + "Z",
        query=req.text,
        matches=matches,
    )
