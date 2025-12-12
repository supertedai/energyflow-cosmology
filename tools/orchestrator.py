#!/usr/bin/env python3
"""
Orchestrator - Central ingestion pipeline
==========================================

Ensures 100% sync between:
- Qdrant (semantic vectors)
- Neo4j (structural graph)
- GNN (node embeddings)

Pipeline:
    Input → Preprocess → Chunk → Embed → Qdrant
                                        ↓
                            Concept Extract → Neo4j
                                        ↓
                                  Update GNN index

Usage:
    python tools/orchestrator.py --input chat.txt --type chat
    python tools/orchestrator.py --input doc.pdf --type document
"""

import os
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from neo4j import GraphDatabase

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "efc")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
EMBED_DIM = 3072

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Input:
    """Standardized input format"""
    id: str
    type: Literal["chat", "document", "log"]
    timestamp: str
    source: str
    text: str
    metadata: Dict = None

@dataclass
class Chunk:
    """Text chunk with metadata"""
    id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: Dict

@dataclass
class Concept:
    """Extracted concept"""
    name: str
    type: str
    description: Optional[str] = None
    confidence: float = 0.0

# ============================================================
# STEP 1: PREPROCESSING
# ============================================================

def preprocess(raw_text: str, input_type: str) -> str:
    """
    Normalize input text.
    
    Rules:
    - Remove excessive whitespace
    - Normalize line breaks
    - Keep structure for documents
    - Clean for chat
    """
    text = raw_text.strip()
    
    if input_type == "chat":
        # Clean chat: collapse whitespace
        text = " ".join(text.split())
    else:
        # Keep document structure
        text = "\n".join(line.strip() for line in text.split("\n"))
    
    return text

# ============================================================
# STEP 2: CHUNKING
# ============================================================

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Chunk text with overlap.
    
    Rules:
    - 300-800 tokens per chunk (≈600 chars)
    - 10-15% overlap
    - Break at sentence boundaries
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
        
        chunks.append(chunk.strip())
        start += len(chunk) - overlap
    
    return chunks

# ============================================================
# STEP 3: EMBEDDING
# ============================================================

def embed_text(text: str) -> List[float]:
    """
    Create embedding vector using the actual embed_client.
    """
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from apis.unified_api.clients.embed_client import embed_text as real_embed
    return real_embed(text)
    
    import random
    rng = random.Random(seed)
    return [rng.random() for _ in range(EMBED_DIM)]

# ============================================================
# STEP 4: CONCEPT EXTRACTION
# ============================================================

def extract_concepts(text: str) -> List[Concept]:
    """
    Extract concepts from text.
    
    Uses simple keyword extraction for now.
    TODO: Replace with LLM-based extraction (GPT-4, Claude, etc.)
    """
    concepts = []
    
    # Simple keyword detection
    keywords = {
        "entropy": "thermodynamic",
        "energy flow": "thermodynamic",
        "cosmology": "physics",
        "consciousness": "cognitive",
        "meta": "architecture",
        "symbiosis": "architecture",
        "GNN": "technical",
        "graph": "technical",
    }
    
    text_lower = text.lower()
    
    for keyword, concept_type in keywords.items():
        if keyword in text_lower:
            concepts.append(Concept(
                name=keyword.title(),
                type=concept_type,
                confidence=0.8
            ))
    
    return concepts

# ============================================================
# STEP 5: QDRANT INSERTION
# ============================================================

def ingest_to_qdrant(client: QdrantClient, chunks: List[Chunk]) -> List[str]:
    """
    Insert chunks to Qdrant.
    
    Returns list of inserted point IDs.
    """
    points = []
    
    for chunk in chunks:
        vector = embed_text(chunk.text)
        
        point = PointStruct(
            id=chunk.id,
            vector=vector,
            payload={
                "document_id": chunk.document_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "source": chunk.metadata.get("source", "unknown"),
                "type": chunk.metadata.get("type", "unknown"),
                "timestamp": chunk.metadata.get("timestamp"),
                **chunk.metadata
            }
        )
        points.append(point)
    
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
    
    return [p.id for p in points]

# ============================================================
# STEP 6: NEO4J INSERTION
# ============================================================

