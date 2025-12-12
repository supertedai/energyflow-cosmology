#!/usr/bin/env python3
"""
gnn_scoring.py - GNN-based Scoring for Intention Gate
=====================================================

Purpose: Add GNN structural similarity as a feature for intention_gate

This module:
- Loads GNN embeddings from trained EFC model
- Compares Private Memory chunks to EFC structure
- Returns "structural stability score" (0-1)
- Used as ADDITIONAL SIGNAL only (not decision maker)

Safety:
- Read-only (no writes)
- Optional (works even if GNN not trained)
- Doesn't override human feedback
- Just adds context: "how similar to stable EFC patterns?"

Usage:
    from gnn_scoring import get_gnn_similarity_score
    
    score = get_gnn_similarity_score(
        private_chunk_text="The entropy gradient drives cosmic evolution",
        top_k=5
    )
    # Returns: {"gnn_similarity": 0.87, "confidence": 0.92}
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import openai

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Use absolute paths to work from any directory
_BASE_DIR = Path(__file__).resolve().parent.parent
GNN_EMBEDDINGS_PATH = _BASE_DIR / "symbiose_gnn_output/node_embeddings.json"
EFC_NODES_PATH = _BASE_DIR / "symbiose_gnn_output/efc_nodes_latest.jsonl"
EFC_METADATA_PATH = _BASE_DIR / "symbiose_gnn_output/efc_metadata_latest.json"
PROJECTION_MATRIX_PATH = _BASE_DIR / "symbiose_gnn_output/projection_matrix.npy"

# Cache for loaded data
_gnn_cache = {
    'embeddings': None,
    'nodes': None,
    'metadata': None,
    'projection_matrix': None
}

# Domains where GNN scoring should be skipped
# (personal facts don't need EFC structural similarity)
SKIP_GNN_DOMAINS = {
    "identity",      # Names, personal info
    "preference",    # Likes, dislikes
    "private_life",  # Family, relationships
    "small_talk"     # Casual conversation
}

# ============================================================
# GNN SIMILARITY SCORING
# ============================================================

def get_gnn_similarity_score(
    private_chunk_text: str,
    top_k: int = 5,
    chunk_domain: str = None
) -> Dict:
    """
    Calculate how similar a Private chunk is to stable EFC concepts
    
    HYBRID TWO-STAGE APPROACH:
    1. String/fuzzy filter → find relevant EFC concepts (50 candidates)
    2. Embed both in SAME SPACE (OpenAI) → semantic similarity
    3. Use GNN structure as weight adjustment only
    
    This avoids the modality break: GNN embeddings are structural, not semantic.
    
    Args:
        private_chunk_text: Text from Private Memory chunk
        top_k: Number of top EFC concepts to compare with
        chunk_domain: Domain/category of chunk (identity, preference, theory, etc.)
        
    Returns:
        {
            "gnn_similarity": float (0-1),  # Semantic similarity to EFC (same space)
            "confidence": float (0-1),      # How confident (based on top-k agreement)
            "top_matches": list,            # Top matching EFC concepts
            "available": bool               # Whether GNN is available
        }
    """
    # Skip GNN for personal/non-theory domains
    if chunk_domain and chunk_domain in SKIP_GNN_DOMAINS:
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.0,
            "top_matches": [],
            "available": False,
            "reason": f"Skipped: domain '{chunk_domain}' not applicable for GNN"
        }
    
    # Auto-detect personal content if domain not provided
    if not chunk_domain and _is_personal_content(private_chunk_text):
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.0,
            "top_matches": [],
            "available": False,
            "reason": "Skipped: detected personal/identity content"
        }
    
    # Check if GNN is available
    if not _is_gnn_available():
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.0,
            "top_matches": [],
            "available": False,
            "reason": "GNN not trained yet"
        }
    
    # Load GNN data (cached)
    try:
        gnn_embeddings, nodes, metadata = _load_gnn_data()
    except Exception as e:
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.0,
            "top_matches": [],
            "available": False,
            "reason": f"Failed to load GNN: {str(e)}"
        }
    
    # ============================================================
    # STAGE 1: STRING/FUZZY FILTER
    # Find EFC concepts that might be relevant (domain anchoring)
    # ============================================================
    
    candidate_concepts = _find_candidate_concepts(
        private_chunk_text,
        nodes,
        max_candidates=50
    )
    
    if not candidate_concepts:
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.3,
            "top_matches": [],
            "available": True,
            "reason": "No EFC concepts matched via string filter"
        }
    
    # ============================================================
    # STAGE 2: SEMANTIC SIMILARITY IN SAME SPACE
    # Embed both chunk and candidates with OpenAI → compare in same space
    # ============================================================
    
    try:
        # Embed the private chunk
        query_embedding = _get_text_embedding(private_chunk_text)
        
        # Embed candidate concepts (batch for efficiency)
        candidate_texts = [c['name'] for c in candidate_concepts]
        candidate_embeddings = _get_batch_embeddings(candidate_texts)
        
    except Exception as e:
        return {
            "gnn_similarity": 0.0,
            "confidence": 0.0,
            "top_matches": [],
            "available": False,
            "reason": f"Failed to embed text: {str(e)}"
        }
    
    # Calculate semantic similarity (same space = meaningful)
    similarities = []
    for i, candidate in enumerate(candidate_concepts):
        semantic_sim = _cosine_similarity(query_embedding, candidate_embeddings[i])
        
        # Weight by GNN structure (centrality boost)
        degree = candidate.get('degree', 0)
        centrality_weight = 1.0 + (degree / 1000.0)  # Boost for high-degree nodes
        
        weighted_sim = semantic_sim * centrality_weight
        
        similarities.append({
            'concept': candidate['name'],
            'semantic_similarity': float(semantic_sim),
            'weighted_similarity': float(weighted_sim),
            'degree': degree,
            'string_match_score': candidate.get('match_score', 0.0)
        })
    
    # Sort by weighted similarity
    similarities.sort(key=lambda x: x['weighted_similarity'], reverse=True)
    
    # Get top-k matches
    top_matches = similarities[:top_k]
    
    # Calculate aggregate score
    # Use exponential decay: first match counts most
    weights = np.exp(-0.5 * np.arange(len(top_matches)))
    weights = weights / weights.sum()
    
    top_sims = [m['semantic_similarity'] for m in top_matches]
    gnn_similarity = float(np.sum(np.array(top_sims) * weights))
    
    # Confidence: how consistent are the top matches?
    if len(top_sims) > 1:
        sim_variance = np.var(top_sims)
        confidence = 1.0 - min(sim_variance * 2, 1.0)
    else:
        confidence = 0.5
    
    return {
        "gnn_similarity": round(gnn_similarity, 3),
        "confidence": round(confidence, 3),
        "top_matches": top_matches[:3],  # Return top 3 for display
        "available": True
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _is_gnn_available() -> bool:
    """Check if GNN model has been trained"""
    return (
        GNN_EMBEDDINGS_PATH.exists() and
        EFC_NODES_PATH.exists() and
        EFC_METADATA_PATH.exists()
    )


def _load_gnn_data():
    """Load GNN embeddings and nodes (with caching)"""
    global _gnn_cache
    
    # Return cached data if available
    if _gnn_cache['embeddings'] is not None:
        return (
            _gnn_cache['embeddings'],
            _gnn_cache['nodes'],
            _gnn_cache['metadata']
        )
    
    # Load embeddings
    with open(GNN_EMBEDDINGS_PATH, 'r') as f:
        embeddings = np.array(json.load(f))
    
    # Load nodes
    nodes = []
    with open(EFC_NODES_PATH, 'r') as f:
        for line in f:
            nodes.append(json.loads(line))
    
    # Load metadata
    with open(EFC_METADATA_PATH, 'r') as f:
        metadata = json.load(f)
    
    # Cache for future calls
    _gnn_cache['embeddings'] = embeddings
    _gnn_cache['nodes'] = nodes
    _gnn_cache['metadata'] = metadata
    
    return embeddings, nodes, metadata


def _get_text_embedding(text: str) -> np.ndarray:
    """Get OpenAI embedding for text"""
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=text[:8000]  # Truncate if too long
    )
    return np.array(response.data[0].embedding)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors (same dimension)"""
    # Normalize
    a = a / (np.linalg.norm(a) + 1e-8)
    b = b / (np.linalg.norm(b) + 1e-8)
    
    return float(np.dot(a, b))


