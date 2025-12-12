#!/usr/bin/env python3
"""
Private Orchestrator - Chat, Reflection & Emergent Memory Pipeline
==================================================================

Purpose: Personal knowledge graph ISOLATED from EFC theory.

Differences from orchestrator_v2:
- Namespace: :PrivateDocument, :PrivateChunk, :PrivateConcept
- Collection: "private" (not "efc")
- NO GNN training (read-only access later)
- Memory classification (STM/LONGTERM/DISCARD)
- Feedback support (added after this layer)

Usage:
    python tools/private_orchestrator.py --input "your thought" --type chat
"""

import os
import json
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Literal, Tuple
from dataclasses import dataclass, asdict, field

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, PointIdsList
from neo4j import GraphDatabase
import tiktoken

load_dotenv()

# ============================================================
# CONFIG - PRIVATE NAMESPACE
# ============================================================

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "private"  # ⚠️ ISOLATED from "efc"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_PRIVATE = os.getenv("NEO4J_DB_PRIVATE", "private_mem")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Token-based chunking (same as orchestrator_v2)
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBED_DIM = 3072

TOKENIZER = tiktoken.get_encoding("cl100k_base")

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class PrivateInput:
    """Standardized private input"""
    id: str
    type: Literal["chat", "reflection", "note"]
    timestamp: str
    text: str
    metadata: Dict = None

@dataclass
class PrivateChunk:
    """Private chunk with memory classification"""
    id: str
    document_id: str
    text: str
    chunk_index: int
    token_count: int
    memory_class: Optional[str] = None  # STM|LONGTERM|DISCARD (set by classifier)
    metadata: Dict = None

@dataclass
class PrivateConcept:
    """Private concept (can be subjective)"""
    name: str
    type: str
    description: Optional[str] = None
    confidence: float = 0.0
    domain: str = "personal"
    subjective: bool = True  # Always true for private concepts

# ============================================================
# STEP 1: PREPROCESSING
# ============================================================

def preprocess(text: str, input_type: str) -> str:
    """Normalize input text"""
    text = text.strip()
    
    if input_type == "chat":
        text = " ".join(text.split())
    else:
        text = "\n".join(line.strip() for line in text.split("\n") if line.strip())
    
    return text

# ============================================================
# STEP 2: TOKEN-BASED CHUNKING
# ============================================================

