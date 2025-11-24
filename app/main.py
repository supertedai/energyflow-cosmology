from fastapi import FastAPI
from graph_rag.api import router as graph_rag_router

app = FastAPI(title="Graph-RAG API", version="1.1.0")
app.include_router(graph_rag_router, prefix="/graph")
