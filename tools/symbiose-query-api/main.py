from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

# -------------------------------
# Models
# -------------------------------

class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    result: str
    source: str = "symbiose-query-api-v1"


# -------------------------------
# Health check
# -------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "api": "symbiose-query-api-v1"}


# -------------------------------
# Basic echo endpoint (v1)
# -------------------------------
# Denne gjør at API-en deployer 100% korrekt. 
# Etter deploy kan vi legge inn:
#   - Neo4j lookup
#   - Qdrant RAG
#   - metadata-søk
#   - IMX resonans
# -------------------------------

@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    text = payload.text.strip()

    # Minimal logikk – API fungerer, og kan utvides når Cloud Run er live.
    response = f"Symbiose API mottok teksten: '{text}'. Systemet kjører og er klart for utvidelser."

    return QueryResponse(result=response)
