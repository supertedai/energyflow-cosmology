import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../.."))

META_INDEX = os.path.join(ROOT_DIR, "meta-index.json")
META_GRAPH = os.path.join(ROOT_DIR, "meta-graph/meta-graph.jsonld")


def load_json(path):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/index")
def get_meta_index():
    return load_json(META_INDEX)


@router.get("/graph")
def get_meta_graph():
    return load_json(META_GRAPH)


@router.get("/nodes")
def list_meta_nodes():
    graph = load_json(META_GRAPH)
    return [n.get("id") or n.get("@id") for n in graph.get("@graph", [])]


@router.get("/node/{node_id}")
def get_meta_node(node_id: str):
    graph = load_json(META_GRAPH)
    for n in graph.get("@graph", []):
        nid = n.get("id") or n.get("@id")
        if nid == node_id:
            return n
    raise HTTPException(status_code=404, detail="Node not found")
