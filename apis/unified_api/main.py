# FILE: apis/unified_api/main.py

from fastapi import FastAPI

# Routers
from apis.unified_api.routers.neo4j import router as neo4j_router
from apis.unified_api.routers.rag_router import router as rag_router
from apis.unified_api.routers.graph_rag import router as graph_rag_router
from apis.unified_api.routers.unified_query import router as unified_query_router
from apis.unified_api.routers.ingest import router as ingest_router
from apis.unified_api.routers.embed import router as embed_router

app = FastAPI(title="Unified Symbiose API")

@app.get("/health")
def health():
    return {"status": "ok"}

# Register routers
app.include_router(neo4j_router,      prefix="/neo4j")
app.include_router(rag_router,        prefix="/rag")
app.include_router(graph_rag_router,  prefix="/graph-rag")
app.include_router(unified_query_router)
app.include_router(ingest_router,     prefix="/ingest")
app.include_router(embed_router,      prefix="/embed")