def _is_personal_content(text: str) -> bool:
    """
    Detect if text is personal/identity content (skip GNN for these)
    
    Simple heuristic: contains personal pronouns + common identity markers
    """
    text_lower = text.lower()
    
    # Personal indicators
    personal_markers = [
        "my name is", "jeg heter", "i am", "jeg er",
        "my wife", "min kone", "my husband", "min mann",
        "my family", "min familie", "i like", "jeg liker",
        "born in", "født", "live in", "bor i"
    ]
    
    return any(marker in text_lower for marker in personal_markers)


def _find_candidate_concepts(
    query_text: str,
    nodes: list,
    max_candidates: int = 50
) -> list:
    """
    STAGE 1: String/fuzzy filter to find relevant EFC concepts
    
    Uses:
    - Substring matching
    - Token overlap
    - Fuzzy matching (simple)
    
    Returns list of candidate concepts with match scores.
    """
    query_lower = query_text.lower()
    query_tokens = set(query_lower.split())
    
    candidates = []
    
    for node in nodes:
        concept_name = node.get('name', '').lower()
        
        # Skip empty names
        if not concept_name:
            continue
        
        # Calculate match score
        match_score = 0.0
        
        # 1. Exact substring match (strongest signal)
        if concept_name in query_lower or query_lower in concept_name:
            match_score += 1.0
        
        # 2. Token overlap
        concept_tokens = set(concept_name.split())
        if concept_tokens and query_tokens:
            overlap = len(concept_tokens & query_tokens)
            match_score += overlap / max(len(concept_tokens), len(query_tokens))
        
        # 3. Key term matching (if available)
        key_terms = node.get('key_terms', [])
        if isinstance(key_terms, list):
            for term in key_terms:
                if term.lower() in query_lower:
                    match_score += 0.5
        
        # 4. Boost for high-degree nodes (central concepts)
        degree = node.get('degree', 0)
        if degree > 10:
            match_score *= 1.2  # 20% boost for well-connected concepts
        
        # Only include if some match found
        if match_score > 0.0:
            candidates.append({
                'name': node.get('name', 'Unknown'),
                'degree': degree,
                'match_score': match_score,
                'node_data': node
            })
    
    # Sort by match score
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Return top N candidates
    return candidates[:max_candidates]


