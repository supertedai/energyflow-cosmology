# -------------------------------------------------------------
# EFC Semantic Node API
# Complete backend for semantic search, ranking, graph export,
# embedding match, and index refresh.
# -------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import re
import numpy as np
from pathlib import Path

# -------------------------------------------------------------
# Index Loader
# -------------------------------------------------------------

INDEX_PATH = Path("semantic-search-index.json")

def load_index():
    """
    Loads the semantic search index from JSON file.
    """
    if not INDEX_PATH.exists():
        raise FileNotFoundError("semantic-search-index.json not found.")
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("nodes", [])

NODES = load_index()


# -------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------

def tokenize(text: str):
    """
    Lowercase tokenization for semantic matching.
    """
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def score_node(node: dict, tokens: list):
    """
    Simple symbolic semantic scoring based on:
    - id
    - summary
    - domain
    - tags
    - layer
    """
    score = 0

    # ID match
    if "id" in node:
        for t in tokens:
            if t in node["id"].lower():
                score += 4

    # Summary match
    if "summary" in node:
        summary_tokens = tokenize(node["summary"])
        score += len(set(tokens) & set(summary_tokens)) * 2

    # Domain match
    if "domain" in node:
        for t in tokens:
            if t == node["domain"]:
                score += 5

    # Tags match
    if "tags" in node:
        tags = [t.lower() for t in node["tags"]]
        score += len(set(tokens) & set(tags)) * 3

    # Layer match
    if "layer" in node:
        for t in tokens:
            if t == node["layer"].lower():
                score += 3

    return score


def cosine_similarity(a, b):
    """
    Computes cosine similarity between embedding vectors.
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# -------------------------------------------------------------
# FastAPI Application
# -------------------------------------------------------------

app = FastAPI(
    title="EFC Semantic Node API",
    description="Semantic search interface for the Energy-Flow Cosmology repository.",
    version="1.0",
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Routes
# -------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "EFC Semantic Node API is running."}


# -------------------------------------------------------------
# Semantic Search
# -------------------------------------------------------------

@app.get("/search")
async def search(query: str, top_k: int = 5):
    """
    Performs symbolic semantic search across all nodes.
    """
    tokens = tokenize(query)

    scored = []
    for node in NODES:
        s = score_node(node, tokens)
        if s > 0:
            scored.append((s, node))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [{"score": s, **n} for s, n in scored[:top_k]]

    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


# -------------------------------------------------------------
# Direct Node Lookup
# -------------------------------------------------------------

@app.get("/node/{node_id}")
async def get_node(node_id: str):
    for node in NODES:
        if node["id"] == node_id:
            return node
    return {"error": "Node not found"}


# -------------------------------------------------------------
# Embedding Ranking
# -------------------------------------------------------------

@app.post("/embedding-rank")
async def embedding_rank(embedding: List[float], top_k: int = 5):
    """
    Ranks nodes based on cosine similarity to the given embedding.
    Uses deterministic hashed text embedding for each node.
    """

    if not isinstance(embedding, list):
        return {"error": "Embedding must be a list of floats"}

    def node_embedding(node):
        text = node["id"] + " " + " ".join(node.get("tags", [])) + " " + node.get("summary", "")
        tokens = tokenize(text)

        vec = np.zeros(256)
        for t in tokens:
            idx = hash(t) % 256
            vec[idx] += 1

        return vec

    query_vec = np.array(embedding)
    results = []

    for node in NODES:
        node_vec = node_embedding(node)
        similarity = cosine_similarity(query_vec, node_vec)
        results.append((similarity, node))

    results.sort(key=lambda x: x[0], reverse=True)

    return [{"similarity": sim, **node} for sim, node in results[:top_k]]


# -------------------------------------------------------------
# Graph Export
# -------------------------------------------------------------

@app.get("/graph")
async def full_graph():
    """
    Returns all nodes + simple inferred edges.
    """
    edges = []

    for node in NODES:
        if "path" in node:
            parent = "/".join(node["path"].split("/")[:-2])
            if parent:
                edges.append({"from": parent, "to": node["id"]})

    return {"nodes": NODES, "edges": edges}


# -------------------------------------------------------------
# Refresh Semantic Index
# -------------------------------------------------------------

@app.post("/refresh-index")
async def refresh_index():
    """
    Reloads semantic-search-index.json from disk.
    """
    global NODES
    NODES = load_index()
    return {"status": "refreshed", "node_count": len(NODES)}