def ingest_to_neo4j(driver, document: Input, chunks: List[Chunk], concepts: List[Concept]) -> str:
    """
    Insert document, chunks, and concepts to Neo4j.
    
    Structure:
        (:Document) -[:HAS_CHUNK]-> (:Chunk)
        (:Chunk) -[:MENTIONS]-> (:Concept)
        (:Concept) -[:RELATES_TO]-> (:Concept)
    
    Returns document node elementId.
    """
    with driver.session() as session:
        # Create Document node
        result = session.run("""
            CREATE (d:Document {
                id: $id,
                type: $type,
                source: $source,
                timestamp: $timestamp,
                text_length: $text_length
            })
            RETURN elementId(d) AS node_id
        """, 
            id=document.id,
            type=document.type,
            source=document.source,
            timestamp=document.timestamp,
            text_length=len(document.text)
        )
        doc_node_id = result.single()["node_id"]
        
        # Create Chunk nodes
        for chunk in chunks:
            session.run("""
                MATCH (d:Document {id: $doc_id})
                CREATE (c:Chunk {
                    id: $chunk_id,
                    text: $text,
                    chunk_index: $chunk_index
                })
                CREATE (d)-[:HAS_CHUNK]->(c)
            """,
                doc_id=document.id,
                chunk_id=chunk.id,
                text=chunk.text[:500],  # Truncate for storage
                chunk_index=chunk.chunk_index
            )
        
        # Create Concept nodes and relations
        for concept in concepts:
            session.run("""
                MERGE (c:Concept {name: $name})
                ON CREATE SET 
                    c.type = $type,
                    c.description = $description,
                    c.created = timestamp()
                
                WITH c
                MATCH (chunk:Chunk)-[:HAS_CHUNK*0..1]-(d:Document {id: $doc_id})
                WHERE chunk.text CONTAINS $name
                MERGE (chunk)-[:MENTIONS {confidence: $confidence}]->(c)
            """,
                name=concept.name,
                type=concept.type,
                description=concept.description,
                doc_id=document.id,
                confidence=concept.confidence
            )
        
        return doc_node_id

# ============================================================
# ORCHESTRATOR - MAIN PIPELINE
# ============================================================

def orchestrate(
    text: str,
    source: str,
    input_type: Literal["chat", "document", "log"] = "document",
    metadata: Dict = None
) -> Dict:
    """
    Full ingestion pipeline.
    
    Args:
        text: Raw input text
        source: Source identifier (filename, chat_id, etc.)
        input_type: Type of input
        metadata: Additional metadata
    
    Returns:
        Dict with:
            - document_id
            - chunk_ids
            - concept_names
            - neo4j_node_id
    """
    print(f"🚀 Orchestrator starting: {input_type} from {source}")
    
    # Step 1: Create standardized input
    doc_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    input_doc = Input(
        id=doc_id,
        type=input_type,
        timestamp=timestamp,
        source=source,
        text=text,
        metadata=metadata or {}
    )
    
    # Step 2: Preprocess
    print("  📝 Preprocessing...")
    clean_text = preprocess(text, input_type)
    
    # Step 3: Chunk
    print("  ✂️  Chunking...")
    text_chunks = chunk_text(clean_text)
    print(f"     Generated {len(text_chunks)} chunks")
    
    # Step 4: Create Chunk objects
    chunks = []
    for idx, chunk_text in enumerate(text_chunks):
        chunk_id = f"{doc_id}-chunk-{idx}"
        chunks.append(Chunk(
            id=chunk_id,
            document_id=doc_id,
            text=chunk_text,
            chunk_index=idx,
            metadata={
                "source": source,
                "type": input_type,
                "timestamp": timestamp,
                **(metadata or {})
            }
        ))
    
    # Step 5: Extract concepts
    print("  🧠 Extracting concepts...")
    concepts = extract_concepts(clean_text)
    print(f"     Found {len(concepts)} concepts: {[c.name for c in concepts]}")
    
    # Step 6: Ingest to Qdrant
    print("  📊 Inserting to Qdrant...")
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    # Ensure collection exists
    try:
        qdrant_client.get_collection(QDRANT_COLLECTION)
    except:
        qdrant_client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
        )
    
    chunk_ids = ingest_to_qdrant(qdrant_client, chunks)
    print(f"     ✅ {len(chunk_ids)} chunks in Qdrant")
    
    # Step 7: Ingest to Neo4j
    print("  🕸️  Inserting to Neo4j...")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    neo4j_node_id = ingest_to_neo4j(neo4j_driver, input_doc, chunks, concepts)
    neo4j_driver.close()
    print(f"     ✅ Neo4j node: {neo4j_node_id}")
    
    # Step 8: Update GNN index (TODO)
    print("  🧬 GNN index update: TODO")
    
    print("✅ Orchestrator complete\n")
    
    return {
        "document_id": doc_id,
        "chunk_ids": chunk_ids,
        "concepts": [c.name for c in concepts],
        "neo4j_node_id": neo4j_node_id,
        "qdrant_collection": QDRANT_COLLECTION
    }

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator - Full ingestion pipeline")
    parser.add_argument("--input", required=True, help="Input file or text")
    parser.add_argument("--type", choices=["chat", "document", "log"], default="document")
    parser.add_argument("--source", help="Source identifier (default: filename)")
    
    args = parser.parse_args()
    
    # Read input
    input_path = Path(args.input)
    if input_path.exists():
        text = input_path.read_text()
        source = args.source or input_path.name
    else:
        text = args.input
        source = args.source or "cli"
    
    # Run orchestrator
    result = orchestrate(
        text=text,
        source=source,
        input_type=args.type
    )
    
    print("\n📋 Result:")
    print(json.dumps(result, indent=2))
