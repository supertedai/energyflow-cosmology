# apis/unified_api/clients/gnn_client.py

"""
GNN-basert hybrid scoring for Graph-RAG.
Bruker strukturelle embeddings til å booste semantisk søk.
"""

from pathlib import Path
import json
from typing import List, Dict, Optional
import numpy as np

GNN_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "symbiose_gnn_output"
NODE_EMBEDDINGS_PATH = GNN_OUTPUT_DIR / "node_embeddings.json"
NODE_MAPPING_PATH = GNN_OUTPUT_DIR / "node_mapping.json"

# Cache
_node_embeddings: Optional[List[List[float]]] = None
_node_mapping: Optional[Dict[str, int]] = None
_reverse_mapping: Optional[Dict[int, str]] = None


def load_gnn_artifacts():
    """Lazy-load GNN embeddings og mapping."""
    global _node_embeddings, _node_mapping, _reverse_mapping
    
    if _node_embeddings is not None:
        return
    
    if NODE_EMBEDDINGS_PATH.exists():
        with open(NODE_EMBEDDINGS_PATH) as f:
            _node_embeddings = json.load(f)
    
    if NODE_MAPPING_PATH.exists():
        with open(NODE_MAPPING_PATH) as f:
            _node_mapping = json.load(f)
            # Create reverse mapping (int idx -> node_id string)
            _reverse_mapping = {int(v): k for k, v in _node_mapping.items()}


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a, b) / (norm_a * norm_b))


def get_node_embedding(node_id: str) -> Optional[List[float]]:
    """
    Hent GNN-embedding for en gitt node_id (Neo4j node ID).
    """
    load_gnn_artifacts()
    
    if not _node_embeddings or not _node_mapping:
        return None
    
    # Map node_id -> index
    idx = _node_mapping.get(node_id)
    if idx is None:
        return None
    
    if idx < 0 or idx >= len(_node_embeddings):
        return None
    
    return _node_embeddings[idx]


def compute_structural_similarity(node_id: str, reference_ids: List[str]) -> float:
    """
    Beregn gjennomsnittlig strukturell likhet mellom en node og en liste
    av referansenoder (f.eks. query-hits fra Neo4j).
    
    Returnerer score 0.0-1.0, der 1.0 = høy strukturell likhet.
    """
    target_emb = get_node_embedding(node_id)
    if target_emb is None:
        return 0.0
    
    similarities = []
    for ref_id in reference_ids:
        ref_emb = get_node_embedding(ref_id)
        if ref_emb is not None:
            sim = cosine_similarity(target_emb, ref_emb)
            similarities.append(sim)
    
    if not similarities:
        return 0.0
    
    # Return mean similarity
    return float(np.mean(similarities))


def find_k_nearest_neighbors(node_id: str, k: int = 5) -> List[Dict]:
    """
    Finn k nærmeste naboer basert på GNN-embeddings.
    """
    load_gnn_artifacts()
    
    if not _node_embeddings or not _node_mapping or not _reverse_mapping:
        return []
    
    target_emb = get_node_embedding(node_id)
    if target_emb is None:
        return []
    
    # Compute similarities with all nodes
    similarities = []
    for idx, emb in enumerate(_node_embeddings):
        neighbor_id = _reverse_mapping.get(idx, f"node_{idx}")
        if neighbor_id == node_id:
            continue  # Skip self
        
        sim = cosine_similarity(target_emb, emb)
        similarities.append({
            "node_id": neighbor_id,
            "similarity": sim
        })
    
    # Sort and return top k
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    return similarities[:k]


def hybrid_score(
    semantic_score: float,
    structural_score: float,
    alpha: float = 0.7
) -> float:
    """
    Hybrid scoring funksjon.
    
    hybrid = alpha * semantic + (1 - alpha) * structural
    
    Args:
        semantic_score: Qdrant cosine score (0.0-1.0)
        structural_score: GNN embedding similarity (0.0-1.0)
        alpha: Vekt for semantisk score (0.7 = 70% semantikk, 30% struktur)
    
    Returns:
        Hybrid score 0.0-1.0
    """
    return alpha * semantic_score + (1.0 - alpha) * structural_score