def _get_batch_embeddings(texts: list) -> list:
    """
    Get OpenAI embeddings for multiple texts (batch for efficiency)
    
    Returns list of numpy arrays.
    """
    if not texts:
        return []
    
    # Truncate texts if too long
    truncated_texts = [t[:8000] for t in texts]
    
    # Call OpenAI API
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=truncated_texts
    )
    
    # Extract embeddings
    embeddings = [np.array(item.embedding) for item in response.data]
    
    return embeddings


# NOTE: Projection functions removed - no longer needed
# We now use hybrid approach: string filter + same-space semantic similarity
# GNN structure used only as weight adjustment, not for direct embedding comparison


# ============================================================
# INTEGRATION WITH INTENTION GATE
# ============================================================

def add_gnn_signal_to_scores(
    chunk_text: str,
    existing_scores: Dict,
    manual_feedback_count: int = 0,
    chunk_domain: str = None
) -> Dict:
    """
    Enhance intention_gate scores with GNN similarity
    
    This adds:
    - gnn_similarity: structural similarity to EFC (0-1)
    - gnn_confidence: how confident the GNN score is
    - gnn_top_matches: what EFC concepts this resembles
    
    The GNN score is used as:
    - Additional confidence booster (if high similarity)
    - Risk reducer (stable structure = lower risk)
    - NOT as replacement for human feedback
    
    SAFETY GATES:
    - Risk downgrade ONLY if manual_feedback_count >= 1
    - Risk downgrade ONLY if existing confidence >= 0.6
    - GNN skipped for personal/identity content
    
    Args:
        chunk_text: Text from Private Memory chunk
        existing_scores: Scores from intention_gate.calculate_scores()
        manual_feedback_count: Number of manual feedback signals
        chunk_domain: Domain/category of chunk
        
    Returns:
        Enhanced scores dict with GNN fields added
    """
    gnn_result = get_gnn_similarity_score(
        chunk_text,
        top_k=5,
        chunk_domain=chunk_domain
    )
    
    # Add GNN fields to existing scores
    enhanced_scores = existing_scores.copy()
    enhanced_scores['gnn_similarity'] = gnn_result['gnn_similarity']
    enhanced_scores['gnn_confidence'] = gnn_result['confidence']
    enhanced_scores['gnn_available'] = gnn_result['available']
    enhanced_scores['gnn_top_matches'] = gnn_result.get('top_matches', [])
    
    # If GNN shows high similarity to stable EFC concepts, adjust risk
    # BUT ONLY if we have manual feedback to validate
    if (gnn_result['available'] and
        gnn_result['gnn_similarity'] > 0.7 and
        manual_feedback_count >= 1 and  # ⚠️ SAFETY: Require human validation
        existing_scores['confidence'] >= 0.6):  # ⚠️ SAFETY: Require signal confidence
        
        # High GNN similarity = resembles stable EFC structure
        # This can reduce risk if other signals are positive
        if enhanced_scores['importance'] > 0.6 and not enhanced_scores['conflict']:
            # Downgrade risk from high -> medium or medium -> low
            if enhanced_scores['risk'] == 'high':
                enhanced_scores['risk'] = 'medium'
                enhanced_scores['quality_flags'].append('gnn_similarity_boost')
            elif enhanced_scores['risk'] == 'medium':
                enhanced_scores['risk'] = 'low'
                enhanced_scores['quality_flags'].append('gnn_similarity_boost')
    
    # If GNN shows low similarity, flag for review
    if gnn_result['available'] and gnn_result['gnn_similarity'] < 0.3:
        if 'low_gnn_similarity' not in enhanced_scores['quality_flags']:
            enhanced_scores['quality_flags'].append('low_gnn_similarity')
    
    return enhanced_scores


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    # Test GNN scoring
    test_chunks = [
        "The entropy gradient drives cosmic evolution through energy flow",
        "I like pizza and movies",
        "Spacetime distortion emerges from entropy field dynamics",
        "My name is Morten and I work on EFC theory"
    ]
    
    print("🧠 Testing GNN Similarity Scoring\n")
    
    for chunk in test_chunks:
        print(f"Text: {chunk[:60]}...")
        result = get_gnn_similarity_score(chunk, top_k=3)
        
        if result['available']:
            print(f"  GNN Similarity: {result['gnn_similarity']:.3f}")
            print(f"  Confidence: {result['confidence']:.3f}")
            print(f"  Top matches:")
            for m in result['top_matches'][:3]:
                print(f"    - {m['concept']} (semantic: {m['semantic_similarity']:.3f}, weighted: {m['weighted_similarity']:.3f})")
        else:
            print(f"  GNN not available: {result.get('reason', 'Unknown')}")
        
        print()
