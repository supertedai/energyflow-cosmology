from fastapi import FastAPI
from routers import rag, ingest, embed, neo4j, graph_rag

app = FastAPI(title="Unified Symbiose API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(rag.router)
app.include_router(ingest.router)
app.include_router(embed.router)
app.include_router(neo4j.router)
app.include_router(graph_rag.router)
