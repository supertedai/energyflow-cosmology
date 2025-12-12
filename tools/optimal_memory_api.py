#!/usr/bin/env python3
"""
optimal_memory_api.py - Production API for Optimal Memory System
================================================================

FastAPI endpoint for the complete 5-layer memory system.

Endpoints:
- POST /chat/turn - Answer question with full memory intelligence
- POST /memory/fact - Store canonical fact
- POST /memory/context - Store context
- POST /feedback - Provide feedback
- GET /stats - Get system statistics
- GET /profile - Get learned user profile
- POST /profile/export - Export learned profile
- POST /profile/import - Import learned profile

Usage with OpenWebUI or any chat interface:
    POST http://localhost:8001/chat/turn
    {
        "user_message": "Hva heter jeg?",
        "assistant_draft": "Du heter Andreas",
        "session_id": "user123"
    }
    
    Response:
    {
        "final_response": "Du heter Morten",
        "was_overridden": true,
        "domain": "identity",
        "mode": "precision",
        "reasoning": "LONGTERM fact contradicts LLM"
    }
"""

import os
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from optimal_memory_system import OptimalMemorySystem

# Initialize FastAPI
app = FastAPI(
    title="Optimal Memory System API",
    description="5-layer adaptive memory with CMC, SMM, DDE, AME, MLC",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory system (singleton)
memory_system = None

def get_memory_system() -> OptimalMemorySystem:
    """Get or create memory system instance."""
    global memory_system
    if memory_system is None:
        memory_system = OptimalMemorySystem(
            canonical_collection="canonical_facts",
            semantic_collection="semantic_mesh"
        )
    return memory_system


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class ChatTurnRequest(BaseModel):
    """Request for answering a question."""
    user_message: str
    assistant_draft: str
    session_id: Optional[str] = "default"


class StorageFactRequest(BaseModel):
    """Request for storing a canonical fact."""
    key: str
    value: Any
    domain: str
    fact_type: str = "general"
    authority: str = "SHORT_TERM"
    text: Optional[str] = None


class StoreContextRequest(BaseModel):
    """Request for storing context."""
    text: str
    domains: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    session_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request for providing feedback."""
    question: str
    response: str
    was_correct: bool
    was_helpful: bool = True


class ProfileExportRequest(BaseModel):
    """Request for exporting profile."""
    filepath: str = "/tmp/optimal_memory_profile.json"


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "operational",
        "system": "Optimal Memory System v1.0",
        "layers": ["CMC", "SMM", "DDE", "AME", "MLC"]
    }


@app.post("/chat/turn")
async def chat_turn(request: ChatTurnRequest) -> Dict[str, Any]:
    """
    Answer a question with full 5-layer intelligence.
    
    This is the main endpoint for chat integration.
    
    Process:
    1. User asks question
    2. LLM generates draft response
    3. This endpoint applies 5-layer memory intelligence
    4. Returns final response (possibly overridden)
    
    Returns:
        - final_response: The answer to show user
        - decision: OVERRIDE/TRUST_LLM/AUGMENT/DEFER
        - domain: Detected domain
        - mode: Cognitive mode
        - was_overridden: Bool
        - reasoning: Why this decision
        - ... full metadata
    """
    try:
        system = get_memory_system()
        
        result = system.answer_question(
            question=request.user_message,
            llm_draft=request.assistant_draft,
            session_id=request.session_id
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/fact")
async def store_fact(request: StorageFactRequest) -> Dict[str, Any]:
    """
    Store a canonical fact.
    
    Use this to teach the system absolute truths.
    
    Example:
        POST /memory/fact
        {
            "key": "user_name",
            "value": "Morten",
            "domain": "identity",
            "fact_type": "name",
            "authority": "LONGTERM"
        }
    """
    try:
        system = get_memory_system()
        
        fact = system.store_fact(
            key=request.key,
            value=request.value,
            domain=request.domain,
            fact_type=request.fact_type,
            authority=request.authority,
            text=request.text
        )
        
        return {
            "status": "stored",
            "fact_id": fact.id,
            "key": fact.key,
            "domain": fact.domain,
            "authority": fact.authority
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/context")
async def store_context(request: StoreContextRequest) -> Dict[str, Any]:
    """
    Store dynamic context.
    
    Use this for non-canonical information like theories, explanations, etc.
    
    Example:
        POST /memory/context
        {
            "text": "EFC theory describes energy flow through scales",
            "domains": ["cosmology", "theory"],
            "tags": ["EFC", "entropy"]
        }
    """
    try:
        system = get_memory_system()
        
        chunk = system.store_context(
            text=request.text,
            domains=request.domains,
            tags=request.tags,
            session_id=request.session_id
        )
        
        return {
            "status": "stored",
            "chunk_id": chunk.id,
            "domains": chunk.domains,
            "tags": chunk.tags
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def provide_feedback(request: FeedbackRequest) -> Dict[str, str]:
    """
    Provide user feedback.
    
    This is how the system learns from you.
    
    Example:
        POST /feedback
        {
            "question": "Hva heter jeg?",
            "response": "Du heter Morten",
            "was_correct": true,
            "was_helpful": true
        }
    """
    try:
        system = get_memory_system()
        
        system.provide_feedback(
            question=request.question,
            response=request.response,
            was_correct=request.was_correct,
            was_helpful=request.was_helpful
        )
        
        return {
            "status": "feedback_recorded",
            "message": "System learned from your feedback"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get comprehensive system statistics.
    
    Returns stats from all 5 layers:
    - CMC: Canonical facts stored
    - SMM: Context chunks
    - DDE: Learned patterns, domain transitions
    - AME: Enforcement decisions
    - MLC: Cognitive modes, user profile
    """
    try:
        system = get_memory_system()
        return system.get_stats()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile")
async def get_profile() -> Dict[str, Any]:
    """
    Get learned user profile.
    
    Returns:
    - Domain affinities
    - Mode frequencies
    - Correction rates
    - Transition patterns
    - Adaptive settings
    """
    try:
        system = get_memory_system()
        return system.mlc.get_stats()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/export")
async def export_profile(request: ProfileExportRequest) -> Dict[str, str]:
    """
    Export learned profile to file.
    
    This preserves learning across restarts.
    """
    try:
        system = get_memory_system()
        system.export_learned_profile(request.filepath)
        
        return {
            "status": "exported",
            "filepath": request.filepath
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/import")
async def import_profile(filepath: str) -> Dict[str, str]:
    """
    Import previously learned profile.
    """
    try:
        system = get_memory_system()
        system.import_learned_profile(filepath)
        
        return {
            "status": "imported",
            "filepath": filepath
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("🚀 Starting Optimal Memory System API")
    print("=" * 60)
    
    # Initialize system
    get_memory_system()
    
    # Try to load saved profile
    profile_path = "/tmp/optimal_memory_profile.json"
    if os.path.exists(profile_path):
        try:
            memory_system.import_learned_profile(profile_path)
            print(f"✅ Loaded profile from {profile_path}")
        except Exception as e:
            print(f"⚠️ Could not load profile: {e}")
    
    print("=" * 60)
    print("✅ API ready at http://localhost:8001")
    print("📖 Docs at http://localhost:8001/docs")
    print()


@app.on_event("shutdown")
async def shutdown_event():
    """Save profile on shutdown."""
    print("\n🛑 Shutting down...")
    
    try:
        memory_system.export_learned_profile("/tmp/optimal_memory_profile.json")
        print("✅ Profile saved")
    except Exception as e:
        print(f"⚠️ Could not save profile: {e}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "optimal_memory_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
