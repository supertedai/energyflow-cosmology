#!/usr/bin/env python3
"""
Feedback Listener - Log Human Feedback on Private Knowledge
===========================================================

Purpose: Create feedback signals for chunks, concepts, and classifications.

This is the CONTROL LAYER between structure and learning.
Feedback enables:
- Quality validation
- Memory classification refinement
- Training signal for bias control
- Temporal tracking of evolving understanding

Usage:
    # Feedback on chunk classification
    python tools/feedback_listener.py \
      --chunk-id <uuid> \
      --signal correct \
      --context "This is definitely long-term"
    
    # Feedback on concept extraction
    python tools/feedback_listener.py \
      --concept-name "Entropy" \
      --signal incorrect \
      --context "Wrong domain interpretation"
    
    # General quality feedback
    python tools/feedback_listener.py \
      --chunk-id <uuid> \
      --signal good \
      --strength 0.9
"""

import os
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_PRIVATE = os.getenv("NEO4J_DB_PRIVATE", "private_mem")

FEEDBACK_BUFFER = Path("symbiose_gnn_output/feedback_buffer.jsonl")

# ============================================================
# FEEDBACK TYPES
# ============================================================

VALID_SIGNALS = {
    "correct", "incorrect",  # Factual correctness
    "good", "bad",           # Quality/relevance
    "unsure", "neutral"      # Uncertainty
}

VALID_ASPECTS = {
    "classification",  # Memory class (STM/LONGTERM/DISCARD)
    "content",        # Text content quality
    "relevance",      # Usefulness
    "extraction",     # Concept extraction accuracy
    "accuracy"        # Factual accuracy
}

# ============================================================
# CORE FEEDBACK FUNCTIONS
# ============================================================

def create_feedback(
    signal: Literal["correct", "incorrect", "good", "bad", "unsure", "neutral"],
    strength: float = 1.0,
    context: Optional[str] = None,
    session_id: Optional[str] = None,
    source: str = "manual"
) -> dict:
    """
    Create a feedback node structure.
    
    Args:
        signal: Feedback type
        strength: Confidence (0.0-1.0)
        context: Optional explanation
        session_id: Optional session grouping
        source: "manual" | "heuristic" | "llm_agreement"
    
    Returns:
        Feedback dict with id and timestamp
    """
    if signal not in VALID_SIGNALS:
        raise ValueError(f"Invalid signal: {signal}. Must be one of {VALID_SIGNALS}")
    
    if not 0.0 <= strength <= 1.0:
        raise ValueError(f"Strength must be 0.0-1.0, got {strength}")
    
    return {
        "id": str(uuid.uuid4()),
        "timestamp": int(datetime.utcnow().timestamp() * 1000),  # milliseconds
        "signal": signal,
        "strength": strength,
        "context": context,
        "session_id": session_id,
        "source": source,
        "created_at": datetime.utcnow().isoformat()
    }

def log_chunk_feedback(
    driver,
    chunk_id: str,
    signal: str,
    aspect: str = "relevance",
    strength: float = 1.0,
    context: Optional[str] = None,
    suggested_class: Optional[str] = None
) -> str:
    """
    Log feedback on a PrivateChunk.
    
    Args:
        chunk_id: Target chunk UUID
        signal: Feedback signal
        aspect: What aspect being evaluated
        strength: Confidence
        context: Optional explanation
        suggested_class: If correcting classification, what it should be
    
    Returns:
        Feedback node ID
    """
    if aspect not in VALID_ASPECTS:
        raise ValueError(f"Invalid aspect: {aspect}. Must be one of {VALID_ASPECTS}")
    
    feedback = create_feedback(signal, strength, context)
    
    with driver.session() as session:
        # Check if chunk exists
        result = session.run("""
            MATCH (c:PrivateChunk {id: $chunk_id})
            RETURN c.id, c.memory_class
        """, chunk_id=chunk_id)
        
        chunk_data = result.single()
        if not chunk_data:
            raise ValueError(f"PrivateChunk {chunk_id} not found")
        
        original_class = chunk_data["c.memory_class"]
        
        # Create feedback node and relationship
        if suggested_class and aspect == "classification":
            # Classification correction
            session.run("""
                CREATE (f:Feedback {
                    id: $id,
                    timestamp: $timestamp,
                    signal: $signal,
                    strength: $strength,
                    context: $context,
                    session_id: $session_id,
                    source: $source,
                    created_at: $created_at
                })
                
                WITH f
                MATCH (c:PrivateChunk {id: $chunk_id})
                CREATE (f)-[:VALIDATES {
                    aspect: $aspect,
                    original_class: $original_class,
                    suggested_class: $suggested_class
                }]->(c)
                
                RETURN f.id as feedback_id
            """,
                chunk_id=chunk_id,
                aspect=aspect,
                original_class=original_class,
                suggested_class=suggested_class,
                **feedback
            )
        else:
            # General evaluation
            session.run("""
                CREATE (f:Feedback {
                    id: $id,
                    timestamp: $timestamp,
                    signal: $signal,
                    strength: $strength,
                    context: $context,
                    session_id: $session_id,
                    source: $source,
                    created_at: $created_at
                })
                
                WITH f
                MATCH (c:PrivateChunk {id: $chunk_id})
                CREATE (f)-[:EVALUATES {
                    aspect: $aspect
                }]->(c)
                
                RETURN f.id as feedback_id
            """,
                chunk_id=chunk_id,
                aspect=aspect,
                **feedback
            )
    
    # Log to JSON buffer
    log_to_buffer({
        **feedback,
        "target_type": "chunk",
        "target_id": chunk_id,
        "aspect": aspect,
        "original_class": original_class if suggested_class else None,
        "suggested_class": suggested_class
    })
    
    return feedback["id"]

