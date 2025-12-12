#!/usr/bin/env python3
"""
Memory Classifier - STM / LONGTERM / DISCARD Logic
==================================================

Purpose: Classify private chunks into memory categories.

Memory types:
- STM (Short-Term Memory): Temporary, context-dependent
- LONGTERM: Worth keeping, potential EFC promotion
- DISCARD: Noise, no lasting value

This runs AFTER private_orchestrator ingestion.
Later: can be integrated as a step in the pipeline.

Usage:
    python tools/memory_classifier.py --document-id <uuid>
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Literal
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_PRIVATE = os.getenv("NEO4J_DB_PRIVATE", "private_mem")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = "private"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ============================================================
# MEMORY CLASSIFICATION LOGIC
# ============================================================

@dataclass
class ChunkClassification:
    chunk_id: str
    text: str
    memory_class: Literal["STM", "LONGTERM", "DISCARD"]
    confidence: float
    reasoning: str

def classify_chunks_llm(chunks: List[Dict]) -> List[ChunkClassification]:
    """
    Use LLM to classify chunks into memory categories.
    
    Criteria:
    - STM: Temporary thoughts, context-bound, time-sensitive
    - LONGTERM: Reusable insights, stable understanding, worth keeping
    - DISCARD: Filler, noise, redundant
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        classifications = []
        
        for chunk in chunks:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a memory classifier for personal knowledge systems.

Classify text chunks into memory categories:

**STM (Short-Term Memory)**
- Context-dependent thoughts
- Time-sensitive information
- Temporary reflections
- "I wonder if..." without resolution

**LONGTERM (Long-Term Memory)**
- Stable insights
- Reusable understanding
- Core beliefs or principles
- Resolved questions with answers
- Worth reviewing later

**DISCARD**
- Filler text ("hmm", "let me think")
- Pure noise
- Redundant repetition
- No informational value

