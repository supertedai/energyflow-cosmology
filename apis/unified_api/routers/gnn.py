# apis/unified_api/routers/gnn.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter(tags=["GNN"])

# Optional torch import
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Load GNN artifacts
GNN_OUTPUT_DIR = Path(__file__).resolve().parents[3] / "symbiose_gnn_output"
NODE_EMBEDDINGS_PATH = GNN_OUTPUT_DIR / "node_embeddings.json"
NODE_MAPPING_PATH = GNN_OUTPUT_DIR / "node_mapping.json"
MODEL_PATH = GNN_OUTPUT_DIR / "gnn_model.pt"

# Cache loaded artifacts
_node_embeddings = None
_node_mapping = None
_model = None


def load_artifacts():
    """Load GNN artifacts on first request."""
    global _node_embeddings, _node_mapping, _model
    
    if _node_embeddings is not None:
        return
    
    # Load node embeddings
    if NODE_EMBEDDINGS_PATH.exists():
        with open(NODE_EMBEDDINGS_PATH) as f:
            _node_embeddings = json.load(f)
    
    # Load node mapping
    if NODE_MAPPING_PATH.exists():
        with open(NODE_MAPPING_PATH) as f:
            _node_mapping = json.load(f)
    
    # Load model (optional, for inference)
    if MODEL_PATH.exists():
        try:
            from symbiose_gnn.model import SymbioseGNN
            _model = SymbioseGNN(input_dim=64, hidden_dim=128, out_dim=64)
            _model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
            _model.eval()
        except Exception:
            _model = None


@router.get("/status")
def gnn_status():
    """
    Get GNN system status.
    """
    load_artifacts()
    
    # embeddings is a list of vectors, mapping is dict
    total_nodes = len(_node_embeddings) if _node_embeddings else 0
    emb_dim = len(_node_embeddings[0]) if _node_embeddings and len(_node_embeddings) > 0 else 0
    
    return {
        "status": "ok",
        "artifacts": {
            "node_embeddings": _node_embeddings is not None,
            "node_mapping": _node_mapping is not None,
            "model": _model is not None,
        },
        "stats": {
            "total_nodes": total_nodes,
            "embedding_dim": emb_dim,
        },
        "paths": {
            "embeddings": str(NODE_EMBEDDINGS_PATH),
            "mapping": str(NODE_MAPPING_PATH),
            "model": str(MODEL_PATH),
        }
    }


@router.get("/embed/{node_idx}")
def get_node_embedding(node_idx: int):
    """
    Get embedding for a specific node by index.
    """
    load_artifacts()
    
    if not _node_embeddings:
        raise HTTPException(
            status_code=503,
            detail="Node embeddings not available. Run 'python -m symbiose_gnn.embed' first."
        )
    
    if node_idx < 0 or node_idx >= len(_node_embeddings):
        raise HTTPException(
            status_code=404,
            detail=f"Node index {node_idx} out of range. Available: 0-{len(_node_embeddings)-1}"
        )
    
    # Get node ID from mapping if available
    node_id = _node_mapping.get(str(node_idx), f"node_{node_idx}") if _node_mapping else f"node_{node_idx}"
    
    return {
        "node_index": node_idx,
        "node_id": node_id,
        "embedding": _node_embeddings[node_idx],
        "dimension": len(_node_embeddings[node_idx])
    }


@router.get("/nodes")
def list_nodes(limit: int = 10):
    """
    List all nodes with embeddings.
    """
    load_artifacts()
    
    if not _node_embeddings:
        raise HTTPException(
            status_code=503,
            detail="Node embeddings not available."
        )
    
    # Build node list with IDs from mapping
    nodes = []
    for idx in range(min(limit, len(_node_embeddings))):
        node_id = _node_mapping.get(str(idx), f"node_{idx}") if _node_mapping else f"node_{idx}"
        nodes.append({"index": idx, "id": node_id})
    
    return {
        "total": len(_node_embeddings),
        "returned": len(nodes),
        "nodes": nodes
    }


@router.get("/similar/{node_idx}")
def find_similar_nodes(node_idx: int, top_k: int = 5):
    """
    Find most similar nodes based on embedding cosine similarity.
    """
    load_artifacts()
    
    if not _node_embeddings:
        raise HTTPException(status_code=503, detail="Embeddings not available")
    
    if node_idx < 0 or node_idx >= len(_node_embeddings):
        raise HTTPException(status_code=404, detail=f"Node index {node_idx} out of range")
    
    if not TORCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PyTorch not available. Install with: pip install torch"
        )
    
    # Get target embedding
    target_emb = torch.tensor(_node_embeddings[node_idx])
    
    # Compute similarities with all other nodes
    similarities = []
    for idx, other_emb in enumerate(_node_embeddings):
        if idx == node_idx:
            continue
        
        other_tensor = torch.tensor(other_emb)
        similarity = torch.nn.functional.cosine_similarity(
            target_emb.unsqueeze(0),
            other_tensor.unsqueeze(0)
        ).item()
        
        node_id = _node_mapping.get(str(idx), f"node_{idx}") if _node_mapping else f"node_{idx}"
        
        similarities.append({
            "node_index": idx,
            "node_id": node_id,
            "similarity": similarity
        })
    
    # Sort and return top-k
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    
    query_id = _node_mapping.get(str(node_idx), f"node_{node_idx}") if _node_mapping else f"node_{node_idx}"
    
    return {
        "query_node_index": node_idx,
        "query_node_id": query_id,
        "top_k": top_k,
        "results": similarities[:top_k]
    }
