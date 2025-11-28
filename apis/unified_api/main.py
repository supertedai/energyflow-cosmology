from fastapi import FastAPI

# Router imports
from apis.unified_api.routers.neo4j import router as neo4j_router
from apis.unified_api.routers.rag import router as rag_router
from apis.unified_api.routers.graph_rag import router as graph_rag_router

app = FastAPI(title="Unified Symbiose API")

@app.get("/health")
def health():
    return {"status": "ok"}

# Prefix bare her (ikke i router-filene)
app.include_router(neo4j_router, prefix="/neo4j")
app.include_router(rag_router, prefix="/rag")
app.include_router(graph_rag_router, prefix="/graph-rag")