Return JSON:
{
  "memory_class": "STM|LONGTERM|DISCARD",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}"""
                    },
                    {
                        "role": "user",
                        "content": f"Classify this chunk:\n\n{chunk['text'][:500]}"
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            classifications.append(ChunkClassification(
                chunk_id=chunk['id'],
                text=chunk['text'],
                memory_class=result.get("memory_class", "STM"),
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "")
            ))
        
        return classifications
    
    except Exception as e:
        print(f"❌ LLM classification failed: {e}")
        # Fallback: mark everything as STM
        return [
            ChunkClassification(
                chunk_id=c['id'],
                text=c['text'],
                memory_class="STM",
                confidence=0.5,
                reasoning="Fallback classification"
            )
            for c in chunks
        ]

def classify_chunks_heuristic(chunks: List[Dict]) -> List[ChunkClassification]:
    """
    Heuristic-based classification (fallback when LLM not available).
    
    Rules:
    - Very short chunks (<50 chars): DISCARD
    - Contains question marks without answers: STM
    - Contains definitive statements: LONGTERM
    - Default: STM
    """
    classifications = []
    
    for chunk in chunks:
        text = chunk['text']
        text_len = len(text.strip())
        
        # Very short
        if text_len < 50:
            memory_class = "DISCARD"
            reasoning = "Too short to be meaningful"
            confidence = 0.9
        
        # Just questions
        elif '?' in text and not any(word in text.lower() for word in ['because', 'therefore', 'so', 'answer']):
            memory_class = "STM"
            reasoning = "Unresolved question"
            confidence = 0.7
        
        # Definitive statements
        elif any(marker in text.lower() for marker in ['therefore', 'conclusion', 'principle', 'always', 'fundamental']):
            memory_class = "LONGTERM"
            reasoning = "Contains stable insight"
            confidence = 0.6
        
        # Default
        else:
            memory_class = "STM"
            reasoning = "Default classification"
            confidence = 0.5
        
        classifications.append(ChunkClassification(
            chunk_id=chunk['id'],
            text=text,
            memory_class=memory_class,
            confidence=confidence,
            reasoning=reasoning
        ))
    
    return classifications

# ============================================================
# DATABASE UPDATES
# ============================================================

def update_neo4j_memory_class(driver, classifications: List[ChunkClassification]):
    """Update PrivateChunk nodes with memory_class"""
    with driver.session() as session:
        for c in classifications:
            session.run("""
                MATCH (chunk:PrivateChunk {id: $chunk_id})
                SET chunk.memory_class = $memory_class,
                    chunk.memory_confidence = $confidence,
                    chunk.memory_reasoning = $reasoning,
                    chunk.classified_at = timestamp(),
                    chunk.class_changed_at = timestamp()
            """,
                chunk_id=c.chunk_id,
                memory_class=c.memory_class,
                confidence=c.confidence,
                reasoning=c.reasoning
            )

def update_qdrant_memory_class(client: QdrantClient, classifications: List[ChunkClassification]):
    """Update Qdrant payloads with memory_class"""
    for c in classifications:
        try:
            # Get existing point
            point = client.retrieve(
                collection_name=QDRANT_COLLECTION,
                ids=[c.chunk_id]
            )[0]
            
            # Update payload
            payload = point.payload
            payload['memory_class'] = c.memory_class
            payload['memory_confidence'] = c.confidence
            payload['memory_reasoning'] = c.reasoning
            
            # Upsert with updated payload
            client.set_payload(
                collection_name=QDRANT_COLLECTION,
                payload=payload,
                points=[c.chunk_id]
            )
        except Exception as e:
            print(f"⚠️  Failed to update Qdrant point {c.chunk_id}: {e}")

# ============================================================
# MAIN CLASSIFIER
# ============================================================

def classify_document(document_id: str, use_llm: bool = True):
    """
    Classify all chunks in a private document.
    
    Steps:
    1. Fetch chunks from Neo4j
    2. Classify using LLM or heuristics
    3. Update Neo4j + Qdrant
    """
    print(f"🧠 Memory Classifier: {document_id}")
    
    # Connect to databases
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    try:
        # 1. Fetch chunks
        print("  📥 Fetching chunks...")
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (d:PrivateDocument {id: $doc_id})-[:HAS_CHUNK]->(c:PrivateChunk)
                RETURN c.id AS id, c.text AS text
                ORDER BY c.chunk_index
            """, doc_id=document_id)
            
            chunks = [{"id": r["id"], "text": r["text"]} for r in result]
        
        if not chunks:
            print("  ❌ No chunks found")
            return
        
        print(f"     Found {len(chunks)} chunks")
        
        # 2. Classify
        print("  🔍 Classifying...")
        if use_llm:
            classifications = classify_chunks_llm(chunks)
        else:
            classifications = classify_chunks_heuristic(chunks)
        
        # 3. Update databases
        print("  💾 Updating Neo4j...")
        update_neo4j_memory_class(neo4j_driver, classifications)
        
        print("  💾 Updating Qdrant...")
        update_qdrant_memory_class(qdrant_client, classifications)
        
        # 4. Summary
        summary = {
            "STM": sum(1 for c in classifications if c.memory_class == "STM"),
            "LONGTERM": sum(1 for c in classifications if c.memory_class == "LONGTERM"),
            "DISCARD": sum(1 for c in classifications if c.memory_class == "DISCARD")
        }
        
        print("\n✅ Classification complete:")
        print(f"   STM: {summary['STM']}")
        print(f"   LONGTERM: {summary['LONGTERM']}")
        print(f"   DISCARD: {summary['DISCARD']}")
        
        return classifications
    
    finally:
        neo4j_driver.close()

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Classifier - Classify private chunks")
    parser.add_argument("--document-id", required=True, help="Private document ID")
    parser.add_argument("--no-llm", action="store_true", help="Use heuristic classification instead of LLM")
    
    args = parser.parse_args()
    
    try:
        classifications = classify_document(
            document_id=args.document_id,
            use_llm=not args.no_llm
        )
        
        if classifications:
            print("\n📋 Sample classifications:")
            for c in classifications[:3]:
                print(f"\n{c.memory_class} ({c.confidence:.2f})")
                print(f"  Text: {c.text[:100]}...")
                print(f"  Reason: {c.reasoning}")
    
    except Exception as e:
        print(f"\n❌ Classification failed: {e}")
        sys.exit(1)
