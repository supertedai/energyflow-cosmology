#!/usr/bin/env python3
"""
chat_intention_bridge.py - Chat → Cognitive Stack Bridge
========================================================

Purpose: Connect chat interactions to full cognitive stack

This module:
- Takes chat messages (user + assistant)
- Routes through cognitive_router for full stack analysis:
  * Intent detection (protection/learning/exploration)
  * Value assessment (critical/important/routine)
  * Motivational dynamics (goals, preferences, persistence)
- Stores them in Private Memory with cognitive context
- Retrieves relevant existing chunks
- Runs Intention Gate analysis enhanced with cognitive signals
- Returns suggestions WITH cognitive reasoning

Safety:
- ❌ NO writes to memory classes
- ❌ NO promotion/demotion
- ❌ NO steering execution
- ✅ ONLY observation and cognitive-enhanced suggestions

Flow:
    User message + Assistant response
        ↓
    Route through CognitiveRouter (Intent + Value + Motivation)
        ↓
    Store via chat_memory with cognitive context
        ↓
    Retrieve relevant chunks
        ↓
    Run intention_gate enhanced with cognitive signals
        ↓
    Return structured suggestions + cognitive insights
        ↓
    [Human decides what to do]

NEW: Cognitive Stack Integration
- Intent signal drives retrieval weighting
- Value decision affects canonical override strength
- Motivational signal modulates protection/exploration
- Stability report triggers self-healing if needed
- Balance metric exposed for optimization

Usage:
    from chat_intention_bridge import analyze_chat_turn
    
    suggestions = analyze_chat_turn(
        user_message="What is entropy in EFC?",
        assistant_message="Entropy is the driving force..."
    )
    
    # Returns:
    {
        "stored_chunk_id": "uuid...",
        "analyzed_chunks": 5,
        "cognitive_signals": {
            "intent_mode": "learning",
            "value_level": "routine",
            "motivation_strength": 0.65,
            "active_goals": ["optimize_learning"],
            "routing_decision": {...}
        },
        "suggestions": [
            {
                "chunk_id": "uuid...",
                "text_preview": "Entropy drives...",
                "current_class": "transient",
                "action": "promote",
                "reason": "High confidence, strong signals, LEARNING intent supports exploration",
                "confidence": 0.82,
                "risk": "low",
                "gnn_similarity": 0.75,
                "gnn_available": True,
                "cognitive_boost": 0.15  # NEW: Intent-driven boost
            }
        ]
    }
"""

import os
import sys
import json
from typing import Dict, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Import existing modules
from chat_memory import store_chat_turn, retrieve_relevant_memory
from intention_gate import (
    fetch_chunks_with_feedback,
    calculate_scores,
    suggest_action
)

# Import NEW: Cognitive Router
from tools.cognitive_router import CognitiveRouter

# Neo4j config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Try to import GNN scoring
try:
    from gnn_scoring import add_gnn_signal_to_scores
    GNN_AVAILABLE = True
except ImportError:
    GNN_AVAILABLE = False
    print("[chat_intention_bridge] GNN scoring not available", file=sys.stderr)

# Initialize cognitive router (singleton for session)
_cognitive_router = None

def get_cognitive_router() -> CognitiveRouter:
    """Get or create cognitive router singleton"""
    global _cognitive_router
    if _cognitive_router is None:
        _cognitive_router = CognitiveRouter()
    return _cognitive_router


# ============================================================
# MAIN BRIDGE FUNCTION
# ============================================================

