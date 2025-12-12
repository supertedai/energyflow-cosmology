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
EFC_NODES_PATH = GNN_OUTPUT_DIR / "efc_nodes_latest.jsonl"
EFC_METADATA_PATH = GNN_OUTPUT_DIR / "efc_metadata_latest.json"
MODEL_PATH = GNN_OUTPUT_DIR / "efc_gnn_best.pt"

# Cache loaded artifacts
_node_embeddings = None
_efc_nodes = None
_efc_metadata = None
_model = None


def load_artifacts():
    """Load GNN artifacts on first request."""
    global _node_embeddings, _efc_nodes, _efc_metadata, _model
    
    if _node_embeddings is not None:
        return
    
    # Load node embeddings
    if NODE_EMBEDDINGS_PATH.exists():
        with open(NODE_EMBEDDINGS_PATH) as f:
            _node_embeddings = json.load(f)
    
    # Load EFC nodes metadata
    if EFC_NODES_PATH.exists():
        import jsonlines
        _efc_nodes = []
        with jsonlines.open(EFC_NODES_PATH) as reader:
            for obj in reader:
                _efc_nodes.append(obj)
    
    # Load EFC metadata
    if EFC_METADATA_PATH.exists():
        with open(EFC_METADATA_PATH) as f:
            _efc_metadata = json.load(f)
    
    # Load trained GNN model
    if MODEL_PATH.exists() and TORCH_AVAILABLE:
        try:
            _model = torch.load(MODEL_PATH, map_location="cpu")
        except Exception as e:
            print(f"⚠️  Failed to load GNN model: {e}")
            _model = None


@router.get("/status")
def gnn_status():
    """
    Get GNN system status and statistics.
    """
    load_artifacts()
    
    # Check if GNN embeddings dict exists
    total_concepts = len(_node_embeddings) if _node_embeddings else 0
    
    return {
        "status": "ok" if _model is not None else "trained_but_not_loaded",
        "artifacts": {
            "node_embeddings": NODE_EMBEDDINGS_PATH.exists(),
            "efc_nodes": EFC_NODES_PATH.exists(),
            "efc_metadata": EFC_METADATA_PATH.exists(),
            "model": MODEL_PATH.exists(),
        },
        "stats": {
            "total_nodes": len(_efc_nodes) if _efc_nodes else 0,
            "total_concepts": total_concepts,
            "metadata": _efc_metadata if _efc_metadata else {}
        },
        "paths": {
            "embeddings": str(NODE_EMBEDDINGS_PATH),
            "nodes": str(EFC_NODES_PATH),
            "metadata": str(EFC_METADATA_PATH),
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


@router.post("/query")
def query_concepts(request: dict):
    """
    Query GNN for concept similarity by text.
    
    Request body:
    {
        "query": "energy flow",
        "top_k": 5
    }
    """
    query_text = request.get("query", "")
    top_k = request.get("top_k", 5)
    
    if not query_text:
        raise HTTPException(status_code=400, detail="query is required")
    
    # Use gnn_scoring module for text-to-concept matching
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
    
    try:
        from gnn_scoring import get_gnn_similarity_score
        
        result = get_gnn_similarity_score(
            private_chunk_text=query_text,
            top_k=top_k,
            chunk_domain="theory"  # Force theory domain for GNN usage
        )
        
        if not result.get("available"):
            raise HTTPException(
                status_code=503,
                detail=result.get("reason", "GNN not available")
            )
        
        return {
            "query": query_text,
            "gnn_similarity": result.get("gnn_similarity", 0.0),
            "confidence": result.get("confidence", 0.0),
            "matches": result.get("top_matches", [])
        }
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="GNN scoring module not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GNN query error: {str(e)}"
        )
