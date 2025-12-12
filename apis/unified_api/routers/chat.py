"""
Chat Router - Unified Chat Handler Backend - COGNITIVE ENHANCED
================================================================

Handles memory-enforced chat turns with:
- Optimal Memory System (9 layers)
- Cognitive Router (Phase 1-6 integration)
- Full intent, value, motivation signals

ARCHITECTURE:
- OptimalMemorySystem: 9-layer memory (CMC, SMM, DDE, AME, MLC, Neo4j, MIR, MCA, MCE)
- CognitiveRouter: Meta-Supervisor + Value Layer + Motivational Dynamics
- Integration: Cognitive signals enhance memory decisions

UPGRADED from symbiosis_router_v4 to cognitive-aware version.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sys
import os

# Add tools to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools'))

from symbiosis_router_v4 import handle_chat_turn, health_check
from cognitive_router import CognitiveRouter
from optimal_memory_system import OptimalMemorySystem
from value_layer import ValueLayer, HarmDetector

router = APIRouter()

# Initialize cognitive router and memory system (singletons for session)
cognitive_router = CognitiveRouter()
_memory_system: Optional[OptimalMemorySystem] = None
_value_layer: Optional[ValueLayer] = None
_harm_detector: Optional[HarmDetector] = None

# ============================================================
# SHARED COGNITIVE STATE - Updated by /turn, read by /status
# ============================================================
_last_cognitive_context: Dict[str, Any] = {
    "intent": {"mode": "idle", "active_domains": [], "confidence": 0.0},
    "value": {"value_level": "unknown", "harm_detected": False},
    "routing": {"canonical_override_strength": 0.0, "llm_temperature": 0.7},
    "balance": {"value": 0.5},
    "stability": {"stable": True},
    "meta": {
        "last_update": None,
        "last_user_message": None,
        "was_overridden": False,
        "turn_count": 0
    }
}

def update_shared_cognitive_state(
    cognitive_signals: Dict[str, Any],
    user_message: str,
    was_overridden: bool = False
):
    """Update shared cognitive state after each chat turn."""
    global _last_cognitive_context
    from datetime import datetime
    
    _last_cognitive_context = {
        "intent": cognitive_signals.get("intent", {}),
        "value": cognitive_signals.get("value", {}),
        "routing": cognitive_signals.get("routing_decision", {}),
        "balance": cognitive_signals.get("balance", {}),
        "stability": cognitive_signals.get("stability", {}),
        "motivation": cognitive_signals.get("motivation", {}),
        "recommendations": cognitive_signals.get("recommendations", []),
        "meta": {
            "last_update": datetime.utcnow().isoformat(),
            "last_user_message": user_message[:100] if user_message else None,
            "was_overridden": was_overridden,
            "turn_count": _last_cognitive_context.get("meta", {}).get("turn_count", 0) + 1
        }
    }


def get_memory_system() -> OptimalMemorySystem:
    """Get or create OptimalMemorySystem singleton."""
    global _memory_system
    if _memory_system is None:
        _memory_system = OptimalMemorySystem()
    return _memory_system


def get_harm_detector() -> HarmDetector:
    """Get or create HarmDetector singleton."""
    global _harm_detector
    if _harm_detector is None:
        _harm_detector = HarmDetector()
    return _harm_detector


class ChatTurnRequest(BaseModel):
    """Request model for unified chat handler."""
    user_message: str
    assistant_draft: str
    session_id: Optional[str] = None


class ChatTurnResponse(BaseModel):
    """Response model - ENHANCED with cognitive context."""
    final_answer: str
    original_answer: str
    was_overridden: bool
    conflict_reason: Optional[str]
    memory_used: str
    memory_stored: Dict[str, Any]
    gnn: Dict[str, Any]
    retrieved_chunks: List[Any]
    metadata: Dict[str, Any]
    cognitive_context: Optional[Dict[str, Any]] = None  # NEW: Cognitive signals


@router.post("/turn", response_model=ChatTurnResponse)
async def chat_turn(request: ChatTurnRequest):
    """
    Unified chat handler - COGNITIVE ENHANCED.
    
    Processes one chat turn with:
    - OptimalMemorySystem (9-layer memory architecture)
    - CognitiveRouter (Phase 1-6 cognitive signals)
    
    Automatically handles ALL steps:
    1. Cognitive signal generation (intent, value, motivation)
    2. Domain analysis (user + assistant)
    3. Memory retrieval (LONGTERM) with cognitive weighting
    4. Memory enforcement (fixes contradictions)
    5. GNN scoring (structural similarity to EFC)
    6. Storage (saves corrected answer)
    7. Answer enrichment with cognitive context
    
    Args:
        request: ChatTurnRequest with user_message, assistant_draft, optional session_id
    
    Returns:
        ChatTurnResponse with complete analysis + cognitive context
    
    NEW: cognitive_context contains:
        - intent: protection/learning/exploration/refinement
        - value: critical/important/routine
        - motivation: goals, preferences, persistence
        - routing: canonical_override, LLM temperature, triggers
    
    Example:
        POST /chat/turn
        {
            "user_message": "Hva heter jeg?",
            "assistant_draft": "Jeg heter Qwen"
        }
        
        Returns:
        {
            "final_answer": "Jeg heter Morten",
            "was_overridden": true,
            "conflict_reason": "Canonical memory: user.name=Morten",
            "memory_used": "Retrieved from CMC (Canonical Memory Core)...",
            "cognitive_context": {
                "intent": {"mode": "protection", "confidence": 0.92},
                "value": {"value_level": "critical"},
                "motivation": {"motivation_strength": 0.85, "active_goals": ["protect_identity"]},
                "routing": {"canonical_override_strength": 1.0, "llm_temperature": 0.3}
            },
            ...
        }
    """
    
    try:
        # Step 0: EFC Truth Protection - Check for wrong definitions in draft
        harm_detector = get_harm_detector()
        efc_harm = harm_detector.detect_efc_truth_corruption(
            key="efc.response",
            proposed_value=request.assistant_draft
        )
        
        efc_blocked = False
        efc_canonical_answer = None
        
        if efc_harm:
            # Wrong EFC definition detected - prepare canonical override
            efc_blocked = True
            efc_canonical_answer = "EFC står for Energy-Flow Cosmology – en unifisert teoretisk ramme for å beskrive kosmologiske fenomener gjennom energiflyt-prinsipper."
        
        # Step 1: Generate cognitive signals
        cognitive_signals = cognitive_router.process_and_route(
            user_input=request.user_message,
            session_context={"session_id": request.session_id or "default"},
            system_metrics={"accuracy": 0.85},  # TODO: Get real metrics
            value_context={
                "key": "chat.turn",
                "domain": "efc_theory" if efc_blocked else "conversation",
                "content": request.assistant_draft
            }
        )
        
        # Update cognitive signals with EFC harm if detected
        if efc_harm and cognitive_signals.get("value"):
            cognitive_signals["value"]["harm_detected"] = True
            cognitive_signals["value"]["harm_signals"] = [efc_harm.to_dict() if hasattr(efc_harm, 'to_dict') else str(efc_harm)]
        
        # Step 2-7: Call unified router (memory + enforcement + storage)
        result = handle_chat_turn(
            user_message=request.user_message,
            assistant_draft=efc_canonical_answer if efc_blocked else request.assistant_draft,
            session_id=request.session_id
        )
        
        # If EFC was blocked, FORCE correct answer (override any LLM generation)
        if efc_blocked:
            result["was_overridden"] = True
            result["conflict_reason"] = f"EFC Truth Protection: {efc_harm.evidence[0] if hasattr(efc_harm, 'evidence') else 'Wrong EFC definition blocked'}"
            # FORCE canonical answer - LLM cannot override this
            result["final_answer"] = efc_canonical_answer
            result["original_answer"] = request.assistant_draft
        
        # Map router output to response model
        memory = result.get("memory", {})
        memory_retrieved = memory.get("retrieved", "")
        
        # Convert memory string to list of chunks (split by lines if needed)
        if isinstance(memory_retrieved, str):
            retrieved_chunks = [memory_retrieved] if memory_retrieved.strip() else []
        else:
            retrieved_chunks = memory_retrieved  # Already a list
        
        # Build cognitive context for response
        cognitive_context = {
            "intent": cognitive_signals["intent"],
            "value": cognitive_signals.get("value"),
            "motivation": cognitive_signals.get("motivation"),
            "routing": cognitive_signals["routing_decision"],
            "balance": cognitive_signals["balance"],
            "stability": cognitive_signals["stability"],
            "recommendations": cognitive_signals["recommendations"]
        }
        
        # ============================================================
        # UPDATE SHARED STATE FOR DASHBOARD MONITORING
        # ============================================================
        update_shared_cognitive_state(
            cognitive_signals=cognitive_signals,
            user_message=request.user_message,
            was_overridden=result["was_overridden"]
        )
        
        return ChatTurnResponse(
            final_answer=result["final_answer"],
            original_answer=result["original_answer"],
            was_overridden=result["was_overridden"],
            conflict_reason=result["conflict_reason"],
            memory_used=memory_retrieved,
            memory_stored=memory.get("stored", {}),
            gnn=result.get("gnn", {}),
            retrieved_chunks=retrieved_chunks,
            metadata=result.get("metadata", {}),
            cognitive_context=cognitive_context  # NEW: Full cognitive signals
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat turn processing failed: {str(e)}"
        )


@router.get("/health")
async def chat_router_health():
    """
    Check health of Optimal Memory System (9 layers).
    
    Returns status of all memory layers:
    - CMC (Canonical Memory Core)
    - SMM (Semantic Mesh Memory)
    - DDE (Dynamic Domain Engine)
    - AME (Adaptive Memory Enforcer)
    - MLC (Meta-Learning Cortex)
    - Neo4j Graph Layer
    - MIR, MCA, MCE (Advanced layers)
    """
    health_status = health_check()
    
    if health_status["status"] == "healthy":
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)


# ============================================================
# DEBUG ENDPOINTS
# ============================================================

# Store last turn for debugging
_last_turn_result: Optional[Dict[str, Any]] = None
_last_turn_request: Optional[Dict[str, Any]] = None


@router.post("/turn-debug", response_model=ChatTurnResponse)
async def chat_turn_debug(request: ChatTurnRequest):
    """
    Same as /turn but stores result for /debug/last-turn inspection.
    Use this during development/testing.
    """
    global _last_turn_result, _last_turn_request
    
    try:
        result = handle_chat_turn(
            user_message=request.user_message,
            assistant_draft=request.assistant_draft,
            session_id=request.session_id
        )
        
        # Store for debug inspection
        _last_turn_request = {
            "user_message": request.user_message,
            "assistant_draft": request.assistant_draft,
            "session_id": request.session_id
        }
        _last_turn_result = result
        
        # Map router output to response model
        memory = result.get("memory", {})
        memory_retrieved = memory.get("retrieved", "")
        
        # Convert memory string to list
        if isinstance(memory_retrieved, str):
            retrieved_chunks = [memory_retrieved] if memory_retrieved.strip() else []
        else:
            retrieved_chunks = memory_retrieved
        
        return ChatTurnResponse(
            final_answer=result["final_answer"],
            original_answer=result["original_answer"],
            was_overridden=result["was_overridden"],
            conflict_reason=result["conflict_reason"],
            memory_used=memory_retrieved,
            memory_stored=memory.get("stored", {}),
            gnn=result.get("gnn", {}),
            retrieved_chunks=retrieved_chunks,
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat turn processing failed: {str(e)}"
        )


@router.get("/debug/last-turn")
async def debug_last_turn():
    """
    Get complete details of last processed turn (via /turn-debug).
    Useful for debugging memory enforcement, GNN scoring, etc.
    """
    if not _last_turn_result:
        return {
            "status": "no_data",
            "message": "No turn processed yet via /turn-debug"
        }
    
    return {
        "status": "ok",
        "request": _last_turn_request,
        "result": _last_turn_result,
        "analysis": {
            "memory_enforcement_triggered": _last_turn_result.get("was_overridden", False),
            "conflict_detected": _last_turn_result.get("conflict_reason") is not None,
            "gnn_available": _last_turn_result.get("gnn", {}).get("available", False),
            "memories_retrieved": len(_last_turn_result.get("memory", {}).get("retrieved", "")),
            "memory_stored": _last_turn_result.get("memory", {}).get("stored", {}).get("stored", False)
        }
    }


@router.get("/stats/overrides")
async def override_statistics():
    """
    Get statistics about memory overrides.
    
    NOTE: This is a placeholder - implement persistent storage
    for production (Redis/DB) to track across restarts.
    """
    # TODO: Implement persistent stats storage
    return {
        "status": "not_implemented",
        "message": "Implement persistent override tracking",
        "recommendation": "Use Redis or DB to store override events"
    }


# ============================================================
# TEST SUITE ENDPOINT
# ============================================================

@router.post("/test/known-failures")
async def test_known_failures():
    """
    Run test suite with 20 known failure cases.
    Verifies memory enforcement works correctly.
    
    Returns:
        Summary of pass/fail for each test case
    """
    
    test_cases = [
        # Identity tests
        {
            "name": "Assistant identity (Norwegian)",
            "user_message": "Hva heter du?",
            "assistant_draft": "Jeg heter Qwen",
            "expected_override": True,
            "expected_contains": "Opus"
        },
        {
            "name": "Assistant identity (English)",
            "user_message": "What is your name?",
            "assistant_draft": "I am Qwen",
            "expected_override": True,
            "expected_contains": "Opus"
        },
        {
            "name": "User identity",
            "user_message": "Hvem er jeg?",
            "assistant_draft": "Jeg vet ikke hvem du er",
            "expected_override": True,
            "expected_contains": "Morten"
        },
        # Relationship tests
        {
            "name": "User spouse",
            "user_message": "Hvem er jeg gift med?",
            "assistant_draft": "Jeg vet ikke",
            "expected_override": True,
            "expected_contains": "gift"
        },
        # Generic response (should NOT override)
        {
            "name": "General question (no override)",
            "user_message": "Hva er 2+2?",
            "assistant_draft": "2+2 er 4",
            "expected_override": False,
            "expected_contains": "4"
        },
    ]
    
    results = []
    
    for test in test_cases:
        try:
            result = handle_chat_turn(
                user_message=test["user_message"],
                assistant_draft=test["assistant_draft"],
                session_id=f"test-{test['name']}"
            )
            
            passed = True
            errors = []
            
            # Check override expectation
            if result["was_overridden"] != test["expected_override"]:
                passed = False
                errors.append(
                    f"Override mismatch: expected {test['expected_override']}, got {result['was_overridden']}"
                )
            
            # Check content
            if test["expected_contains"] not in result["final_answer"]:
                passed = False
                errors.append(
                    f"Content missing: expected '{test['expected_contains']}' in answer"
                )
            
            results.append({
                "test": test["name"],
                "passed": passed,
                "errors": errors,
                "final_answer": result["final_answer"],
                "was_overridden": result["was_overridden"]
            })
            
        except Exception as e:
            results.append({
                "test": test["name"],
                "passed": False,
                "errors": [f"Exception: {str(e)}"],
                "final_answer": None,
                "was_overridden": None
            })
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    return {
        "status": "ok",
        "summary": {
            "passed": passed_count,
            "failed": total_count - passed_count,
            "total": total_count,
            "pass_rate": f"{(passed_count/total_count)*100:.1f}%"
        },
        "results": results
    }


# ============================================================
# FAST COGNITIVE STATUS ENDPOINT (NO LLM CALL)
# ============================================================

@router.get("/cognitive/status")
async def cognitive_status():
    """
    Fast endpoint for monitoring dashboard.
    Returns LAST cognitive state from actual chat turns.
    
    Use this for live monitoring instead of /turn.
    Response time: <10ms (vs 15+ seconds for /turn)
    """
    global _last_cognitive_context
    
    # Check GNN availability
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
    
    gnn_available = False
    try:
        from gnn_scoring import _is_gnn_available
        gnn_available = _is_gnn_available()
    except:
        pass
    
    return {
        "status": "ok",
        "cognitive_context": _last_cognitive_context,
        "was_overridden": _last_cognitive_context.get("meta", {}).get("was_overridden", False),
        "final_answer": f"[Last turn: {_last_cognitive_context.get('meta', {}).get('last_user_message', 'No turns yet')}]",
        "original_answer": "[Status from shared state]",
        "gnn": {"available": gnn_available},
        "retrieved_chunks": [],
        "metadata": {
            "session_id": "monitor",
            "turn_number": _last_cognitive_context.get("meta", {}).get("turn_count", 0)
        }
    }