def chunk_text_by_tokens(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Chunk text by tokens (same as orchestrator_v2)"""
    tokens = TOKENIZER.encode(text)
    
    if len(tokens) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = TOKENIZER.decode(chunk_tokens)
        
        # Try to break at sentence boundary
        if end < len(tokens) and '.' in chunk_text:
            last_period = chunk_text.rfind('. ')
            if last_period > len(chunk_text) * 0.5:
                chunk_text = chunk_text[:last_period + 1]
                chunk_tokens = TOKENIZER.encode(chunk_text)
        
        chunks.append(chunk_text.strip())
        advance = max(len(chunk_tokens) - overlap, 1)
        start += advance
    
    return chunks

# ============================================================
# STEP 3: EMBEDDING
# ============================================================

def embed_text(text: str) -> List[float]:
    """Create embedding vector"""
    from apis.unified_api.clients.embed_client import embed_text as real_embed
    return real_embed(text)

# ============================================================
# STEP 4: CONCEPT EXTRACTION (PRIVATE VERSION)
# ============================================================

def extract_concepts_llm(text: str) -> Tuple[List[PrivateConcept], Dict]:
    """
    Extract private concepts (can be subjective, speculative).
    
    Different from EFC extraction:
    - Allows subjective interpretations
    - Captures questions and uncertainties
    - Tracks evolving thoughts
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a personal knowledge graph analyzer.

Extract concepts and relationships from personal thoughts, reflections, and notes.

Unlike formal theory extraction:
- Capture questions, doubts, speculations
- Track evolving understanding
- Mark subjective interpretations
- Include "wondering about X" as concepts

Return JSON with:
{
  "concepts": [
    {
      "name": "concept name",
      "type": "Concept|Question|Idea|Hypothesis|Note|Observation|Reflection",
      "description": "brief description",
      "confidence": 0.0-1.0,
      "domain": "personal|technical|philosophical|meta",
      "subjective": true|false
    }
  ],
  "relationships": [
    {
      "source": "concept name",
      "target": "concept name",
      "type": "RELATES_TO|QUESTIONS|EXPLORES|BUILDS_ON|CONTRADICTS",
      "strength": 0.0-1.0,
      "reasoning": "brief explanation"
    }
  ]
}

Be inclusive: capture even uncertain thoughts."""
                },
                {
                    "role": "user",
                    "content": f"Extract concepts from this thought:\n\n{text[:2000]}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        result = json.loads(response.choices[0].message.content)
        
        concepts = []
        for item in result.get("concepts", []):
            concepts.append(PrivateConcept(
                name=item.get("name", "Unknown"),
                type=item.get("type", "Concept"),
                description=item.get("description"),
                confidence=item.get("confidence", 0.7),
                domain=item.get("domain", "personal"),
                subjective=item.get("subjective", True)
            ))
        
        semantic_structure = {
            "relationships": result.get("relationships", [])
        }
        
        return concepts, semantic_structure
    
    except Exception as e:
        print(f"⚠️  LLM extraction failed: {e}")
        return [], {"relationships": []}

# ============================================================
# STEP 5: QDRANT INSERTION (PRIVATE COLLECTION)
# ============================================================

def ingest_to_qdrant(client: QdrantClient, chunks: List[PrivateChunk]) -> List[str]:
    """Insert chunks to private Qdrant collection"""
    points = []
    
    for chunk in chunks:
        vector = embed_text(chunk.text)
        
        if len(vector) != EMBED_DIM:
            raise ValueError(f"Embedding dim {len(vector)} != EMBED_DIM {EMBED_DIM}")
        
        point = PointStruct(
            id=chunk.id,
            vector=vector,
            payload={
                "document_id": chunk.document_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "memory_class": chunk.memory_class,  # STM|LONGTERM|DISCARD
                "type": chunk.metadata.get("type", "unknown"),
                "timestamp": chunk.metadata.get("timestamp"),
                "namespace": "private"  # ⚠️ Explicit namespace marker
            }
        )
        points.append(point)
    
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
    
    return [p.id for p in points]

# ============================================================
# STEP 6: NEO4J INSERTION (PRIVATE NAMESPACE)
# ============================================================

def ingest_to_neo4j(
    driver, 
    document: PrivateInput, 
    chunks: List[PrivateChunk], 
    concepts: List[PrivateConcept], 
    semantic_structure: Dict
) -> str:
    """
    Insert to Neo4j using PRIVATE namespace.
    
    Node labels:
    - :PrivateDocument (not :Document)
    - :PrivateChunk (not :Chunk)
    - :PrivateConcept (not :Concept)
    
    This ensures NO CROSSOVER with EFC graph.
    """
    with driver.session() as session:
        tx = None
        try:
            tx = session.begin_transaction()
            
            # 1. Create PrivateDocument node
            result = tx.run("""
                CREATE (d:PrivateDocument {
                    id: $id,
                    type: $type,
                    timestamp: $timestamp,
                    text_length: $text_length
                })
                RETURN elementId(d) AS node_id
            """, 
                id=document.id,
                type=document.type,
                timestamp=document.timestamp,
                text_length=len(document.text)
            )
            doc_node_id = result.single()["node_id"]
            
            # 2. Create PrivateChunk nodes
            for chunk in chunks:
                tx.run("""
                    MATCH (d:PrivateDocument {id: $doc_id})
                    CREATE (c:PrivateChunk {
                        id: $chunk_id,
                        text: $text,
                        chunk_index: $chunk_index,
                        token_count: $token_count,
                        memory_class: $memory_class
                    })
                    CREATE (d)-[:HAS_CHUNK]->(c)
                """,
                    doc_id=document.id,
                    chunk_id=chunk.id,
                    text=chunk.text[:1000],
                    chunk_index=chunk.chunk_index,
                    token_count=chunk.token_count,
                    memory_class=chunk.memory_class
                )
            
            # 3. Create PrivateConcept nodes
            for concept in concepts:
                node_label = f"Private{concept.type}" if concept.type in [
                    "Question", "Idea", "Hypothesis", "Note", "Observation", "Reflection"
                ] else "PrivateConcept"
                
                tx.run(f"""
                    MERGE (c:{node_label} {{name: $name}})
                    ON CREATE SET 
                        c.type = $type,
                        c.description = $description,
                        c.domain = $domain,
                        c.subjective = $subjective,
                        c.created = timestamp()
                    
                    WITH c
                    MATCH (d:PrivateDocument {{id: $doc_id}})-[:HAS_CHUNK]->(chunk:PrivateChunk)
                    WHERE toLower(chunk.text) CONTAINS toLower($name)
                    MERGE (chunk)-[:MENTIONS {{confidence: $confidence}}]->(c)
                """,
                    name=concept.name,
                    type=concept.type,
                    description=concept.description,
                    domain=concept.domain,
                    subjective=concept.subjective,
                    doc_id=document.id,
                    confidence=concept.confidence
                )
            
            # 4. Create private semantic relationships
            relationships = semantic_structure.get("relationships", [])
            for rel in relationships:
                rel_type = rel.get("type", "RELATES_TO")
                source = rel.get("source")
                target = rel.get("target")
                strength = rel.get("strength", 0.7)
                reasoning = rel.get("reasoning", "")
                
                if source and target:
                    try:
                        tx.run(f"""
                            MATCH (source {{name: $source_name}})
                            WHERE any(label IN labels(source) WHERE label STARTS WITH 'Private')
                            MATCH (target {{name: $target_name}})
                            WHERE any(label IN labels(target) WHERE label STARTS WITH 'Private')
                            MERGE (source)-[r:{rel_type}]->(target)
                            ON CREATE SET 
                                r.strength = $strength,
                                r.reasoning = $reasoning,
                                r.created = timestamp()
                        """,
                            source_name=source,
                            target_name=target,
                            strength=strength,
                            reasoning=reasoning
                        )
                    except Exception as e:
                        print(f"     ⚠️  Failed to create {rel_type} relationship: {e}")
            
            tx.commit()
            return doc_node_id
        
        except Exception as e:
            if tx is not None:
                tx.rollback()
            raise Exception(f"Neo4j insertion failed: {e}")

# ============================================================
# ORCHESTRATOR - PRIVATE PIPELINE
# ============================================================

def orchestrate(
    text: str,
    input_type: Literal["chat", "reflection", "note"] = "chat",
    metadata: Dict = None
) -> Dict:
    """
    Private ingestion pipeline.
    
    NO authority filtering - everything is accepted.
    NO GNN training.
    """
    print(f"🧠 Private Orchestrator: {input_type}")
    
    qdrant_client = None
    neo4j_driver = None
    inserted_chunk_ids = []
    
    try:
        # Step 1: Create private input
        doc_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        input_doc = PrivateInput(
            id=doc_id,
            type=input_type,
            timestamp=timestamp,
            text=text,
            metadata=metadata or {}
        )
        
        # Step 2: Preprocess
        print("  📝 Preprocessing...")
        clean_text = preprocess(text, input_type)
        
        # Step 3: Token-based chunking
        print("  ✂️  Chunking by tokens...")
        text_chunks = chunk_text_by_tokens(clean_text)
        print(f"     Generated {len(text_chunks)} chunks")
        
        # Step 4: Create PrivateChunk objects
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk_id = str(uuid.uuid4())
            token_count = len(TOKENIZER.encode(chunk_text))
            
            chunks.append(PrivateChunk(
                id=chunk_id,
                document_id=doc_id,
                text=chunk_text,
                chunk_index=idx,
                token_count=token_count,
                memory_class=None,  # Will be set by memory_classifier later
                metadata={
                    "type": input_type,
                    "timestamp": timestamp,
                    **(metadata or {})
                }
            ))
        
        # Step 5: LLM concept extraction (private version)
        print("  🧠 Extracting concepts...")
        concepts, semantic_structure = extract_concepts_llm(clean_text)
        print(f"     Found {len(concepts)} concepts")
        
        # Step 6: Ingest to Qdrant (private collection)
        print("  📊 Inserting to Qdrant (private)...")
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Ensure private collection exists
        try:
            qdrant_client.get_collection(QDRANT_COLLECTION)
        except:
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
            )
        
        inserted_chunk_ids = ingest_to_qdrant(qdrant_client, chunks)
        print(f"     ✅ {len(inserted_chunk_ids)} chunks in private collection")
        
        # Step 7: Ingest to Neo4j (private namespace)
        print("  🕸️  Inserting to Neo4j (private namespace)...")
        neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        neo4j_node_id = ingest_to_neo4j(neo4j_driver, input_doc, chunks, concepts, semantic_structure)
        print(f"     ✅ Neo4j node: {neo4j_node_id}")
        
        neo4j_driver.close()
        
        print("✅ Private pipeline complete\n")
        
        return {
            "document_id": doc_id,
            "chunk_ids": inserted_chunk_ids,
            "concepts": [c.name for c in concepts],
            "neo4j_node_id": neo4j_node_id,
            "namespace": "private",
            "total_tokens": sum(c.token_count for c in chunks)
        }
    
    except Exception as e:
        # Rollback
        print(f"\n❌ ERROR: {e}")
        print("🔄 Rolling back...")
        
        if inserted_chunk_ids and qdrant_client:
            try:
                qdrant_client.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=PointIdsList(points=inserted_chunk_ids)
                )
                print(f"   ✅ Deleted {len(inserted_chunk_ids)} Qdrant points")
            except Exception as rollback_error:
                print(f"   ⚠️  Rollback failed: {rollback_error}")
        
        raise e
    
    finally:
        if neo4j_driver:
            neo4j_driver.close()

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Private Orchestrator - Personal knowledge pipeline")
    parser.add_argument("--input", required=True, help="Input text or file")
    parser.add_argument("--type", choices=["chat", "reflection", "note"], default="chat")
    
    args = parser.parse_args()
    
    # Read input
    input_path = Path(args.input)
    if input_path.exists():
        text = input_path.read_text()
    else:
        text = args.input
    
    # Run private orchestrator
    try:
        result = orchestrate(
            text=text,
            input_type=args.type
        )
        
        print("\n📋 Result:")
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)
