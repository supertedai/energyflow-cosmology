from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import re
from pathlib import Path

INDEX_PATH = Path("semantic-search-index.json")

app = FastAPI(
    title="EFC Semantic Node API",
    description="Semantic search interface for the Energy-Flow Cosmology repository.",
    version="1.0"
)

# CORS: allow everything locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_index():
    if not INDEX_PATH.exists():
        raise FileNotFoundError("semantic-search-index.json not found.")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("nodes", [])

NODES = load_index()

def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())

def score_node(node, tokens):
    score = 0

    # id
    if "id" in node:
        for t in tokens:
            if t in node["id"].lower():
                score += 4

    # summary
    if "summary" in node:
        summary_tokens = tokenize(node["summary"])
        score += len(set(tokens) & set(summary_tokens)) * 2

    # domain
    if "domain" in node:
        for t in tokens:
            if t == node["domain"]:
                score += 5

    # tags
    if "tags" in node:
        tags = [t.lower() for t in node["tags"]]
        score += len(set(tokens) & set(tags)) * 3

    # layer
    if "layer" in node:
        for t in tokens:
            if t == node["layer"].lower():
                score += 3

    return score


@app.get("/")
async def root():
    return {"message": "EFC Semantic Node API is running."}


@app.get("/search")
async def search(query: str, top_k: int = 5):
    tokens = tokenize(query)

    scored = []
    for node in NODES:
        s = score_node(node, tokens)
        if s > 0:
            scored.append((s, node))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [{ "score": s, **n } for s, n in scored[:top_k]]

    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


@app.get("/node/{node_id}")
async def get_node(node_id: str):
    for node in NODES:
        if node["id"] == node_id:
            return node
    return {"error": "Node not found"}
