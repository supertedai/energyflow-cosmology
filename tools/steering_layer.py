#!/usr/bin/env python3
"""
steering_layer.py - Active Memory Management with Safety Gates
==============================================================

Purpose: WRITE-ENABLED layer that promotes, demotes, and manages memory classification
based on intention_gate suggestions and safety rules.

Key principle: Power with restraint.

Safety gates:
1. Consensus requirement (≥2 signals, ≥1 manual)
2. Time-in-class minimum (24h for STM→LONGTERM)
3. Quality threshold (importance > 0.75, confidence > 0.6)
4. Conflict detection (manual review required)
5. Dry-run mode (test before apply)
6. Audit logging (all decisions tracked)

Actions:
- promote: STM → LONGTERM
- demote: LONGTERM → STM (if unstable)
- discard: STM/LONGTERM → DISCARD (if confirmed low value)

Usage:
    # Dry-run mode (no changes)
    python tools/steering_layer.py --dry-run
    
    # Apply promotions only
    python tools/steering_layer.py --action promote
    
    # Apply all eligible actions
    python tools/steering_layer.py --apply-all
    
    # Specific chunk
    python tools/steering_layer.py --chunk-id <uuid> --action promote
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Literal, Optional, Dict, List
from dataclasses import dataclass, asdict

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

AUDIT_LOG = Path("symbiose_gnn_output/steering_audit.jsonl")

# Safety thresholds (match intention_gate)
MIN_FEEDBACK_SIGNALS = 2
MIN_MANUAL_FEEDBACK = 1
MIN_TIME_IN_CLASS_HOURS = 24
MIN_IMPORTANCE = 0.75
MIN_CONFIDENCE = 0.6

# Safety cap for batch operations
MAX_ACTIONS_PER_RUN = 10

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class SteeringDecision:
    """Record of a steering action"""
    decision_id: str
    timestamp: str
    chunk_id: str
    action: str  # promote, demote, discard, flag_efc
    from_class: str
    to_class: str
    reason: str
    
    # Supporting evidence
    importance: float
    uncertainty: float
    confidence: float
    conflict: bool
    risk: str
    
    feedback_count: int
    manual_feedback_count: int
    time_in_class_hours: float
    
    # Execution
    dry_run: bool
    applied: bool
    error: Optional[str] = None

# ============================================================
# INTENTION INTEGRATION
# ============================================================

def get_intention_analysis(driver) -> List[Dict]:
    """
    Get intention_gate analysis for all chunks.
    Uses intention_gate module.
    """
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from intention_gate import (
            fetch_chunks_with_feedback,
            calculate_scores,
            suggest_action
        )
        
        with driver.session() as session:
            chunks = fetch_chunks_with_feedback(session)
        
        results = []
        for chunk in chunks:
            scores = calculate_scores(chunk["feedback"], chunk["created_at"])
            suggestion = suggest_action(
                chunk["id"],
                chunk["memory_class"],
                scores,
                chunk["class_changed_at"],
                chunk["manual_feedback_count"]
            )
            
            results.append({
                "chunk_id": chunk["id"],
                "memory_class": chunk["memory_class"],
                "created_at": chunk["created_at"],
                "class_changed_at": chunk.get("class_changed_at", chunk["created_at"]),  # Fallback to created_at
                "scores": scores,
                "suggestion": suggestion,
                "feedback_count": len(chunk["feedback"]),
                "manual_feedback_count": chunk["manual_feedback_count"]
            })
        
        return results
    
    except ImportError as e:
        print(f"❌ Could not import intention_gate: {e}")
        sys.exit(1)

# ============================================================
# SAFETY VALIDATION
# ============================================================

def validate_promotion(analysis: Dict) -> tuple[bool, str]:
    """
    Validate promotion STM → LONGTERM meets all safety criteria.
    
    Returns: (is_valid, reason)
    """
    scores = analysis["scores"]
    suggestion = analysis["suggestion"]
    
    # Must be suggested by intention gate
    if suggestion["action"] != "promote":
        return False, f"Intention gate suggests: {suggestion['action']}"
    
    # Consensus requirement
    if analysis["feedback_count"] < MIN_FEEDBACK_SIGNALS:
        return False, f"Insufficient feedback ({analysis['feedback_count']} < {MIN_FEEDBACK_SIGNALS})"
    
    if analysis["manual_feedback_count"] < MIN_MANUAL_FEEDBACK:
        return False, f"No manual feedback ({analysis['manual_feedback_count']} < {MIN_MANUAL_FEEDBACK})"
    
    # Quality threshold
    if scores["importance"] < MIN_IMPORTANCE:
        return False, f"Low importance ({scores['importance']} < {MIN_IMPORTANCE})"
    
    # Validate confidence exists and meets threshold
    if "confidence" not in scores:
        return False, "Missing confidence score from intention_gate"
    
    if scores["confidence"] < MIN_CONFIDENCE:
        return False, f"Low confidence ({scores['confidence']} < {MIN_CONFIDENCE})"
    
    # Time requirement - use class_changed_at if available, fallback to created_at
    now = datetime.utcnow().timestamp() * 1000
    class_timestamp = analysis.get("class_changed_at", analysis["created_at"])
    time_in_class_hours = (now - class_timestamp) / (1000 * 60 * 60)
    
    if time_in_class_hours < MIN_TIME_IN_CLASS_HOURS:
        return False, f"Too recent ({time_in_class_hours:.1f}h < {MIN_TIME_IN_CLASS_HOURS}h)"
    
    # Conflict check
    if scores["conflict"]:
        return False, "Conflict detected - requires manual review"
    
    # Risk check
    if scores["risk"] == "high":
        return False, "High risk - requires manual review"
    
    return True, "All safety criteria met"

def validate_demotion(analysis: Dict) -> tuple[bool, str]:
    """
    Validate demotion LONGTERM → STM.
    
    More lenient than promotion - allows unstable LONGTERM to return to STM.
    """
    scores = analysis["scores"]
    suggestion = analysis["suggestion"]
    
    # Must be LONGTERM
    if analysis["memory_class"] != "LONGTERM":
        return False, "Not LONGTERM"
    
    # Must be suggested by intention gate
    if suggestion["action"] not in ["review", "wait"]:
        return False, f"Intention gate suggests: {suggestion['action']}"
    
    # High uncertainty or risk
    if scores["uncertainty"] > 0.6 or scores["risk"] == "high":
        return True, f"Unstable LONGTERM (uncertainty: {scores['uncertainty']}, risk: {scores['risk']})"
    
    return False, "Still stable"

def validate_discard(analysis: Dict) -> tuple[bool, str]:
    """
    Validate DISCARD classification.
    
    Very strict - requires explicit negative feedback.
    """
    scores = analysis["scores"]
    
    # Conflict blocks discard - never discard during disagreement
    if scores["conflict"]:
        return False, "Conflict present - discard blocked"
    
    # Requires negative feedback
    if analysis["feedback_count"] < 2:
        return False, "Insufficient feedback for discard"
    
    # Must have low importance and explicit negative signals
    if scores["importance"] > 0.2:
        return False, f"Too high importance ({scores['importance']})"
    
    # Requires manual confirmation
    if analysis["manual_feedback_count"] < 1:
        return False, "No manual confirmation for discard"
    
    return True, "Confirmed low value"

# ============================================================
# STEERING ACTIONS
# ============================================================

def apply_promotion(driver, qdrant_client, chunk_id: str, analysis: Dict, dry_run: bool) -> SteeringDecision:
    """
    Promote chunk STM → LONGTERM.
    
    Updates both Neo4j and Qdrant.
    """
    scores = analysis["scores"]
    now = datetime.utcnow().timestamp() * 1000
    time_in_class = (now - analysis["created_at"]) / (1000 * 60 * 60)
    
    decision = SteeringDecision(
        decision_id=f"steer-{chunk_id[:8]}-{int(now)}",
        timestamp=datetime.utcnow().isoformat(),
        chunk_id=chunk_id,
        action="promote",
        from_class="STM",
        to_class="LONGTERM",
        reason=analysis["suggestion"]["reason"],
        importance=scores["importance"],
        uncertainty=scores["uncertainty"],
        confidence=scores["confidence"],
        conflict=scores["conflict"],
        risk=scores["risk"],
        feedback_count=analysis["feedback_count"],
        manual_feedback_count=analysis["manual_feedback_count"],
        time_in_class_hours=round(time_in_class, 1),
        dry_run=dry_run,
        applied=False
    )
    
    if dry_run:
        print(f"  [DRY-RUN] Would promote {chunk_id} → LONGTERM")
        log_decision(decision)
        return decision
    
    try:
        # Update Neo4j
        with driver.session() as session:
            session.run("""
                MATCH (c:PrivateChunk {id: $chunk_id})
                SET c.memory_class = 'LONGTERM',
                    c.promoted_at = $timestamp,
                    c.promotion_reason = $reason,
                    c.class_changed_at = $timestamp
            """, chunk_id=chunk_id, timestamp=int(now), reason=decision.reason)
        
        # Update Qdrant
        qdrant_client.set_payload(
            collection_name="private",
            points=[chunk_id],
            payload={"memory_class": "LONGTERM"}
        )
        
        decision.applied = True
        print(f"  ✅ Promoted {chunk_id} → LONGTERM")
        log_decision(decision)
        return decision
    
    except Exception as e:
        decision.error = str(e)
        print(f"  ❌ Failed to promote {chunk_id}: {e}")
        log_decision(decision)
        return decision

def apply_demotion(driver, qdrant_client, chunk_id: str, analysis: Dict, dry_run: bool) -> SteeringDecision:
    """
    Demote chunk LONGTERM → STM.
    """
    scores = analysis["scores"]
    now = datetime.utcnow().timestamp() * 1000
    time_in_class = (now - analysis["created_at"]) / (1000 * 60 * 60)
    
    decision = SteeringDecision(
        decision_id=f"steer-{chunk_id[:8]}-{int(now)}",
        timestamp=datetime.utcnow().isoformat(),
        chunk_id=chunk_id,
        action="demote",
        from_class="LONGTERM",
        to_class="STM",
        reason=analysis["suggestion"]["reason"],
        importance=scores["importance"],
        uncertainty=scores["uncertainty"],
        confidence=scores["confidence"],
        conflict=scores["conflict"],
        risk=scores["risk"],
        feedback_count=analysis["feedback_count"],
        manual_feedback_count=analysis["manual_feedback_count"],
        time_in_class_hours=round(time_in_class, 1),
        dry_run=dry_run,
        applied=False
    )
    
    if dry_run:
        print(f"  [DRY-RUN] Would demote {chunk_id} → STM")
        log_decision(decision)
        return decision
    
    try:
        # Update Neo4j
        with driver.session() as session:
            session.run("""
                MATCH (c:PrivateChunk {id: $chunk_id})
                SET c.memory_class = 'STM',
                    c.demoted_at = $timestamp,
                    c.demotion_reason = $reason,
                    c.class_changed_at = $timestamp
            """, chunk_id=chunk_id, timestamp=int(now), reason=decision.reason)
        
        # Update Qdrant
        qdrant_client.set_payload(
            collection_name="private",
            points=[chunk_id],
            payload={"memory_class": "STM"}
        )
        
        decision.applied = True
        print(f"  ✅ Demoted {chunk_id} → STM")
        log_decision(decision)
        return decision
    
    except Exception as e:
        decision.error = str(e)
        print(f"  ❌ Failed to demote {chunk_id}: {e}")
        log_decision(decision)
        return decision

def apply_discard(driver, qdrant_client, chunk_id: str, analysis: Dict, dry_run: bool) -> SteeringDecision:
    """
    Mark chunk as DISCARD.
    
    Does NOT delete - only marks for later cleanup.
    """
    scores = analysis["scores"]
    now = datetime.utcnow().timestamp() * 1000
    time_in_class = (now - analysis["created_at"]) / (1000 * 60 * 60)
    
    decision = SteeringDecision(
        decision_id=f"steer-{chunk_id[:8]}-{int(now)}",
        timestamp=datetime.utcnow().isoformat(),
        chunk_id=chunk_id,
        action="discard",
        from_class=analysis["memory_class"],
        to_class="DISCARD",
        reason="Confirmed low value",
        importance=scores["importance"],
        uncertainty=scores["uncertainty"],
        confidence=scores["confidence"],
        conflict=scores["conflict"],
        risk=scores["risk"],
        feedback_count=analysis["feedback_count"],
        manual_feedback_count=analysis["manual_feedback_count"],
        time_in_class_hours=round(time_in_class, 1),
        dry_run=dry_run,
        applied=False
    )
    
    if dry_run:
        print(f"  [DRY-RUN] Would mark {chunk_id} → DISCARD")
        log_decision(decision)
        return decision
    
    try:
        # Update Neo4j
        with driver.session() as session:
            session.run("""
                MATCH (c:PrivateChunk {id: $chunk_id})
                SET c.memory_class = 'DISCARD',
                    c.discarded_at = $timestamp,
                    c.class_changed_at = $timestamp
            """, chunk_id=chunk_id, timestamp=int(now))
        
        # Update Qdrant
        qdrant_client.set_payload(
            collection_name="private",
            points=[chunk_id],
            payload={"memory_class": "DISCARD"}
        )
        
        decision.applied = True
        print(f"  ✅ Marked {chunk_id} → DISCARD")
        log_decision(decision)
        return decision
    
    except Exception as e:
        decision.error = str(e)
        print(f"  ❌ Failed to discard {chunk_id}: {e}")
        log_decision(decision)
        return decision

# ============================================================
# AUDIT LOGGING
# ============================================================

def log_decision(decision: SteeringDecision):
    """Append decision to audit log"""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    with open(AUDIT_LOG, 'a') as f:
        f.write(json.dumps(asdict(decision)) + '\n')

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Steering Layer - Active memory management")
    
    parser.add_argument("--dry-run", action="store_true",
                       help="Test mode - no actual changes")
    parser.add_argument("--chunk-id", help="Apply to specific chunk only")
    parser.add_argument("--action", choices=["promote", "demote", "discard"],
                       help="Apply specific action only")
    parser.add_argument("--apply-all", action="store_true",
                       help="Apply all eligible actions (USE WITH CAUTION)")
    
    args = parser.parse_args()
    
    # Safety check
    if args.apply_all and not args.dry_run:
        confirm = input("⚠️  Apply all actions WITHOUT dry-run? Type 'yes' to confirm: ")
        if confirm != "yes":
            print("❌ Aborted")
            sys.exit(0)
    
    # Connect to Neo4j and Qdrant
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    try:
        print("🎯 Fetching intention analysis...")
        analyses = get_intention_analysis(driver)
        
        if args.chunk_id:
            analyses = [a for a in analyses if a["chunk_id"] == args.chunk_id]
        
        if not analyses:
            print("  No chunks to process")
            sys.exit(0)
        
        print(f"   Found {len(analyses)} chunks")
        
        # Process each chunk
        decisions = []
        action_count = 0
        
        for analysis in analyses:
            # Safety cap - stop after MAX_ACTIONS_PER_RUN
            if action_count >= MAX_ACTIONS_PER_RUN:
                print(f"\n⚠️  Reached safety cap ({MAX_ACTIONS_PER_RUN} actions)")
                print(f"   Stopping to prevent runaway execution")
                break
            chunk_id = analysis["chunk_id"]
            memory_class = analysis["memory_class"]
            
            # Determine eligible actions
            eligible_actions = []
            
            # Check promotion
            if memory_class == "STM" and (not args.action or args.action == "promote"):
                is_valid, reason = validate_promotion(analysis)
                if is_valid:
                    eligible_actions.append("promote")
            
            # Check demotion
            if memory_class == "LONGTERM" and (not args.action or args.action == "demote"):
                is_valid, reason = validate_demotion(analysis)
                if is_valid:
                    eligible_actions.append("demote")
            
            # Check discard
            if memory_class in ["STM", "LONGTERM"] and (not args.action or args.action == "discard"):
                is_valid, reason = validate_discard(analysis)
                if is_valid:
                    eligible_actions.append("discard")
            
            # Apply actions
            if eligible_actions:
                print(f"\n📌 Chunk: {chunk_id} ({memory_class})")
                print(f"   Eligible actions: {', '.join(eligible_actions)}")
                
                for action in eligible_actions:
                    if args.apply_all or args.chunk_id:
                        if action == "promote":
                            decision = apply_promotion(driver, qdrant_client, chunk_id, analysis, args.dry_run)
                            decisions.append(decision)
                            action_count += 1
                        elif action == "demote":
                            decision = apply_demotion(driver, qdrant_client, chunk_id, analysis, args.dry_run)
                            decisions.append(decision)
                            action_count += 1
                        elif action == "discard":
                            decision = apply_discard(driver, qdrant_client, chunk_id, analysis, args.dry_run)
                            decisions.append(decision)
                            action_count += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Steering Summary:")
        print(f"   Total chunks processed: {len(analyses)}")
        print(f"   Decisions made: {len(decisions)}")
        
        if decisions:
            applied = sum(1 for d in decisions if d.applied)
            failed = sum(1 for d in decisions if d.error)
            
            print(f"   Applied: {applied}")
            print(f"   Failed: {failed}")
            
            by_action = {}
            for d in decisions:
                by_action[d.action] = by_action.get(d.action, 0) + 1
            
            print(f"\n   By action:")
            for action, count in by_action.items():
                print(f"     {action}: {count}")
        
        if args.dry_run:
            print(f"\n⚠️  DRY-RUN mode - no changes applied")
            print(f"   Remove --dry-run to apply changes")
        
        print(f"\n✅ Audit log: {AUDIT_LOG}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        driver.close()