def analyze_chat_turn(
    user_message: str,
    assistant_message: str,
    importance: str = "medium",
    max_analyzed_chunks: int = 10,
    session_context: Optional[Dict] = None
) -> Dict:
    """
    Analyze a chat turn with FULL COGNITIVE STACK
    
    NEW: Routes through CognitiveRouter for intent + value + motivation analysis
    
    Args:
        user_message: What the user said
        assistant_message: What the assistant responded
        importance: "high" | "medium" | "low" (affects storage)
        max_analyzed_chunks: Maximum number of chunks to analyze
        session_context: Optional session info for cognitive routing
        
    Returns:
        {
            "stored_chunk_id": str,
            "analyzed_chunks": int,
            "cognitive_signals": {           # NEW
                "intent_mode": str,
                "value_level": str,
                "motivation_strength": float,
                "active_goals": List[str],
                "routing_decision": Dict
            },
            "suggestions": [
                {
                    "chunk_id": str,
                    "text_preview": str,
                    "current_class": str,
                    "action": str,
                    "reason": str,             # Enhanced with cognitive reasoning
                    "confidence": float,
                    "risk": str,
                    "gnn_similarity": float,
                    "gnn_available": bool,
                    "cognitive_boost": float  # NEW: Intent-driven adjustment
                }
            ],
            "timestamp": str
        }
    """
    # NEW: Step 0 - Route through cognitive stack
    router = get_cognitive_router()
    
    # Prepare session context
    if session_context is None:
        session_context = {}
    
    # Detect if this is identity/protection query
    is_identity_query = any(word in user_message.lower() for word in [
        "hva heter", "who am i", "mitt navn", "my name", "min identitet"
    ])
    
    value_context = None
    if is_identity_query:
        value_context = {
            "key": "user.name",
            "domain": "identity",
            "content": None,  # Unknown at this stage
            "metadata": {"is_canonical": True, "trust_score": 0.95}
        }
    
    # Get cognitive signals
    cognitive_signals = router.process_and_route(
        user_input=user_message,
        session_context=session_context,
        system_metrics={"accuracy": 0.85, "override_rate": 0.2},
        value_context=value_context
    )
    
    # Extract routing decision
    routing_decision = cognitive_signals["routing_decision"]
    intent_mode = cognitive_signals["intent"]["mode"]
    
    motivation_strength = 0.5  # Default
    active_goals = []
    if cognitive_signals["motivation"]:
        motivation_strength = cognitive_signals["motivation"]["motivation_strength"]
        active_goals = [g["goal_type"] for g in cognitive_signals["motivation"]["active_goals"]]
    
    value_level = "routine"
    if cognitive_signals["value"]:
        value_level = cognitive_signals["value"]["value_level"]
    
    # Step 1: Store the chat turn with cognitive context
    result = store_chat_turn(
        user_message=user_message,
        assistant_message=assistant_message,
        importance=importance
    )
    
    stored_chunk_id = result.get("chunk_id")
    
    # Step 2: Retrieve relevant chunks (weighted by routing decision)
    combined_query = f"{user_message} {assistant_message}"
    retrieval_weight = routing_decision["memory_retrieval_weight"]
    
    # Adjust k based on routing decision
    adjusted_k = int(max_analyzed_chunks * retrieval_weight)
    adjusted_k = max(adjusted_k, 3)  # At least 3
    
    relevant_memories = retrieve_relevant_memory(
        query=combined_query,
        k=adjusted_k
    )
    
    # Step 3: Fetch chunks for analysis
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
    )
    
    try:
        with driver.session() as session:
            all_chunks = fetch_chunks_with_feedback(session)
            chunks_to_analyze = sorted(
                all_chunks,
                key=lambda c: c.get("created_at") or 0,
                reverse=True
            )[:adjusted_k]
    finally:
        driver.close()
    
    # Step 4: Run intention_gate analysis ENHANCED with cognitive signals
    suggestions = []
    canonical_override_strength = routing_decision["canonical_override_strength"]
    
    for chunk in chunks_to_analyze:
        try:
            # Calculate base scores
            scores = calculate_scores(
                chunk["feedback"],
                chunk["created_at"]
            )
            
            # Enhance with GNN if available
            if GNN_AVAILABLE:
                try:
                    scores = add_gnn_signal_to_scores(
                        chunk_text=chunk["text"],
                        existing_scores=scores,
                        manual_feedback_count=chunk["manual_feedback_count"],
                        chunk_domain=None
                    )
                except Exception as e:
                    print(f"[chat_intention_bridge] GNN scoring failed: {e}", file=sys.stderr)
            
            # NEW: Apply cognitive boost
            cognitive_boost = 0.0
            
            # If PROTECTION mode and chunk is canonical → strong boost
            if intent_mode == "protection" and chunk["memory_class"] == "canonical":
                cognitive_boost = canonical_override_strength * 0.3
            
            # If LEARNING mode → allow exploration (slight boost to non-canonical)
            elif intent_mode == "learning" and chunk["memory_class"] in ["transient", "working"]:
                cognitive_boost = 0.1
            
            # If high motivation → boost confidence
            if motivation_strength > 0.8:
                cognitive_boost += 0.05
            
            # Apply boost to confidence
            original_confidence = scores.get("confidence", 0.0)
            boosted_confidence = min(original_confidence + cognitive_boost, 1.0)
            scores["confidence"] = boosted_confidence
            
            # Get suggestion
            class_changed_at = chunk.get("class_changed_at") or chunk.get("created_at", 0)
            suggestion = suggest_action(
                chunk["id"],
                chunk["memory_class"],
                scores,
                class_changed_at,
                chunk["manual_feedback_count"]
            )
            
            # NEW: Enhance reason with cognitive context
            cognitive_reasoning = []
            if intent_mode == "protection":
                cognitive_reasoning.append("PROTECTION mode active")
            elif intent_mode == "learning":
                cognitive_reasoning.append("LEARNING mode - exploration favored")
            
            if value_level == "critical":
                cognitive_reasoning.append("CRITICAL value - maximum safety")
            
            if active_goals:
                cognitive_reasoning.append(f"Active goals: {', '.join(active_goals)}")
            
            enhanced_reason = suggestion["reason"]
            if cognitive_reasoning:
                enhanced_reason += " | " + ", ".join(cognitive_reasoning)
            
            # Format for output
            suggestions.append({
                "chunk_id": chunk["id"],
                "text_preview": chunk["text"][:100] if chunk["text"] else "",
                "current_class": chunk["memory_class"],
                "action": suggestion["action"],
                "reason": enhanced_reason,  # Enhanced with cognitive reasoning
                "confidence": boosted_confidence,
                "risk": scores.get("risk", "unknown"),
                "gnn_similarity": scores.get("gnn_similarity", 0.0),
                "gnn_available": scores.get("gnn_available", False),
                "risk_note": suggestion.get("risk_note", ""),
                "cognitive_boost": cognitive_boost  # NEW
            })
            
        except Exception as e:
            print(f"[chat_intention_bridge] Error analyzing chunk {chunk['id']}: {e}", file=sys.stderr)
            continue
    
    # Step 5: Return structured result with cognitive signals
    return {
        "stored_chunk_id": stored_chunk_id,
        "analyzed_chunks": len(suggestions),
        "cognitive_signals": {
            "intent_mode": intent_mode,
            "value_level": value_level,
            "motivation_strength": motivation_strength,
            "active_goals": active_goals,
            "routing_decision": routing_decision,
            "recommendations": cognitive_signals["recommendations"]
        },
        "suggestions": suggestions,
        "timestamp": datetime.utcnow().isoformat()
    }