def log_concept_feedback(
    driver,
    concept_name: str,
    signal: str,
    aspect: str = "accuracy",
    strength: float = 1.0,
    context: Optional[str] = None
) -> str:
    """
    Log feedback on a PrivateConcept.
    
    Args:
        concept_name: Target concept name
        signal: Feedback signal
        aspect: What aspect being evaluated
        strength: Confidence
        context: Optional explanation
    
    Returns:
        Feedback node ID
    """
    if aspect not in VALID_ASPECTS:
        raise ValueError(f"Invalid aspect: {aspect}. Must be one of {VALID_ASPECTS}")
    
    feedback = create_feedback(signal, strength, context)
    
    with driver.session() as session:
        # Check if concept exists
        result = session.run("""
            MATCH (c:PrivateConcept {name: $concept_name})
            RETURN c.name
        """, concept_name=concept_name)
        
        if not result.single():
            raise ValueError(f"PrivateConcept '{concept_name}' not found")
        
        # Create feedback
        session.run("""
            CREATE (f:Feedback {
                id: $id,
                timestamp: $timestamp,
                signal: $signal,
                strength: $strength,
                context: $context,
                session_id: $session_id,
                source: $source,
                created_at: $created_at
            })
            
            WITH f
            MATCH (c:PrivateConcept {name: $concept_name})
            CREATE (f)-[:EVALUATES {
                aspect: $aspect
            }]->(c)
            
            RETURN f.id as feedback_id
        """,
            concept_name=concept_name,
            aspect=aspect,
            **feedback
        )
    
    # Log to JSON buffer
    log_to_buffer({
        **feedback,
        "target_type": "concept",
        "target_id": concept_name,
        "aspect": aspect
    })
    
    return feedback["id"]

def log_to_buffer(feedback_data: dict):
    """Append feedback to JSON buffer for offline analysis"""
    FEEDBACK_BUFFER.parent.mkdir(parents=True, exist_ok=True)
    
    with open(FEEDBACK_BUFFER, 'a') as f:
        f.write(json.dumps(feedback_data) + '\n')

# ============================================================
# QUERY FUNCTIONS
# ============================================================

