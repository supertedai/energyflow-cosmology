# FILE: /Users/morpheus/energyflow-cosmology/apis/unified_api/main.py

from dotenv import load_dotenv
load_dotenv()  # Load .env BEFORE any other imports

from fastapi import FastAPI
import sys
import os

# Add parent directory to path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from apis.unified_api.routers.neo4j import router as neo4j_router
from apis.unified_api.routers.rag_router import router as rag_router
from apis.unified_api.routers.graph_rag import router as graph_rag_router
from apis.unified_api.routers.unified_query import router as unified_query_router
from apis.unified_api.routers.ingest import router as ingest_router
from apis.unified_api.routers.embed import router as embed_router
from apis.unified_api.routers.gnn import router as gnn_router
from apis.unified_api.routers.chat import router as chat_router
from apis.unified_api.routers.efc_meta_learning import router as efc_router
from apis.unified_api.routers.msty_context import router as msty_router

app = FastAPI(title="Unified Symbiose API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

# Register routers with prefixes
app.include_router(neo4j_router, prefix="/neo4j", tags=["Neo4j"])
app.include_router(rag_router, prefix="/rag", tags=["RAG"])
app.include_router(graph_rag_router, prefix="/graph-rag", tags=["Graph-RAG"])
app.include_router(unified_query_router, tags=["Unified"])
app.include_router(ingest_router, prefix="/ingest", tags=["Ingest"])
app.include_router(embed_router, prefix="/embed", tags=["Embed"])
app.include_router(gnn_router, prefix="/gnn", tags=["GNN"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(efc_router, prefix="/efc", tags=["EFC Meta-Learning"])
app.include_router(msty_router, prefix="/msty", tags=["Msty AI Context"])

