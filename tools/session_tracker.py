#!/usr/bin/env python3
"""
Session Tracker - LAG 1: CAPTURE
================================

Tracks session state, domain drift, and turn metrics.

Functions:
- get_session_state(session_id) → Current session metrics
- get_previous_domain(session_id) → Last domain visited
- calculate_hop_distance(prev_domain, curr_domain) → Distance between domains
- calculate_field_entropy(session_id) → Session domain scatter
- get_turn_count(session_id) → Total turns in session
- update_session_state(session_id, turn_data) → Save turn metrics
"""

import os
import sys
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv()

# Qdrant client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Domain embeddings for distance calculation (simplified - could use actual embeddings)
DOMAIN_EMBEDDINGS = {
    "personal": [1.0, 0.0, 0.0, 0.0, 0.0],
    "cosmology": [0.0, 1.0, 0.0, 0.0, 0.0],
    "thermo_energy": [0.0, 0.9, 0.1, 0.0, 0.0],
    "ai_symbiosis": [0.0, 0.0, 1.0, 0.0, 0.0],
    "meta": [0.0, 0.0, 0.0, 1.0, 0.0],
    "philosophy": [0.0, 0.0, 0.0, 0.9, 0.1],
    "mathematics": [0.0, 0.5, 0.0, 0.0, 0.5],
    "coding": [0.0, 0.0, 0.5, 0.0, 0.5],
    "general": [0.2, 0.2, 0.2, 0.2, 0.2],
}


