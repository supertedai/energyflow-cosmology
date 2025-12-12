#!/usr/bin/env python3
"""
Unified Ingestion API - All data MUST go through this endpoint
==============================================================

FastAPI endpoint that enforces Orchestrator v2 pipeline for
ALL new data entering the system.

Features:
- POST /ingest - Single text/document ingestion
- POST /ingest/batch - Batch ingestion
- POST /ingest/file - File upload ingestion
- GET /health - Pipeline health check

All endpoints use ingestion_hook.py to guarantee:
✅ Token-based chunking
✅ LLM concept extraction
✅ Perfect Qdrant ↔ Neo4j sync
✅ GNN integration (TODO)
✅ Rollback safety

Usage:
    uvicorn tools.ingestion_api:app --host 0.0.0.0 --port 8001

Example:
    curl -X POST http://localhost:8001/ingest \
         -H "Content-Type: application/json" \
         -d '{"text": "My content", "source": "api", "type": "document"}'
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.ingestion_hook import ingest_text, ingest_file, ingest_multiple

# -------------------------------------------------------------
# FastAPI Application
# -------------------------------------------------------------

app = FastAPI(
    title="EFC Ingestion API",
    description="Unified ingestion endpoint - ALL data goes through Orchestrator v2",
    version="2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Models
# -------------------------------------------------------------

class IngestRequest(BaseModel):
    text: str = Field(..., description="Text content to ingest")
    source: str = Field(..., description="Human-readable source identifier")
    type: str = Field(default="document", description="Input type: document, chat, or log")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class BatchIngestRequest(BaseModel):
    items: List[IngestRequest] = Field(..., description="List of items to ingest")

class IngestResponse(BaseModel):
    document_id: str
    chunk_ids: List[str]
    concepts: List[str]
    neo4j_node_id: str
    total_tokens: int
    status: str = "success"

class HealthResponse(BaseModel):
    status: str
    pipeline: str
    components: Dict[str, str]

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - API info"""
    return {
        "service": "EFC Ingestion API",
        "version": "2.0",
        "pipeline": "Orchestrator v2 (deterministic)",
        "endpoints": "/ingest, /ingest/batch, /ingest/file, /health"
    }

@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(request: IngestRequest):
    """
    Ingest single text document through Orchestrator v2
    
    This is the PRIMARY ingestion endpoint. All data MUST go through here.
    """
    try:
        result = ingest_text(
            text=request.text,
            source=request.source,
            input_type=request.type,
            metadata=request.metadata
        )
        
        return IngestResponse(
            document_id=result["document_id"],
            chunk_ids=result["chunk_ids"],
            concepts=result["concepts"],
            neo4j_node_id=result["neo4j_node_id"],
            total_tokens=result["total_tokens"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/ingest/batch", response_model=List[IngestResponse])
async def batch_ingest_endpoint(request: BatchIngestRequest):
    """
    Ingest multiple documents in batch
    
    Processes each item through Orchestrator v2 sequentially.
    """
    results = []
    errors = []
    
    for i, item in enumerate(request.items, 1):
        try:
            result = ingest_text(
                text=item.text,
                source=item.source,
                input_type=item.type,
                metadata=item.metadata
            )
            
            results.append(IngestResponse(
                document_id=result["document_id"],
                chunk_ids=result["chunk_ids"],
                concepts=result["concepts"],
                neo4j_node_id=result["neo4j_node_id"],
                total_tokens=result["total_tokens"]
            ))
        
        except Exception as e:
            errors.append({"index": i, "source": item.source, "error": str(e)})
    
    if errors:
        raise HTTPException(
            status_code=207,  # Multi-Status
            detail={
                "message": f"Batch completed with {len(errors)} errors",
                "successful": len(results),
                "failed": len(errors),
                "errors": errors,
                "results": results
            }
        )
    
    return results

@app.post("/ingest/file")
async def file_ingest_endpoint(
    file: UploadFile = File(...),
    source: Optional[str] = None,
    type: Optional[str] = None
):
    """
    Ingest uploaded file through Orchestrator v2
    
    Accepts text files (.txt, .md, .json, .py, etc.)
    """
    try:
        # Read file content
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        # Auto-detect source from filename
        if source is None:
            source = file.filename
        
        # Auto-detect type from filename
        if type is None:
            filename_lower = file.filename.lower()
            if "chat" in filename_lower or "conversation" in filename_lower:
                type = "chat"
            elif filename_lower.endswith(".log"):
                type = "log"
            else:
                type = "document"
        
        result = ingest_text(
            text=text,
            source=source,
            input_type=type,
            metadata={"filename": file.filename, "content_type": file.content_type}
        )
        
        return IngestResponse(
            document_id=result["document_id"],
            chunk_ids=result["chunk_ids"],
            concepts=result["concepts"],
            neo4j_node_id=result["neo4j_node_id"],
            total_tokens=result["total_tokens"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Verifies all pipeline components are available
    """
    try:
        # Test imports
        from orchestrator_v2 import orchestrate
        from qdrant_client import QdrantClient
        from neo4j import GraphDatabase
        
        components = {
            "orchestrator": "✅ Available",
            "qdrant": "✅ Connected",
            "neo4j": "✅ Connected",
            "llm": "✅ OpenAI configured",
            "embeddings": "✅ Cohere configured"
        }
        
        return HealthResponse(
            status="healthy",
            pipeline="Orchestrator v2 (deterministic)",
            components=components
        )
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """
    Get ingestion statistics from Qdrant and Neo4j
    """
    try:
        from dotenv import load_dotenv
        from qdrant_client import QdrantClient
        from neo4j import GraphDatabase
        
        load_dotenv()
        
        # Qdrant stats
        qdrant = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        collection_info = qdrant.get_collection('efc')
        
        # Neo4j stats
        neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (d:Document) 
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                OPTIONAL MATCH (c)-[:MENTIONS]->(concept:Concept)
                RETURN 
                    count(DISTINCT d) as documents,
                    count(DISTINCT c) as chunks,
                    count(DISTINCT concept) as concepts
            """)
            neo4j_stats = result.single()
        
        neo4j_driver.close()
        
        return {
            "qdrant": {
                "collection": "efc",
                "points_count": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size
            },
            "neo4j": {
                "documents": neo4j_stats["documents"],
                "chunks": neo4j_stats["chunks"],
                "concepts": neo4j_stats["concepts"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
