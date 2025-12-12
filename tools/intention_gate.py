#!/usr/bin/env python3
"""
intention_gate.py (read-only v2 - GNN-enhanced)
================================================

Reads Private knowledge state and produces SUGGESTIONS ONLY.
NO writing. NO promotion. NO steering.

Input:
- :PrivateChunk
- :Feedback
- memory_class
- GNN similarity (NEW)

Computes:
- importance_score (0–1)
- uncertainty_score (0–1)
- conflict (bool)
- risk_level ("low" | "medium" | "high")
- gnn_similarity (0–1) - how similar to stable EFC structure

Outputs:
- "Consider for EFC promotion"
- "Too unstable - wait"
- "High conflict - manual review"

IMPROVEMENTS OVER V1:
1. GNN structural similarity as additional signal
2. GNN reduces risk for chunks resembling stable EFC patterns
3. Low GNN similarity flags for manual review
4. All v1 features preserved (temporal, source, conflict, etc.)
"""

import os
import sys
from statistics import mean, stdev
from datetime import datetime, timedelta
from collections import Counter
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Import GNN scoring module
try:
    from gnn_scoring import add_gnn_signal_to_scores
    GNN_AVAILABLE = True
except ImportError:
    GNN_AVAILABLE = False
    print("[intention_gate] Warning: gnn_scoring not available, running without GNN", file=sys.stderr)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB_PRIVATE = os.getenv("NEO4J_DB_PRIVATE", "private_mem")

POSITIVE = {"good", "correct"}
NEGATIVE = {"bad", "incorrect"}
UNCERTAIN = {"unsure", "neutral"}

# Source weights
SOURCE_WEIGHTS = {
    "manual": 1.0,
    "heuristic": 0.5,
    "llm_agreement": 0.7
}

# Temporal decay (exponential)
DECAY_DAYS = 30  # Half-life for feedback importance

# Consensus requirements
MIN_FEEDBACK_FOR_PROMOTION = 2
MIN_MANUAL_FEEDBACK = 1
MIN_TIME_IN_CLASS_HOURS = 24  # Must be STM for at least 1 day


# ============================================================
# TEMPORAL WEIGHTING
# ============================================================

def temporal_weight(timestamp_ms: int) -> float:
    """
    Calculate weight based on age of feedback.
    Exponential decay: weight = 0.5^(age_days / DECAY_DAYS)
    """
    now = datetime.utcnow().timestamp() * 1000
    age_ms = now - timestamp_ms
    age_days = age_ms / (1000 * 60 * 60 * 24)
    
    if age_days < 0:
        return 1.0  # Future timestamp? Use full weight
    
    return 0.5 ** (age_days / DECAY_DAYS)


# ============================================================
# METRIC CALCULATION
# ============================================================

