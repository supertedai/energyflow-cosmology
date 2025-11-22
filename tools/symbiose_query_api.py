#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import torch
from symbiose_gnn.model import SymbioseGNN
from symbiose_gnn.embed import embed_nodes

# ---------------- ENV ----------------

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

MODEL_PATH = "symbiose_gnn/model.pt"

# ---------------- APP ----------------

app = FastAPI(title="Symbiose Query Layer")

class Query(BaseModel):
    question: str


# ---------------- HELPERS ----------------

def neo_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        database=NEO4J_DATABASE
    )


def graph_query(text: str):
    """Simple keyword GraphRAG search."""
    with neo_driver().session() as s:
        result = s.run(
            """
            MATCH (n)
            WHERE ANY(k IN n.keywords WHERE k CONTAINS $t)
               OR n.title CONTAINS $t
               OR n.description CONTAINS $t
            RETURN n LIMIT 10
            """,
            t=text
        )
        return [r["n"] for r in result]


def rag_query(text: str):
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return client.search(
        collection_name="efc_rag",
        query_vector=client.get_default_embedding(text),
        limit=5
    )


def gnn_resonance(nodes):
    """Compute resonance score from node embeddings."""
    if not os.path.exists(MODEL_PATH):
        return None

    model = SymbioseGNN.load_from_checkpoint(MODEL_PATH)
    model.eval()

    node_vecs = embed_nodes(nodes)
    with torch.no_grad():
        score = model(node_vecs).mean().item()
    return score


# ---------------- ROUTE ----------------

@app.post("/query")
def query_api(q: Query):

    graph_hits = graph_query(q.question)
    rag_hits = rag_query(q.question)

    gnn_score = gnn_resonance(graph_hits)

    return {
        "answer": f"Spørsmålet ditt er mottatt: '{q.question}'.",
        "graph_hits": [dict(n) for n in graph_hits],
        "rag_hits": [str(h.payload) for h in rag_hits],
        "gnn_resonance": gnn_score,
    }


# ---------------- MAIN ----------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8084)
