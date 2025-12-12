"""
Msty AI Live Context API
Provides real-time context and EFC-augmented responses for Msty AI client
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tools.optimal_memory_system import OptimalMemorySystem
from tools.efc_theory_engine import EFCTheoryEngine
from tools.neo4j_graph_layer import Neo4jGraphLayer
from tools.canonical_memory_core import CanonicalMemoryCore
from tools.semantic_mesh_memory import SemanticMeshMemory

router = APIRouter()

# Global system (initialized on first use)
_memory_system = None
_efc_engine = None


def get_memory_system():
    """Lazy initialization of memory system."""
    global _memory_system, _efc_engine
    
    if _memory_system is None:
        _memory_system = OptimalMemorySystem()
        _efc_engine = _memory_system.efc_engine
    
    return _memory_system, _efc_engine


# Request/Response models
class MstyContextRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    user_id: Optional[str] = None
    domain: Optional[str] = None


class MstyContextResponse(BaseModel):
    query: str
    context: Dict[str, Any]
    efc_pattern_detected: bool
    efc_score: float
    efc_reasoning: str
    should_use_efc: bool
    related_concepts: List[str]
    conversation_context: Optional[str]
    timestamp: str


class MstyQueryRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    user_id: Optional[str] = None
    domain: Optional[str] = None
    use_efc_augmentation: bool = True


class MstyQueryResponse(BaseModel):
    answer: str
    efc_used: bool
    context_retrieved: bool
    patterns_detected: List[str]
    confidence: float
    sources: List[str]
    timestamp: str


class MstyFeedbackRequest(BaseModel):
    query: str
    response: str
    was_helpful: bool
    user_id: Optional[str] = None
    domain: Optional[str] = None


@router.get("/live-context")
async def get_live_context_simple(query: str = ""):
    """
    Simple GET endpoint for Msty AI Live Context integration.
    
    Usage: GET /msty/live-context?query=Your+question+here
    
    Returns formatted context for injection into conversation.
    """
    try:
        if not query:
            return {
                "context": "No query provided. Add ?query=your_question to get context.",
                "status": "ready"
            }
        
        memory_system, efc_engine = get_memory_system()
        
        # Detect EFC patterns
        efc_result = efc_engine.detect_efc_pattern(
            question=query,
            domain=None
        )
        
        # Get semantic context
        try:
            semantic_results = memory_system.smm.search_context(
                query=query,
                k=3
            )
            
            semantic_context = "\n\n".join([
                f"• {chunk.text[:200]}..." if len(chunk.text) > 200 else f"• {chunk.text}"
                for chunk, score in semantic_results
            ]) if semantic_results else ""
            
        except Exception as e:
            semantic_context = ""
        
        # Build context string
        context_parts = []
        
        if semantic_context:
            context_parts.append(f"**Relevant Context:**\n{semantic_context}")
        
        if efc_result.score > 4:
            context_parts.append(f"\n**EFC Framework Analysis:**\n{efc_result.reasoning}")
        
        if not context_parts:
            context_parts.append("No additional context available from knowledge base.")
        
        return {
            "context": "\n\n".join(context_parts),
            "efc_detected": efc_result.score > 0,
            "efc_score": efc_result.score,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "context": f"Context retrieval temporarily unavailable.",
            "error": str(e),
            "status": "error"
        }


@router.post("/context", response_model=MstyContextResponse)
async def get_live_context(request: MstyContextRequest):
    """
    Get live context for current conversation.
    
    Retrieves:
    - Relevant semantic context from memory
    - EFC pattern detection
    - Related concepts from knowledge graph
    - Conversation-aware recommendations
    """
    try:
        memory_system, efc_engine = get_memory_system()
        
        # Detect EFC patterns
        efc_result = efc_engine.detect_efc_pattern(
            question=request.query,
            domain=request.domain
        )
        
        # Get semantic context
        context_query = request.query
        if request.conversation_history:
            # Augment query with recent conversation
            recent = request.conversation_history[-3:]
            conversation_text = " ".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent
            ])
            context_query = f"{conversation_text}\n\nCurrent: {request.query}"
        
        # Retrieve from memory
        try:
            # Use semantic search from SMM
            semantic_results = memory_system.smm.search_context(
                query=request.query,
                k=5
            )
            
            semantic_context = "\n\n".join([
                chunk.text for chunk, score in semantic_results
            ]) if semantic_results else ""
            
        except Exception as e:
            semantic_context = ""
            print(f"Memory retrieval failed: {e}")
        
        # Get related concepts from graph
        related_concepts = []
        if memory_system.graph:
            try:
                # Extract key concepts from query
                words = request.query.lower().split()
                key_words = [w for w in words if len(w) > 5][:3]
                
                for word in key_words:
                    neighbors = memory_system.graph.find_neighbors(word, max_depth=1)
                    related_concepts.extend(neighbors[:5])
            except:
                pass
        
        # Determine if EFC should be used
        should_use_efc = efc_engine.should_augment_with_efc(efc_result)
        
        return MstyContextResponse(
            query=request.query,
            context={
                "semantic": semantic_context,
                "efc_patterns": efc_result.detected_patterns,
                "reasoning_traces": [],
                "memory_layers": ["semantic_mesh"]
            },
            efc_pattern_detected=efc_result.score > 0,
            efc_score=efc_result.score,
            efc_reasoning=efc_result.reasoning,
            should_use_efc=should_use_efc,
            related_concepts=list(set(related_concepts))[:10],
            conversation_context=conversation_text if request.conversation_history else None,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.post("/query", response_model=MstyQueryResponse)
async def enhanced_query(request: MstyQueryRequest):
    """
    Enhanced query with automatic EFC augmentation.
    
    This is the main endpoint Msty AI should use for queries.
    It automatically detects when to use EFC and augments responses.
    """
    try:
        memory_system, efc_engine = get_memory_system()
        
        # Detect EFC patterns
        efc_result = efc_engine.detect_efc_pattern(
            question=request.query,
            domain=request.domain
        )
        
        # Determine strategy
        use_efc = request.use_efc_augmentation and efc_engine.should_augment_with_efc(efc_result)
        
        # Retrieve context
        try:
            semantic_results = memory_system.smm.search_context(
                query=request.query,
                k=5
            )
            
            semantic_context = "\n\n".join([
                chunk.text for chunk, score in semantic_results
            ]) if semantic_results else ""
            
        except Exception as e:
            semantic_context = ""
            print(f"Memory retrieval failed: {e}")
        
        # Build response
        answer_parts = []
        
        # Add semantic context
        if semantic_context:
            answer_parts.append(semantic_context)
        
        # Add EFC augmentation if relevant
        if use_efc:
            efc_context = f"\n\n**EFC Framework Analysis:**\n{efc_result.reasoning}"
            answer_parts.append(efc_context)
        
        answer = "\n\n".join(answer_parts)
        
        # Extract sources
        sources = ["semantic_mesh"]
        if use_efc:
            sources.append("efc_engine")
        
        return MstyQueryResponse(
            answer=answer,
            efc_used=use_efc,
            context_retrieved=bool(semantic_context),
            patterns_detected=efc_result.detected_patterns,
            confidence=efc_result.score / 8.0 if use_efc else 0.5,  # Normalized confidence
            sources=sources,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.post("/feedback")
async def record_feedback(request: MstyFeedbackRequest):
    """
    Record user feedback on response quality.
    
    This enables the adaptive learning system to improve.
    """
    try:
        memory_system, efc_engine = get_memory_system()
        
        # Detect what patterns were in the original query
        efc_result = efc_engine.detect_efc_pattern(
            question=request.query,
            domain=request.domain
        )
        
        # Record feedback for learning
        if efc_engine.learner and efc_result.score > 0:
            efc_engine.provide_feedback(
                question=request.query,
                domain=request.domain or "general",
                efc_score=efc_result.score,
                detected_patterns=efc_result.detected_patterns,
                was_helpful=request.was_helpful
            )
        
        return {
            "status": "ok",
            "message": "Feedback recorded",
            "learning_active": efc_engine.learner is not None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback recording failed: {str(e)}")


@router.get("/patterns")
async def get_active_patterns(user_id: Optional[str] = None, domain: Optional[str] = None):
    """
    Get active EFC patterns for user or domain.
    
    Shows what patterns the system has learned are effective.
    """
    try:
        memory_system, efc_engine = get_memory_system()
        
        if not efc_engine.learner:
            return {"patterns": [], "message": "Learning system not active"}
        
        patterns = []
        
        if domain:
            # Get domain-specific patterns
            if domain in efc_engine.learner.domains:
                domain_data = efc_engine.learner.domains[domain]
                patterns = [
                    {
                        "pattern": p.pattern,
                        "occurrences": p.occurrences,
                        "success_rate": p.success_rate,
                        "last_used": p.last_used
                    }
                    for p in domain_data.learned_patterns.values()
                    if p.active
                ]
        else:
            # Get all patterns
            for domain_name, domain_data in efc_engine.learner.domains.items():
                for pattern in domain_data.learned_patterns.values():
                    if pattern.active:
                        patterns.append({
                            "domain": domain_name,
                            "pattern": pattern.pattern,
                            "occurrences": pattern.occurrences,
                            "success_rate": pattern.success_rate,
                            "last_used": pattern.last_used
                        })
        
        return {
            "patterns": patterns,
            "total": len(patterns),
            "domain_filter": domain
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Check if the context API is operational.
    """
    try:
        memory_system, efc_engine = get_memory_system()
        
        return {
            "status": "operational",
            "memory_system": "active",
            "efc_engine": "active",
            "learning_enabled": efc_engine.learner is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