def cosine_distance(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine distance between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 1.0  # Max distance if zero vector
    
    similarity = dot_product / (norm_v1 * norm_v2)
    distance = 1.0 - similarity
    
    return distance


def get_session_turns(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all turns for a session from Qdrant."""
    try:
        # Filter by session_id only (memory_class filter requires index)
        results = client.scroll(
            collection_name="efc",
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )
        
        turns = []
        for point in results[0]:
            if point.payload:
                # Only include SESSION_TURN entries
                if point.payload.get("memory_class") == "SESSION_TURN":
                    turns.append(point.payload)
        
        # Sort by timestamp
        turns.sort(key=lambda x: x.get("timestamp", ""))
        
        return turns
        
    except Exception as e:
        # Silent fail for MCP compatibility - log to file if needed
        pass
        return []


def get_previous_domain(session_id: str) -> Optional[str]:
    """Get the last domain visited in this session."""
    turns = get_session_turns(session_id, limit=10)
    
    if not turns:
        return None
    
    # Get most recent turn with domain
    for turn in reversed(turns):
        domain = turn.get("domain")
        if domain:
            return domain
    
    return None


def calculate_hop_distance(prev_domain: Optional[str], curr_domain: str) -> float:
    """
    Calculate distance between two domains.
    
    Returns:
        float: 0-2 where 0=identical, 2=opposite
    """
    if not prev_domain:
        return 0.0  # First turn, no hop
    
    if prev_domain == curr_domain:
        return 0.0  # Same domain
    
    # Get embeddings
    prev_emb = DOMAIN_EMBEDDINGS.get(prev_domain, DOMAIN_EMBEDDINGS["general"])
    curr_emb = DOMAIN_EMBEDDINGS.get(curr_domain, DOMAIN_EMBEDDINGS["general"])
    
    # Calculate cosine distance
    distance = cosine_distance(prev_emb, curr_emb)
    
    return distance


def calculate_field_entropy(session_id: str) -> float:
    """
    Calculate domain scatter/entropy for session.
    
    Returns:
        float: 0-1 where 0=focused (one domain), 1=scattered (many domains)
    """
    turns = get_session_turns(session_id)
    
    if len(turns) < 2:
        return 0.0  # Need at least 2 turns
    
    # Get all domains
    domains = [turn.get("domain") for turn in turns if turn.get("domain")]
    
    if len(domains) < 2:
        return 0.0
    
    # Get unique domains
    unique_domains = list(set(domains))
    
    if len(unique_domains) == 1:
        return 0.0  # All same domain = no entropy
    
    # Calculate pairwise similarities
    embeddings = [
        DOMAIN_EMBEDDINGS.get(d, DOMAIN_EMBEDDINGS["general"])
        for d in domains
    ]
    
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = 1.0 - cosine_distance(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    if not similarities:
        return 0.0
    
    # Entropy = 1 - average similarity
    avg_similarity = np.mean(similarities)
    entropy = 1.0 - avg_similarity
    
    return float(entropy)


def get_turn_count(session_id: str) -> int:
    """Get total number of turns in session."""
    turns = get_session_turns(session_id)
    return len(turns)


def get_session_state(session_id: str) -> Dict[str, Any]:
    """
    Get comprehensive session state.
    
    Returns:
        {
            "session_id": str,
            "turn_count": int,
            "domains_visited": [str],
            "override_rate": float,
            "average_gnn": float,
            "field_entropy": float,
            "time_span": float (seconds)
        }
    """
    turns = get_session_turns(session_id)
    
    if not turns:
        return {
            "session_id": session_id,
            "turn_count": 0,
            "domains_visited": [],
            "override_rate": 0.0,
            "average_gnn": 0.0,
            "field_entropy": 0.0,
            "time_span": 0.0
        }
    
    # Extract metrics
    domains = [t.get("domain") for t in turns if t.get("domain")]
    overrides = [t.get("was_overridden", False) for t in turns]
    gnn_scores = [
        t.get("gnn_similarity", 0.0) 
        for t in turns 
        if t.get("gnn_similarity") is not None
    ]
    
    # Calculate override rate
    override_rate = sum(overrides) / len(overrides) if overrides else 0.0
    
    # Calculate average GNN
    average_gnn = np.mean(gnn_scores) if gnn_scores else 0.0
    
    # Calculate time span
    timestamps = [t.get("timestamp") for t in turns if t.get("timestamp")]
    time_span = 0.0
    if len(timestamps) >= 2:
        try:
            first = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
            last = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
            time_span = (last - first).total_seconds()
        except:
            pass
    
    # Calculate field entropy
    field_entropy = calculate_field_entropy(session_id)
    
    return {
        "session_id": session_id,
        "turn_count": len(turns),
        "domains_visited": list(set(domains)),
        "override_rate": float(override_rate),
        "average_gnn": float(average_gnn),
        "field_entropy": float(field_entropy),
        "time_span": float(time_span)
    }


def update_session_state(session_id: str, turn_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save turn data to Qdrant with SESSION_TURN class.
    
    Args:
        session_id: Session identifier
        turn_data: Turn metrics (domain, was_overridden, gnn_similarity, etc.)
    
    Returns:
        Storage result
    """
    try:
        from tools.chat_memory import store_chat_turn
        
        # Create turn summary text
        turn_summary = f"Turn {turn_data.get('turn_number', '?')} in session {session_id}"
        if turn_data.get("domain"):
            turn_summary += f" - Domain: {turn_data['domain']}"
        if turn_data.get("was_overridden"):
            turn_summary += f" - OVERRIDDEN: {turn_data.get('conflict_reason', 'N/A')}"
        
        # Store with SESSION_TURN class
        result = store_chat_turn(
            user_message=turn_data.get("user_message", ""),
            assistant_message=turn_summary,
            importance=None,
            session_id=session_id,
            extra_metadata={
                "memory_class": "SESSION_TURN",
                "turn_number": turn_data.get("turn_number", 0),
                "domain": turn_data.get("domain"),
                "was_overridden": turn_data.get("was_overridden", False),
                "conflict_reason": turn_data.get("conflict_reason"),
                "gnn_similarity": turn_data.get("gnn_similarity"),
                "hop_distance": turn_data.get("hop_distance"),
                "field_entropy": turn_data.get("field_entropy"),
                "stability_score": turn_data.get("stability_score")
            }
        )
        
        return result
        
    except Exception as e:
        # Silent fail for MCP compatibility
        pass
        return {"error": str(e)}


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Session Tracker CLI")
    parser.add_argument("--session-id", required=True, help="Session ID")
    parser.add_argument("--action", choices=["state", "previous", "entropy", "count"], 
                       default="state", help="Action to perform")
    
    args = parser.parse_args()
    
    if args.action == "state":
        state = get_session_state(args.session_id)
        print(json.dumps(state, indent=2))
    
    elif args.action == "previous":
        domain = get_previous_domain(args.session_id)
        print(f"Previous domain: {domain}")
    
    elif args.action == "entropy":
        entropy = calculate_field_entropy(args.session_id)
        print(f"Field entropy: {entropy:.3f}")
    
    elif args.action == "count":
        count = get_turn_count(args.session_id)
        print(f"Turn count: {count}")
