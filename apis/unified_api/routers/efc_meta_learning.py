"""
EFC Meta-Learning Router
Layer 9 integration with adaptive pattern learning
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from tools.efc_theory_engine import EFCTheoryEngine
from tools.neo4j_graph_layer import Neo4jGraphLayer
from tools.canonical_memory_core import CanonicalMemoryCore
from tools.semantic_mesh_memory import SemanticMeshMemory

router = APIRouter()

# Global instances (initialized on first use)
_efc_engine = None
_graph = None
_cmc = None
_smm = None


def get_efc_engine():
    """Lazy initialization of EFC engine."""
    global _efc_engine, _graph, _cmc, _smm
    
    if _efc_engine is None:
        # Initialize dependencies
        _graph = Neo4jGraphLayer()
        _cmc = CanonicalMemoryCore()
        _smm = SemanticMeshMemory()
        
        # Initialize EFC engine with learning enabled
        _efc_engine = EFCTheoryEngine(
            cmc=_cmc,
            smm=_smm,
            graph=_graph,
            enable_learning=True,
            learning_file="efc_pattern_learning_production.json"
        )
    
    return _efc_engine


# Request/Response models
class PatternDetectionRequest(BaseModel):
    question: str
    domain: Optional[str] = None


class PatternDetectionResponse(BaseModel):
    score: float
    relevance_level: str
    language_cues: int
    structural_cues: int
    logical_cues: int
    detected_patterns: List[str]
    reasoning: str
    should_augment: bool
    should_override: bool


class FeedbackRequest(BaseModel):
    question: str
    domain: str
    efc_score: float
    detected_patterns: List[str]
    was_helpful: bool


class UniversalPattern(BaseModel):
    pattern: str
    domains: List[str]
    total_occurrences: int
    success_rate: float
    confidence: float
    discovered_at: str


class LearningStats(BaseModel):
    total_observations: int
    total_patterns: int
    active_patterns: int
    domains_learned: int
    universal_patterns: int
    domain_stats: Dict


@router.post("/detect-pattern", response_model=PatternDetectionResponse)
async def detect_efc_pattern(request: PatternDetectionRequest):
    """
    Detect EFC patterns in a question.
    
    Returns pattern relevance score and recommendations for how to use EFC.
    """
    try:
        engine = get_efc_engine()
        
        result = engine.detect_efc_pattern(
            question=request.question,
            domain=request.domain
        )
        
        return PatternDetectionResponse(
            score=result.score,
            relevance_level=result.relevance_level,
            language_cues=result.language_cues,
            structural_cues=result.structural_cues,
            logical_cues=result.logical_cues,
            detected_patterns=result.detected_patterns,
            reasoning=result.reasoning,
            should_augment=engine.should_augment_with_efc(result),
            should_override=engine.should_override_with_efc(result)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern detection failed: {str(e)}")


@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest):
    """
    Provide feedback on EFC pattern usage.
    
    This enables the adaptive learning system to improve over time.
    """
    try:
        engine = get_efc_engine()
        
        engine.provide_feedback(
            question=request.question,
            domain=request.domain,
            efc_score=request.efc_score,
            detected_patterns=request.detected_patterns,
            was_helpful=request.was_helpful
        )
        
        return {"status": "ok", "message": "Feedback recorded"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback recording failed: {str(e)}")


@router.get("/universal-patterns", response_model=List[UniversalPattern])
async def get_universal_patterns():
    """
    Get universal EFC patterns discovered across multiple domains.
    
    These are patterns that have been validated in ≥3 domains.
    """
    try:
        engine = get_efc_engine()
        
        if not engine.learner:
            return []
        
        patterns = engine.learner.get_universal_patterns()
        
        return [
            UniversalPattern(
                pattern=p.pattern,
                domains=list(p.domains),
                total_occurrences=p.total_occurrences,
                success_rate=p.success_rate,
                confidence=p.confidence,
                discovered_at=p.discovered_at
            )
            for p in patterns
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get universal patterns: {str(e)}")


@router.get("/learning-stats", response_model=LearningStats)
async def get_learning_stats():
    """
    Get statistics about the adaptive learning system.
    
    Shows how many patterns learned, domains covered, etc.
    """
    try:
        engine = get_efc_engine()
        
        if not engine.learner:
            return LearningStats(
                total_observations=0,
                total_patterns=0,
                active_patterns=0,
                domains_learned=0,
                universal_patterns=0,
                domain_stats={}
            )
        
        stats = engine.learner.get_stats()
        universal_count = len(engine.learner.get_universal_patterns())
        
        return LearningStats(
            total_observations=stats["total_observations"],
            total_patterns=stats["total_patterns"],
            active_patterns=stats["active_patterns"],
            domains_learned=stats["domains_learned"],
            universal_patterns=universal_count,
            domain_stats=stats["domain_stats"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning stats: {str(e)}")


@router.get("/domain/{domain_name}/threshold")
async def get_domain_threshold(domain_name: str):
    """
    Get the threshold adjustment for a specific domain.
    
    Negative = easier to activate (domain has high success rate)
    Positive = harder to activate (domain needs more validation)
    """
    try:
        engine = get_efc_engine()
        
        if not engine.learner:
            return {"domain": domain_name, "threshold_adjustment": 0.0}
        
        adjustment = engine.learner.get_threshold_adjustment(domain_name)
        
        domain_stats = None
        if domain_name in engine.learner.domains:
            stats = engine.learner.domains[domain_name]
            domain_stats = {
                "observations": stats.observations,
                "successful_uses": stats.successful_efc_uses,
                "success_rate": stats.successful_efc_uses / stats.observations if stats.observations > 0 else 0,
                "average_score": stats.average_efc_score
            }
        
        return {
            "domain": domain_name,
            "threshold_adjustment": adjustment,
            "stats": domain_stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get domain threshold: {str(e)}")


@router.post("/validate-claim")
async def validate_claim(question: str, claim: str):
    """
    Validate a claim against EFC principles.
    
    Returns which principles support or constrain the claim.
    """
    try:
        engine = get_efc_engine()
        
        validation = engine.check_claim(claim)
        
        return {
            "claim": claim,
            "question_context": question,
            "validation": {
                "supports": [p.name for p in validation.supports],
                "constrains": [p.name for p in validation.constrains],
                "neutral": [p.name for p in validation.neutral],
                "verdict": validation.verdict
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim validation failed: {str(e)}")
