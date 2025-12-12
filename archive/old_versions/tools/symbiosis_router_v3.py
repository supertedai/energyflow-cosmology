#!/usr/bin/env python3
"""
symbiosis_router_v3.py - Unified Chat Router with Domain Engine
===============================================================

CRITICAL UPGRADE: Single tool architecture.

Instead of 15+ separate tools, this provides ONE unified endpoint:
    handle_chat_turn()

Internally coordinates:
1. Domain analysis (via domain_engine_v2)
2. Memory retrieval
3. Memory enforcement
4. GNN scoring
5. Storage
6. Feedback

This is exposed as a SINGLE MCP tool, reducing complexity dramatically.

Usage from MCP:
    symbiosis_chat_turn(
        user_message="Hva er entropi?",
        assistant_draft="Entropi måler uorden..."
    )

Returns complete structured result with all signals.
"""

import os
import sys
from typing import Optional, Dict, Any
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

load_dotenv()

# Config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Import internal modules
from tools.chat_memory import retrieve_relevant_memory, store_chat_turn
from tools.gnn_scoring import get_gnn_similarity_score
from tools.memory_authority_enforcer import enforce_memory_authority
from tools.domain_engine_v2 import analyze_semantic_field


# ============================================================
# UNIFIED CHAT HANDLER
# ============================================================

def handle_chat_turn(
    user_message: str,
    assistant_draft: str,
    session_id: Optional[str] = None,
    enable_domain_analysis: bool = True,
    enable_gnn: bool = True,
    enable_memory_enforcement: bool = True,
) -> Dict[str, Any]:
    """
    UNIFIED chat router - single entry point for ALL chat operations.

    This replaces 15+ separate tools with ONE coordinated flow:
    
    Flow:
        1. Domain analysis (what field is this?)
        2. Memory retrieval (relevant context)
        3. Memory enforcement (fix contradictions)
        4. GNN scoring (structural similarity)
        5. Storage (save corrected answer)
        6. Return complete structured result

    Args:
        user_message: User's question/statement
        assistant_draft: LLM's initial response
        session_id: Optional session identifier
        enable_domain_analysis: Whether to run domain engine
        enable_gnn: Whether to use GNN scoring
        enable_memory_enforcement: Whether to enforce memory authority

    Returns:
        {
            "final_answer": str,
            "original_answer": str,
            "was_overridden": bool,
            "conflict_reason": str,
            
            "domain": {
                "primary_domain": str,
                "primary_label": str,
                "confidence": float,
                "efc_relevance": float,
                "all_scores": {...}
            },
            
            "memory": {
                "retrieved": str,
                "stored": {...}
            },
            
            "gnn": {
                "available": bool,
                "similarity": float,
                "top_matches": [...]
            },
            
            "metadata": {
                "session_id": str,
                "timestamp": str
            }
        }
    """
    
    from datetime import datetime
    from tools.session_tracker import (
        get_previous_domain,
        calculate_hop_distance,
        calculate_field_entropy,
        get_turn_count
    )
    
    # Session tracking - LAG 1: CAPTURE
    previous_domain = get_previous_domain(session_id) if session_id else None
    turn_number = get_turn_count(session_id) + 1 if session_id else 1
    
    result = {
        "final_answer": assistant_draft,
        "original_answer": assistant_draft,
        "was_overridden": False,
        "conflict_reason": None,
        "domain": {},
        "memory": {"retrieved": "", "stored": {}},
        "gnn": {"available": False},
        "metadata": {
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "turn_number": turn_number,
            "previous_domain": previous_domain
        }
    }

    # ========================================
    # STEP 1: DOMAIN ANALYSIS
    # ========================================
    
    if enable_domain_analysis:
        try:
            # Analyze BOTH user query and assistant response
            user_domain = analyze_semantic_field(
                text=user_message,
                source="chat_user",
                session_id=session_id,
                extra_metadata={"role": "user"}
            )
            
            assistant_domain = analyze_semantic_field(
                text=assistant_draft,
                source="chat_assistant",
                session_id=session_id,
                extra_metadata={"role": "assistant"}
            )
            
            # Store domain info (use assistant's domain for routing)
            result["domain"] = {
                "primary_domain": assistant_domain.get("primary_domain"),
                "primary_label": assistant_domain.get("primary_domain_label"),
                "confidence": assistant_domain.get("primary_domain_confidence"),
                "efc_relevance": assistant_domain.get("efc_relevance"),
                "user_domain": user_domain.get("primary_domain"),
                "assistant_domain": assistant_domain.get("primary_domain"),
                "entropy": assistant_domain.get("entropy"),
            }
            
            # LAG 1: CAPTURE - Calculate domain drift metrics
            current_domain = assistant_domain.get("primary_domain")
            hop_distance = calculate_hop_distance(previous_domain, current_domain)
            field_entropy = calculate_field_entropy(session_id) if session_id else 0.0
            stability_score = 1.0 / (1.0 + hop_distance)
            
            # Update metadata with drift metrics
            result["metadata"].update({
                "current_domain": current_domain,
                "hop_distance": hop_distance,
                "field_entropy": field_entropy,
                "stability_score": stability_score
            })
            
        except Exception as e:
            print(f"⚠️  Domain analysis failed: {e}")
            result["domain"] = {"error": str(e)}

    # ========================================
    # STEP 2: MEMORY RETRIEVAL
    # ========================================
    
    try:
        memory_context = retrieve_relevant_memory(
            query=user_message,
            k=5,
            memory_class_filter="LONGTERM"
        )
        result["memory"]["retrieved"] = memory_context
    except Exception as e:
        print(f"⚠️  Memory retrieval failed: {e}")
        memory_context = ""

    # ========================================
    # STEP 3: MEMORY ENFORCEMENT (Universal Fact Checking)
    # ========================================
    
    if enable_memory_enforcement:
        try:
            # Use improved enforcer that handles ALL factual questions
            from memory_authority_enforcer import enforce_memory_authority
            
            enforcement_result = enforce_memory_authority(
                user_question=user_message,
                llm_response=assistant_draft,
                memory_context=memory_context,
                auto_retrieve=True
            )

            if enforcement_result["overridden"]:
                result["final_answer"] = enforcement_result["response"]
                result["was_overridden"] = True
                result["conflict_reason"] = enforcement_result.get("reason", "Memory contradiction")
                
                print(f"🔒 MEMORY OVERRIDE: {enforcement_result['reason']}")
                print(f"   Original: {assistant_draft[:80]}...")
                print(f"   Corrected: {enforcement_result['response'][:80]}...")

        except Exception as e:
            print(f"⚠️  Memory enforcement failed: {e}")
            import traceback
            traceback.print_exc()

    # ========================================
    # STEP 4: GNN SCORING (if applicable)
    # ========================================
    
    if enable_gnn:
        try:
            # Use domain info to decide if GNN is relevant
            primary_domain = result["domain"].get("primary_domain")
            
            # Only run GNN for theory domains
            theory_domains = {"cosmology", "thermo_energy", "ai_symbiosis", "meta"}
            
            if primary_domain in theory_domains:
                gnn_result = get_gnn_similarity_score(
                    private_chunk_text=result["final_answer"],
                    top_k=5,
                    chunk_domain=primary_domain
                )
                
                result["gnn"] = {
                    "available": gnn_result.get("available", False),
                    "similarity": gnn_result.get("gnn_similarity", 0.0),
                    "confidence": gnn_result.get("confidence", 0.0),
                    "top_matches": gnn_result.get("top_matches", [])[:3],
                    "reason": gnn_result.get("reason")
                }
            else:
                result["gnn"] = {
                    "available": False,
                    "reason": f"Domain '{primary_domain}' not applicable for GNN"
                }
                
        except Exception as e:
            print(f"⚠️  GNN scoring failed: {e}")
            result["gnn"] = {"available": False, "error": str(e)}

    # ========================================
    # STEP 5: STORAGE
    # ========================================
    
    try:
        store_result = store_chat_turn(
            user_message=user_message,
            assistant_message=result["final_answer"],
            importance=None,  # auto-detect
            session_id=session_id,
        )
        result["memory"]["stored"] = store_result
    except Exception as e:
        print(f"⚠️  Memory storage failed: {e}")
        result["memory"]["stored"] = {"error": str(e)}

    # ========================================
    # STEP 6: ENRICH FINAL ANSWER (if applicable)
    # ========================================
    
    # Add GNN meta-info if strong signal
    if (result["gnn"].get("available") and 
        result["gnn"].get("similarity", 0) > 0.7):
        
        top_matches = result["gnn"].get("top_matches", [])
        if top_matches:
            best = top_matches[0]
            gnn_meta = (
                f"\n\n[Meta · GNN Signal]\n"
                f"- Dette resonerer sterkt med EFC: '{best.get('concept')}'\n"
                f"- Strukturell likhet: {result['gnn']['similarity']:.2f}\n"
            )
            result["final_answer"] += gnn_meta

    return result