def format_suggestions_for_display(result: Dict) -> str:
    """
    Format suggestions with COGNITIVE INSIGHTS
    
    Args:
        result: Output from analyze_chat_turn()
        
    Returns:
        Formatted string with cognitive context
    """
    output = []
    output.append("🧠 **Cognitive Stack Analysis**\n")
    
    # NEW: Show cognitive signals
    signals = result.get("cognitive_signals", {})
    if signals:
        output.append("**Cognitive State:**")
        output.append(f"  Intent: {signals.get('intent_mode', 'unknown')}")
        output.append(f"  Value: {signals.get('value_level', 'unknown')}")
        output.append(f"  Motivation: {signals.get('motivation_strength', 0):.2f}")
        if signals.get("active_goals"):
            output.append(f"  Active Goals: {', '.join(signals['active_goals'])}")
        output.append("")
    
    output.append(f"Stored new chunk: {result['stored_chunk_id']}")
    output.append(f"Analyzed {result['analyzed_chunks']} existing chunks\n")
    
    if not result['suggestions']:
        output.append("No suggestions at this time.\n")
        return "\n".join(output)
    
    # Group by action
    actions = {}
    for s in result['suggestions']:
        action = s['action']
        if action not in actions:
            actions[action] = []
        actions[action].append(s)
    
    # Display by priority
    priority_order = ['promote', 'review', 'wait', 'demote', 'none']
    
    for action in priority_order:
        if action not in actions:
            continue
            
        suggestions = actions[action]
        if not suggestions:
            continue
        
        output.append(f"\n**{action.upper()}** ({len(suggestions)} chunks):")
        
        for s in suggestions[:3]:  # Show max 3 per category
            output.append(f"\n  • {s['text_preview']}...")
            output.append(f"    Class: {s['current_class']} → Confidence: {s['confidence']:.2f}")
            
            # NEW: Show cognitive boost
            if s.get('cognitive_boost', 0) > 0:
                output.append(f"    Cognitive Boost: +{s['cognitive_boost']:.2f}")
            
            output.append(f"    Reason: {s['reason']}")
            
            if s['gnn_available']:
                output.append(f"    GNN Similarity: {s['gnn_similarity']:.2f}")
            
            if s['risk_note']:
                output.append(f"    ⚠️ {s['risk_note']}")
    
    # NEW: Show recommendations from cognitive stack
    if signals.get("recommendations"):
        output.append("\n**Cognitive Recommendations:**")
        for rec in signals["recommendations"][:3]:
            output.append(f"  • {rec}")
    
    output.append(f"\n---\nTimestamp: {result['timestamp']}")
    
    return "\n".join(output)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Chat Intention Bridge - Test Mode")
    parser.add_argument("--user", help="User message", required=True)
    parser.add_argument("--assistant", help="Assistant message", required=True)
    parser.add_argument("--importance", choices=["high", "medium", "low"], default="medium")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print("🔍 Analyzing chat turn...\n")
    
    result = analyze_chat_turn(
        user_message=args.user,
        assistant_message=args.assistant,
        importance=args.importance
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_suggestions_for_display(result))