def calculate_scores(feedback: list, chunk_created_at: int) -> dict:
    """
    Calculate importance, uncertainty, conflict, and risk.
    
    Improvements:
    - Temporal weighting (recent > old)
    - Source weighting (manual > heuristic)
    - Conflict reduces importance
    - Missing feedback = high uncertainty
    - Signal count confidence
    """
    if not feedback:
        return {
            "importance": 0.0,
            "uncertainty": 1.0,
            "conflict": False,
            "risk": "high",
            "confidence": 0.0,
            "signal_count": 0,
            "source_diversity": 0.0,
            "temporal_spread_days": 0,
            "quality_flags": ["no_feedback"]
        }
    
    # Filter out None signals
    feedback = [f for f in feedback if f["signal"]]
    
    if not feedback:
        return {
            "importance": 0.0,
            "uncertainty": 1.0,
            "conflict": False,
            "risk": "high",
            "confidence": 0.0,
            "signal_count": 0,
            "source_diversity": 0.0,
            "temporal_spread_days": 0,
            "quality_flags": ["no_valid_feedback"]
        }
    
    # Classify signals
    positives = [f for f in feedback if f["signal"] in POSITIVE]
    negatives = [f for f in feedback if f["signal"] in NEGATIVE]
    uncertain_signals = [f for f in feedback if f["signal"] in UNCERTAIN]
    
    # Quality metrics
    sources = [f["source"] for f in feedback]
    source_diversity = len(set(sources)) / len(sources)  # Unique sources ratio
    
    timestamps = [f["timestamp"] for f in feedback if f["timestamp"]]
    temporal_spread_days = 0
    if len(timestamps) > 1:
        temporal_spread_days = (max(timestamps) - min(timestamps)) / (1000 * 60 * 60 * 24)
    
    quality_flags = []
    
    # Check for single-session spam
    if len(feedback) > 3 and temporal_spread_days < 0.1:  # All within ~2 hours
        quality_flags.append("temporal_clustering")
    
    # Check for source bias
    if len(feedback) > 2 and source_diversity < 0.4:
        quality_flags.append("low_source_diversity")
    
    # Calculate weighted importance
    weighted_positives = []
    weighted_negatives = []
    weighted_uncertain = []
    
    for f in positives:
        weight = temporal_weight(f["timestamp"]) * SOURCE_WEIGHTS.get(f["source"], 0.5)
        weighted_positives.append(f["strength"] * weight)
    
    for f in negatives:
        weight = temporal_weight(f["timestamp"]) * SOURCE_WEIGHTS.get(f["source"], 0.5)
        weighted_negatives.append(f["strength"] * weight)
    
    for f in uncertain_signals:
        weight = temporal_weight(f["timestamp"]) * SOURCE_WEIGHTS.get(f["source"], 0.5)
        weighted_uncertain.append(f["strength"] * weight)
    
    # Importance: positive signals, reduced by negatives
    positive_score = mean(weighted_positives) if weighted_positives else 0.0
    negative_score = mean(weighted_negatives) if weighted_negatives else 0.0
    
    importance = max(0.0, positive_score - negative_score)
    
    # Uncertainty: high if no feedback, or many uncertain signals, or conflict
    uncertainty_base = mean(weighted_uncertain) if weighted_uncertain else 0.0
    
    # Increase uncertainty if:
    # - Few signals (low confidence)
    # - Conflict exists
    # - Low source diversity
    signal_count = len(feedback)
    confidence = min(1.0, signal_count / 5.0)  # Full confidence at 5+ signals
    
    uncertainty = uncertainty_base
    if signal_count < 3:
        uncertainty = max(uncertainty, 0.5)  # Baseline uncertainty for low signal count
    
    conflict = bool(positives and negatives)
    if conflict:
        uncertainty = max(uncertainty, 0.6)
    
    if source_diversity < 0.5:
        uncertainty = max(uncertainty, 0.4)
    
    uncertainty = min(1.0, uncertainty)  # Cap at 1.0
    
    # Risk assessment
    if conflict and abs(positive_score - negative_score) < 0.2:
        risk = "high"  # Balanced conflict = high risk
    elif uncertainty > 0.7:
        risk = "high"
    elif importance > 0.75 and confidence > 0.6 and not conflict:
        risk = "low"
    else:
        risk = "medium"
    
    return {
        "importance": round(importance, 3),
        "uncertainty": round(uncertainty, 3),
        "conflict": conflict,
        "risk": risk,
        "confidence": round(confidence, 3),
        "signal_count": signal_count,
        "source_diversity": round(source_diversity, 3),
        "temporal_spread_days": round(temporal_spread_days, 2),
        "quality_flags": quality_flags
    }


# ============================================================
# SUGGESTION ENGINE (READ-ONLY)
# ============================================================

def suggest_action(chunk_id: str, memory_class: str, scores: dict, 
                   chunk_created_at: int, manual_feedback_count: int) -> dict:
    """
    Generate structured suggestion based on scores.
    
    Returns dict with:
    - action: "promote" | "wait" | "review" | "demote" | "none"
    - reason: explanation
    - confidence: how confident we are (0-1)
    - metadata: supporting data
    """
    now = datetime.utcnow().timestamp() * 1000
    
    # Handle missing chunk_created_at (fallback to 0 hours)
    if chunk_created_at is None or chunk_created_at == 0:
        time_in_class_hours = 0
    else:
        time_in_class_hours = (now - chunk_created_at) / (1000 * 60 * 60)
    
    # High conflict = manual review required
    if scores["conflict"]:
        return {
            "action": "review",
            "reason": "High conflict - manual review",
            "confidence": 0.9,
            "metadata": {
                "conflict": True,
                "importance": scores["importance"],
                "uncertainty": scores["uncertainty"]
            }
        }
    
    # Quality flags = wait or review
    if scores["quality_flags"]:
        return {
            "action": "wait",
            "reason": f"Quality issues: {', '.join(scores['quality_flags'])}",
            "confidence": 0.7,
            "metadata": {
                "quality_flags": scores["quality_flags"],
                "signal_count": scores["signal_count"]
            }
        }
    
    # Promotion criteria (STM -> LONGTERM or EFC)
    if memory_class == "STM":
        meets_consensus = (
            scores["signal_count"] >= MIN_FEEDBACK_FOR_PROMOTION and
            manual_feedback_count >= MIN_MANUAL_FEEDBACK
        )
        meets_time = time_in_class_hours >= MIN_TIME_IN_CLASS_HOURS
        meets_quality = (
            scores["importance"] > 0.75 and
            scores["confidence"] > 0.6 and
            scores["risk"] == "low"
        )
        
        if meets_consensus and meets_time and meets_quality:
            return {
                "action": "promote",
                "reason": "Consider for LONGTERM promotion",
                "confidence": scores["confidence"],
                "metadata": {
                    "importance": scores["importance"],
                    "signal_count": scores["signal_count"],
                    "manual_feedback": manual_feedback_count,
                    "time_in_class_hours": round(time_in_class_hours, 1)
                }
            }
        
        # Missing time requirement
        if meets_consensus and meets_quality and not meets_time:
            return {
                "action": "wait",
                "reason": f"Too recent - needs {round(MIN_TIME_IN_CLASS_HOURS - time_in_class_hours, 1)} more hours",
                "confidence": 0.8,
                "metadata": {
                    "time_in_class_hours": round(time_in_class_hours, 1),
                    "required_hours": MIN_TIME_IN_CLASS_HOURS
                }
            }
        
        # High risk
        if scores["risk"] == "high":
            return {
                "action": "wait",
                "reason": "Too unstable - wait",
                "confidence": 0.7,
                "metadata": {
                    "risk": scores["risk"],
                    "uncertainty": scores["uncertainty"]
                }
            }
    
    # LONGTERM re-evaluation
    if memory_class == "LONGTERM":
        if scores["risk"] == "high" or scores["uncertainty"] > 0.6:
            return {
                "action": "review",
                "reason": "Re-evaluate stability",
                "confidence": 0.6,
                "metadata": {
                    "risk": scores["risk"],
                    "uncertainty": scores["uncertainty"]
                }
            }
    
    # DISCARD rescue
    if memory_class == "DISCARD":
        if scores["importance"] > 0.6 and scores["confidence"] > 0.5:
            return {
                "action": "review",
                "reason": "Possibly misclassified as DISCARD",
                "confidence": scores["confidence"],
                "metadata": {
                    "importance": scores["importance"],
                    "signal_count": scores["signal_count"]
                }
            }
    
    return {
        "action": "none",
        "reason": "No action needed",
        "confidence": 0.5,
        "metadata": {}
    }


