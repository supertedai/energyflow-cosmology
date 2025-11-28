from fastapi import FastAPI

# Riktig modulnavn: unified_api (underscore)
from apis.unified_api.routers.rag import router as rag_router
# Ingest er deaktivert i Lag 1a
# from apis.unified_api.routers.ingest import router as ingest_router
from apis.unified_api.routers.neo4j import router as neo4j_router
from apis.unified_api.routers.graph_rag import router as graph_rag_router
from apis.unified_api.routers.embed import router as embed_router

app = FastAPI(title="Unified Symbiose API")

@app.get("/health")
def health():
    return {"status": "ok"}

# inkluder routers
app.include_router(rag_router)
# app.include_router(ingest_router)  # deaktivert
app.include_router(neo4j_router)
app.include_router(graph_rag_router)
app.include_router(embed_router)