# ============================================================
# CLI TESTING
# ============================================================

if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Test symbiosis_router_v3 (unified)")
    parser.add_argument("--user", required=True, help="User message")
    parser.add_argument("--assistant", required=True, help="Assistant draft")
    parser.add_argument("--session-id", help="Optional session id")
    parser.add_argument("--no-domain", action="store_true", help="Disable domain analysis")
    parser.add_argument("--no-gnn", action="store_true", help="Disable GNN")
    parser.add_argument("--no-enforce", action="store_true", help="Disable memory enforcement")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if not args.json:
        print("🧠 Testing Unified Symbiosis Router v3\n")
        print(f"User: {args.user}")
        print(f"Assistant Draft: {args.assistant}")
        print()

    result = handle_chat_turn(
        user_message=args.user,
        assistant_draft=args.assistant,
        session_id=args.session_id,
        enable_domain_analysis=not args.no_domain,
        enable_gnn=not args.no_gnn,
        enable_memory_enforcement=not args.no_enforce,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n" + "="*60)
        print("RESULT:")
        print("="*60)
        
        print(f"\n📝 Final Answer: {result['final_answer'][:100]}...")
        
        if result["was_overridden"]:
            print(f"\n🔒 OVERRIDDEN: {result['conflict_reason']}")
            print(f"   Original: {result['original_answer'][:60]}...")
        
        domain = result.get("domain", {})
        if domain.get("primary_domain"):
            print(f"\n🎯 Domain: {domain['primary_label']} ({domain['primary_domain']})")
            print(f"   Confidence: {domain['confidence']}")
            print(f"   EFC Relevance: {domain['efc_relevance']}")
        
        if result["gnn"].get("available"):
            print(f"\n🧠 GNN: {result['gnn']['similarity']:.3f}")
            if result["gnn"].get("top_matches"):
                print(f"   Top match: {result['gnn']['top_matches'][0]['concept']}")
        
        memory = result.get("memory", {})
        if memory.get("stored", {}).get("stored"):
            print(f"\n💾 Stored: {memory['stored']['document_id']}")
