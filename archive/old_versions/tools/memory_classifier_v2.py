#!/usr/bin/env python3
"""
Memory Classifier v2 - Feedback-Aware Reclassification
======================================================

Purpose: Reclassify chunks using BOTH automated signals AND feedback.

Key improvements from v1:
- Reads :Feedback nodes
- Implements consensus logic (anti-bias)
- Only reclassifies when signals agree
- Logs reclassification history

Usage:
    # Reclassify single document
    python tools/memory_classifier_v2.py --document-id <uuid>
    
    # Reclassify all chunks with feedback
    python tools/memory_classifier_v2.py --all-with-feedback
    
    # Dry run (show what would change)
    python tools/memory_classifier_v2.py --document-id <uuid> --dry-run
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Literal, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

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
# CONSENSUS RULES
# ============================================================

# Minimum number of feedback signals required for reclassification
MIN_FEEDBACK_SIGNALS = 2

# Minimum strength for feedback to count
MIN_FEEDBACK_STRENGTH = 0.7

# Required ratio of positive signals for consensus (0.8 = 80% agreement)
CONSENSUS_THRESHOLD = 0.8

# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class FeedbackSignal:
    """Aggregated feedback for a chunk"""
    chunk_id: str
    current_class: str
    feedback_count: int
    positive_count: int  # good, correct
    negative_count: int  # bad, incorrect
    manual_count: int
    suggested_classes: Dict[str, int]  # class → count
    consensus_reached: bool
    consensus_class: Optional[str]
    confidence: float

@dataclass
class ReclassificationDecision:
    """Decision to reclassify a chunk"""
    chunk_id: str
    text: str
    old_class: str
    new_class: str
    confidence: float
    reasoning: str
    feedback_support: int
    manual_support: bool

# ============================================================
# FEEDBACK ANALYSIS
# ============================================================

def analyze_chunk_feedback(driver, chunk_id: str) -> Optional[FeedbackSignal]:
    """
    Analyze all feedback for a chunk and determine if consensus exists.
    
    Returns None if insufficient feedback.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (c:PrivateChunk {id: $chunk_id})
            OPTIONAL MATCH (c)<-[r:EVALUATES|VALIDATES]-(f:Feedback)
            WHERE f.strength >= $min_strength
            RETURN 
                c.memory_class as current_class,
                collect({
                    signal: f.signal,
                    strength: f.strength,
                    source: f.source,
                    suggested_class: CASE 
                        WHEN type(r) = 'VALIDATES' THEN r.suggested_class 
                        ELSE null 
                    END
                }) as feedback_list
        """, 
            chunk_id=chunk_id,
            min_strength=MIN_FEEDBACK_STRENGTH
        )
        
        data = result.single()
        if not data or not data["feedback_list"]:
            return None
        
        current_class = data["current_class"]
        feedback_list = [f for f in data["feedback_list"] if f["signal"] is not None]
        
        if len(feedback_list) < MIN_FEEDBACK_SIGNALS:
            return None
        
        # Count signals
        positive = sum(1 for f in feedback_list if f["signal"] in ["good", "correct"])
        negative = sum(1 for f in feedback_list if f["signal"] in ["bad", "incorrect"])
        manual = sum(1 for f in feedback_list if f["source"] == "manual")
        
        # Count suggested classes
        suggested_classes = {}
        for f in feedback_list:
            if f["suggested_class"]:
                suggested_classes[f["suggested_class"]] = suggested_classes.get(f["suggested_class"], 0) + 1
        
        # Determine consensus
        total_signals = len(feedback_list)
        consensus_reached = False
        consensus_class = None
        confidence = 0.0
        
        # Check if there's a dominant suggested class
        if suggested_classes:
            max_class = max(suggested_classes.items(), key=lambda x: x[1])
            consensus_class = max_class[0]
            confidence = max_class[1] / total_signals
            
            # Consensus reached if:
            # 1. Ratio exceeds threshold
            # 2. At least one manual confirmation
            if confidence >= CONSENSUS_THRESHOLD and manual >= 1:
                consensus_reached = True
        
        # If no explicit suggestions but strong positive/negative signals
        elif positive > 0 or negative > 0:
            # Strong positive signals suggest LONGTERM
            if positive / total_signals >= CONSENSUS_THRESHOLD and manual >= 1:
                if current_class == "STM":
                    consensus_reached = True
                    consensus_class = "LONGTERM"
                    confidence = positive / total_signals
            
            # Strong negative signals suggest DISCARD
            elif negative / total_signals >= CONSENSUS_THRESHOLD and manual >= 1:
                if current_class != "DISCARD":
                    consensus_reached = True
                    consensus_class = "DISCARD"
                    confidence = negative / total_signals
        
        return FeedbackSignal(
            chunk_id=chunk_id,
            current_class=current_class,
            feedback_count=total_signals,
            positive_count=positive,
            negative_count=negative,
            manual_count=manual,
            suggested_classes=suggested_classes,
            consensus_reached=consensus_reached,
            consensus_class=consensus_class,
            confidence=confidence
        )

def get_reclassification_candidates(driver) -> List[FeedbackSignal]:
    """
    Find all chunks with sufficient feedback for potential reclassification.
    """
    with driver.session() as session:
        # Get all chunks with feedback
        result = session.run("""
            MATCH (c:PrivateChunk)<-[:EVALUATES|VALIDATES]-(f:Feedback)
            WHERE f.strength >= $min_strength
            WITH c.id as chunk_id, count(DISTINCT f) as feedback_count
            WHERE feedback_count >= $min_signals
            RETURN chunk_id
            ORDER BY feedback_count DESC
        """,
            min_strength=MIN_FEEDBACK_STRENGTH,
            min_signals=MIN_FEEDBACK_SIGNALS
        )
        
        chunk_ids = [r["chunk_id"] for r in result]
    
    # Analyze each chunk
    candidates = []
    for chunk_id in chunk_ids:
        signal = analyze_chunk_feedback(driver, chunk_id)
        if signal and signal.consensus_reached:
            candidates.append(signal)
    
    return candidates

# ============================================================
# RECLASSIFICATION
# ============================================================

def reclassify_chunk(
    driver, 
    qdrant_client: QdrantClient,
    feedback_signal: FeedbackSignal,
    dry_run: bool = False
) -> ReclassificationDecision:
    """
    Reclassify a chunk based on feedback consensus.
    
    Args:
        driver: Neo4j driver
        qdrant_client: Qdrant client
        feedback_signal: Analyzed feedback
        dry_run: If True, don't actually update databases
    
    Returns:
        Decision object
    """
    with driver.session() as session:
        # Get chunk text
        result = session.run("""
            MATCH (c:PrivateChunk {id: $chunk_id})
            RETURN c.text as text
        """, chunk_id=feedback_signal.chunk_id)
        
        chunk_text = result.single()["text"]
    
    decision = ReclassificationDecision(
        chunk_id=feedback_signal.chunk_id,
        text=chunk_text,
        old_class=feedback_signal.current_class,
        new_class=feedback_signal.consensus_class,
        confidence=feedback_signal.confidence,
        reasoning=f"Consensus from {feedback_signal.feedback_count} signals "
                  f"({feedback_signal.manual_count} manual)",
        feedback_support=feedback_signal.feedback_count,
        manual_support=feedback_signal.manual_count > 0
    )
    
    if not dry_run:
        # Update Neo4j
        with driver.session() as session:
            session.run("""
                MATCH (c:PrivateChunk {id: $chunk_id})
                SET c.memory_class = $new_class,
                    c.reclassified_at = timestamp(),
                    c.reclassification_confidence = $confidence,
                    c.reclassification_reasoning = $reasoning
            """,
                chunk_id=feedback_signal.chunk_id,
                new_class=feedback_signal.consensus_class,
                confidence=feedback_signal.confidence,
                reasoning=decision.reasoning
            )
        
        # Update Qdrant
        try:
            qdrant_client.set_payload(
                collection_name=QDRANT_COLLECTION,
                payload={
                    "memory_class": feedback_signal.consensus_class,
                    "reclassified_at": datetime.utcnow().isoformat()
                },
                points=[feedback_signal.chunk_id]
            )
        except Exception as e:
            print(f"⚠️  Failed to update Qdrant: {e}")
    
    return decision

# ============================================================
# BATCH RECLASSIFICATION
# ============================================================

def reclassify_document(driver, document_id: str, dry_run: bool = False) -> List[ReclassificationDecision]:
    """
    Reclassify all chunks in a document based on feedback.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (d:PrivateDocument {id: $doc_id})-[:HAS_CHUNK]->(c:PrivateChunk)
            RETURN c.id as chunk_id
        """, doc_id=document_id)
        
        chunk_ids = [r["chunk_id"] for r in result]
    
    if not chunk_ids:
        return []
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    decisions = []
    
    for chunk_id in chunk_ids:
        signal = analyze_chunk_feedback(driver, chunk_id)
        if signal and signal.consensus_reached:
            decision = reclassify_chunk(driver, qdrant_client, signal, dry_run)
            decisions.append(decision)
    
    return decisions

def reclassify_all_with_feedback(driver, dry_run: bool = False) -> List[ReclassificationDecision]:
    """
    Reclassify all chunks that have sufficient feedback.
    """
    candidates = get_reclassification_candidates(driver)
    
    if not candidates:
        return []
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    decisions = []
    
    for signal in candidates:
        decision = reclassify_chunk(driver, qdrant_client, signal, dry_run)
        decisions.append(decision)
    
    return decisions

# ============================================================
# REPORTING
# ============================================================

def print_reclassification_report(decisions: List[ReclassificationDecision], dry_run: bool = False):
    """Print summary of reclassification decisions"""
    if not decisions:
        print("  No reclassifications needed")
        return
    
    mode = "DRY RUN - " if dry_run else ""
    print(f"\n{mode}Reclassification Summary:")
    print(f"  Total: {len(decisions)}")
    
    # Count by transition
    transitions = {}
    for d in decisions:
        key = f"{d.old_class} → {d.new_class}"
        transitions[key] = transitions.get(key, 0) + 1
    
    print("\n  Transitions:")
    for trans, count in sorted(transitions.items()):
        print(f"    {trans}: {count}")
    
    print("\n  Details:")
    for d in decisions:
        print(f"\n  📌 {d.chunk_id}")
        print(f"     {d.old_class} → {d.new_class} (confidence: {d.confidence:.2f})")
        print(f"     Text: {d.text[:80]}...")
        print(f"     Reasoning: {d.reasoning}")

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Classifier v2 - Feedback-aware reclassification")
    
    # Target
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--document-id", help="Reclassify chunks in specific document")
    group.add_argument("--all-with-feedback", action="store_true",
                      help="Reclassify all chunks with sufficient feedback")
    
    # Options
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would change without updating databases")
    parser.add_argument("--min-signals", type=int, default=MIN_FEEDBACK_SIGNALS,
                       help=f"Minimum feedback signals required (default: {MIN_FEEDBACK_SIGNALS})")
    parser.add_argument("--consensus-threshold", type=float, default=CONSENSUS_THRESHOLD,
                       help=f"Consensus threshold 0.0-1.0 (default: {CONSENSUS_THRESHOLD})")
    
    args = parser.parse_args()
    
    # Update globals if specified
    if args.min_signals:
        MIN_FEEDBACK_SIGNALS = args.min_signals
    if args.consensus_threshold:
        CONSENSUS_THRESHOLD = args.consensus_threshold
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        print("🧠 Memory Classifier v2 - Feedback-Aware")
        print(f"   Min signals: {MIN_FEEDBACK_SIGNALS}")
        print(f"   Consensus threshold: {CONSENSUS_THRESHOLD}")
        if args.dry_run:
            print("   Mode: DRY RUN (no changes will be made)")
        print()
        
        # Run reclassification
        if args.document_id:
            print(f"  Reclassifying document: {args.document_id}")
            decisions = reclassify_document(driver, args.document_id, args.dry_run)
        else:
            print("  Reclassifying all chunks with feedback...")
            decisions = reclassify_all_with_feedback(driver, args.dry_run)
        
        # Print report
        print_reclassification_report(decisions, args.dry_run)
        
        if decisions and not args.dry_run:
            print(f"\n✅ {len(decisions)} chunks reclassified")
        elif decisions and args.dry_run:
            print(f"\n✅ {len(decisions)} chunks would be reclassified")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        driver.close()
