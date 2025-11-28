from fastapi import FastAPI

# Viktig: bruk absolutte imports basert på repo-strukturen
from apis.unified-api.routers.rag import router as rag_router
from apis.unified-api.routers.ingest import router as ingest_router
from apis.unified-api.routers.neo4j_ops import router as neo4j_router
from apis.unified-api.routers.graph_rag import router as graph_rag_router
# embed-router finnes ikke — fjernet. Legg til hvis du har den.

app = FastAPI(title="Unified Symbiose API")

@app.get("/health")
def health():
    return {"status": "ok"}

# registrer routers
app.include_router(rag_router)
app.include_router(ingest_router)
app.include_router(neo4j_router)
app.include_router(graph_rag_router)