# ============================================================
# DATA ACCESS
# ============================================================

def fetch_chunks_with_feedback(session):
    """Fetch all PrivateChunks with their feedback"""
    result = session.run("""
        MATCH (c:PrivateChunk)
        OPTIONAL MATCH (c)<-[r]-(f:Feedback)
        RETURN 
            c.id AS id,
            c.text AS text,
            c.memory_class AS memory_class,
            c.created_at AS created_at,
            c.class_changed_at AS class_changed_at,
            collect({
                signal: f.signal,
                strength: f.strength,
                source: f.source,
                timestamp: f.timestamp
            }) AS feedback
    """)
    
    chunks = []
    for row in result:
        feedback = [f for f in row["feedback"] if f["signal"] is not None]
        
        # Count manual feedback
        manual_count = sum(1 for f in feedback if f.get("source") == "manual")
        
        chunks.append({
            "id": row["id"],
            "text": row["text"],
            "memory_class": row["memory_class"],
            "created_at": row["created_at"],
            "class_changed_at": row["class_changed_at"] if row["class_changed_at"] else row["created_at"],
            "feedback": feedback,
            "manual_feedback_count": manual_count
        })
    
    return chunks


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="Intention Gate - Read-only analysis")
    parser.add_argument("--chunk-id", help="Analyze specific chunk only")
    parser.add_argument("--action-filter", choices=["promote", "wait", "review", "demote", "none"],
                       help="Show only chunks with specific action")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--test", action="store_true", help="Run with test data instead of database")
    
    args = parser.parse_args()
    
    # Test mode: use mock data
    if args.test:
        print("🧪 Running in test mode with mock data\n")
        
        now = time.time() * 1000
        test_chunks = [
            {
                "id": "test-1",
                "text": "The entropy gradient drives cosmic evolution through energy flow dynamics",
                "memory_class": "transient",
                "created_at": now - (7 * 24 * 60 * 60 * 1000),  # 7 days ago
                "class_changed_at": now - (7 * 24 * 60 * 60 * 1000),
                "feedback": [
                    {"signal": "useful", "strength": 0.9, "source": "manual", "timestamp": now - (6 * 24 * 60 * 60 * 1000)},
                    {"signal": "useful", "strength": 0.8, "source": "manual", "timestamp": now - (5 * 24 * 60 * 60 * 1000)}
                ],
                "manual_feedback_count": 2
            },
            {
                "id": "test-2",
                "text": "I like pizza and my favorite movie is The Matrix",
                "memory_class": "transient",
                "created_at": now - (3 * 24 * 60 * 60 * 1000),  # 3 days ago
                "class_changed_at": now - (3 * 24 * 60 * 60 * 1000),
                "feedback": [
                    {"signal": "useful", "strength": 0.6, "source": "manual", "timestamp": now - (2 * 24 * 60 * 60 * 1000)}
                ],
                "manual_feedback_count": 1
            }
        ]
        
        results = []
        for c in test_chunks:
            scores = calculate_scores(c["feedback"], c["created_at"])
            
            # Enhance with GNN if available
            if GNN_AVAILABLE:
                try:
                    scores = add_gnn_signal_to_scores(
                        chunk_text=c["text"],
                        existing_scores=scores,
                        manual_feedback_count=c["manual_feedback_count"],
                        chunk_domain=None
                    )
                except Exception as e:
                    print(f"[intention_gate] GNN scoring failed: {e}", file=sys.stderr)
            
            suggestion = suggest_action(
                c["id"],
                c["memory_class"],
                scores,
                c["class_changed_at"],
                c["manual_feedback_count"]
            )
            
            result = {
                "chunk_id": c["id"],
                "memory_class": c["memory_class"],
                "text_preview": c["text"][:100],
                "scores": scores,
                "suggestion": suggestion
            }
            results.append(result)
        
        # Print results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"\n{'='*60}")
                print(f"Chunk: {r['chunk_id']}")
                print(f"Class: {r['memory_class']}")
                print(f"Text: {r['text_preview']}")
                print(f"\nScores:")
                for k, v in r['scores'].items():
                    if k != 'quality_flags':
                        print(f"  {k}: {v}")
                if r['scores'].get('quality_flags'):
                    print(f"  flags: {', '.join(r['scores']['quality_flags'])}")
                print(f"\nSuggestion:")
                print(f"  Action: {r['suggestion']['action']}")
                print(f"  Reason: {r['suggestion']['reason']}")
                if r['suggestion'].get('risk_note'):
                    print(f"  Risk: {r['suggestion']['risk_note']}")
        
        sys.exit(0)
    
    # Normal mode: use database
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            chunks = fetch_chunks_with_feedback(session)
            
            if args.chunk_id:
                chunks = [c for c in chunks if c["id"] == args.chunk_id]
            
            if not chunks:
                print("No PrivateChunks found.")
                sys.exit(0)
            
            results = []
            
            for c in chunks:
                scores = calculate_scores(c["feedback"], c["created_at"])
                
                # Enhance with GNN if available
                if GNN_AVAILABLE:
                    try:
                        scores = add_gnn_signal_to_scores(
                            chunk_text=c["text"],
                            existing_scores=scores,
                            manual_feedback_count=c["manual_feedback_count"],
                            chunk_domain=None  # Auto-detect for now
                        )
                    except Exception as e:
                        print(f"[intention_gate] GNN scoring failed: {e}", file=sys.stderr)
                
                suggestion = suggest_action(
                    c["id"],
                    c["memory_class"],
                    scores,
                    c["class_changed_at"],
                    c["manual_feedback_count"]
                )
                
                result = {
                    "chunk_id": c["id"],
                    "memory_class": c["memory_class"],
                    "text_preview": c["text"][:100] if c["text"] else "",
                    "scores": scores,
                    "suggestion": suggestion
                }
                
                # Filter by action if specified
                if args.action_filter and suggestion["action"] != args.action_filter:
                    continue
                
                results.append(result)
            
            # Output
            if args.json:
                import json
                print(json.dumps(results, indent=2))
            else:
                for r in results:
                    print("──────────────────────────────────────────")
                    print(f"Chunk: {r['chunk_id']}")
                    print(f"Text: {r['text_preview']}...")
                    print(f"Memory class: {r['memory_class']}")
                    print(f"Importance: {r['scores']['importance']}")
                    print(f"Uncertainty: {r['scores']['uncertainty']}")
                    print(f"Confidence: {r['scores']['confidence']}")
                    print(f"Conflict: {r['scores']['conflict']}")
                    print(f"Risk: {r['scores']['risk']}")
                    print(f"Signals: {r['scores']['signal_count']}")
                    print(f"Source diversity: {r['scores']['source_diversity']}")
                    print(f"Temporal spread: {r['scores']['temporal_spread_days']} days")
                    
                    # Show GNN scores if available
                    if 'gnn_similarity' in r['scores']:
                        print(f"🧠 GNN Similarity: {r['scores']['gnn_similarity']} (confidence: {r['scores']['gnn_confidence']})")
                        if r['scores'].get('gnn_top_matches'):
                            print(f"   Top EFC matches:")
                            for match in r['scores']['gnn_top_matches'][:3]:
                                print(f"     - {match['concept']} (sim: {match['similarity']:.3f})")
                    
                    if r['scores']['quality_flags']:
                        print(f"⚠️  Quality flags: {', '.join(r['scores']['quality_flags'])}")
                    print()
                    print(f"🎯 Action: {r['suggestion']['action'].upper()}")
                    print(f"   Reason: {r['suggestion']['reason']}")
                    print(f"   Confidence: {r['suggestion']['confidence']}")
                    if r['suggestion']['metadata']:
                        print(f"   Metadata: {r['suggestion']['metadata']}")
                    print()
    
    finally:
        driver.close()