def get_chunk_feedback(driver, chunk_id: str) -> List[dict]:
    """Get all feedback for a chunk"""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:PrivateChunk {id: $chunk_id})<-[r]-(f:Feedback)
            RETURN f.signal, f.strength, f.context, f.timestamp, 
                   type(r) as rel_type, properties(r) as rel_props
            ORDER BY f.timestamp DESC
        """, chunk_id=chunk_id)
        
        return [dict(r) for r in result]

def get_concept_feedback(driver, concept_name: str) -> List[dict]:
    """Get all feedback for a concept"""
    with driver.session() as session:
        result = session.run("""
            MATCH (c:PrivateConcept {name: $concept_name})<-[r]-(f:Feedback)
            RETURN f.signal, f.strength, f.context, f.timestamp,
                   type(r) as rel_type, properties(r) as rel_props
            ORDER BY f.timestamp DESC
        """, concept_name=concept_name)
        
        return [dict(r) for r in result]

def get_consensus_candidates(driver, min_positive: int = 2) -> list:
    """
    Find chunks with sufficient positive feedback for LONGTERM promotion.
    
    Implements anti-bias rule: requires multiple positive signals.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (c:PrivateChunk {memory_class: "STM"})<-[:EVALUATES]-(f:Feedback)
            WHERE f.signal IN ["good", "correct"]
              AND f.strength >= 0.7
            WITH c, 
                 count(f) as positive_count,
                 collect(DISTINCT f.source) as sources,
                 collect(f.signal) as signals
            WHERE positive_count >= $min_positive
              AND size([s IN sources WHERE s = "manual"]) >= 1
            RETURN c.id, c.text, positive_count, sources, signals
            ORDER BY positive_count DESC
        """, min_positive=min_positive)
        
        return [dict(r) for r in result]

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Feedback Listener - Log feedback on private knowledge")
    
    # Target
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chunk-id", help="Target PrivateChunk UUID")
    group.add_argument("--concept-name", help="Target PrivateConcept name")
    
    # Feedback
    parser.add_argument("--signal", required=True, choices=list(VALID_SIGNALS),
                       help="Feedback signal")
    parser.add_argument("--aspect", choices=list(VALID_ASPECTS), default="relevance",
                       help="Aspect being evaluated")
    parser.add_argument("--strength", type=float, default=1.0,
                       help="Confidence (0.0-1.0)")
    parser.add_argument("--context", help="Optional explanation")
    parser.add_argument("--suggested-class", choices=["STM", "LONGTERM", "DISCARD"],
                       help="If correcting classification, what it should be")
    
    # Query mode
    parser.add_argument("--query", action="store_true",
                       help="Query existing feedback instead of creating new")
    parser.add_argument("--show-candidates", action="store_true",
                       help="Show chunks ready for LONGTERM promotion")
    
    args = parser.parse_args()
    
    # Validation: suggested-class requires classification aspect
    if args.suggested_class and args.aspect != "classification":
        parser.error("--suggested-class requires --aspect classification")
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Query modes
        if args.show_candidates:
            print("🔍 Chunks with consensus for LONGTERM promotion:\n")
            candidates = get_consensus_candidates(driver)
            
            if not candidates:
                print("  No candidates found (need ≥2 positive signals with ≥1 manual)")
            else:
                for c in candidates:
                    print(f"  📌 {c['id']}")
                    print(f"     Text: {c['text'][:100]}...")
                    print(f"     Signals: {c['positive_count']} positive ({c['sources']})")
                    print()
        
        elif args.query:
            if args.chunk_id:
                print(f"📋 Feedback for chunk {args.chunk_id}:\n")
                feedback = get_chunk_feedback(driver, args.chunk_id)
            else:
                print(f"📋 Feedback for concept '{args.concept_name}':\n")
                feedback = get_concept_feedback(driver, args.concept_name)
            
            if not feedback:
                print("  No feedback found")
            else:
                for f in feedback:
                    print(f"  {f['signal']} (strength: {f['strength']})")
                    if f['context']:
                        print(f"    Context: {f['context']}")
                    print(f"    Aspect: {f['rel_props'].get('aspect', 'N/A')}")
                    print()
        
        # Create mode
        else:
            if args.chunk_id:
                print(f"💬 Creating feedback for chunk {args.chunk_id}...")
                feedback_id = log_chunk_feedback(
                    driver,
                    chunk_id=args.chunk_id,
                    signal=args.signal,
                    aspect=args.aspect,
                    strength=args.strength,
                    context=args.context,
                    suggested_class=args.suggested_class
                )
            else:
                print(f"💬 Creating feedback for concept '{args.concept_name}'...")
                feedback_id = log_concept_feedback(
                    driver,
                    concept_name=args.concept_name,
                    signal=args.signal,
                    aspect=args.aspect,
                    strength=args.strength,
                    context=args.context
                )
            
            print(f"✅ Feedback created: {feedback_id}")
            print(f"   Signal: {args.signal}")
            print(f"   Aspect: {args.aspect}")
            print(f"   Strength: {args.strength}")
            if args.context:
                print(f"   Context: {args.context}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    finally:
        driver.close()
