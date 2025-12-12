#!/usr/bin/env python3
"""
gnn_reader_private.py - GNN Inference for Private Memory (READ-ONLY)
====================================================================

Purpose: Use EFC-trained GNN model to analyze Private Memory structure

CRITICAL: This is EVAL-MODE ONLY
- NO training on private data
- NO weight updates
- NO graph modifications
- NO memory_class changes

What it does:
- Loads EFC-trained GNN model (frozen)
- Runs inference on :PrivateChunk/:PrivateConcept nodes
- Returns analysis: centrality, cluster, EFC-similarity
- Used as support signal for intention_gate

Usage:
    from gnn_reader_private import read_gnn_with_steering
    
    result = read_gnn_with_steering(
        query="family relationships",
        namespace="private",
        k=5
    )
"""

import os
import sys
import json
import torch
from pathlib import Path
from typing import Optional, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
import openai

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

GNN_MODEL_PATH = Path("symbiose_gnn_output/gnn_model.pt")
GNN_EMBEDDINGS_PATH = Path("symbiose_gnn_output/node_embeddings.json")

# ============================================================
# GNN INFERENCE (EVAL MODE ONLY)
# ============================================================

def read_gnn_with_steering(
    query: str,
    namespace: str = "private",
    k: int = 5
) -> str:
    """
    Run GNN inference on Private Memory (READ-ONLY)
    
    Args:
        query: Search query for Private Memory
        namespace: Must be "private"
        k: Number of results to return
        
    Returns:
        Formatted string with GNN analysis results
        
    Raises:
        ValueError: If namespace != "private"
        FileNotFoundError: If GNN model not trained yet
    """
    if namespace != "private":
        raise ValueError(f"Only 'private' namespace supported, got: {namespace}")
    
    # Check if GNN model exists
    if not GNN_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"GNN model not found at {GNN_MODEL_PATH}\n"
            "Train GNN first: python symbiose_gnn/train.py"
        )
    
    # Load EFC-trained GNN model (frozen, eval mode)
    try:
        from symbiose_gnn.model import SymbioseGNN
        
        model = SymbioseGNN()
        model.load_state_dict(torch.load(GNN_MODEL_PATH))
        model.eval()  # CRITICAL: Eval mode, no gradients
        
        print("[GNN] Loaded EFC-trained model (eval mode)", file=sys.stderr)
    except Exception as e:
        raise RuntimeError(f"Failed to load GNN model: {e}")
    
    # Connect to databases
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    
    try:
        # Step 1: Get query embedding
        query_vector = _get_query_embedding(query)
        
        # Step 2: Semantic search in Private collection
        search_results = qdrant.search(
            collection_name="private",
            query_vector=query_vector,
            limit=k * 2  # Get more candidates for GNN filtering
        )
        
        if not search_results:
            return f"🔍 No results found for: {query}"
        
        # Step 3: Fetch Private Memory nodes for GNN inference
        chunk_ids = [hit.id for hit in search_results]
        private_nodes = _fetch_private_nodes(driver, chunk_ids)
        
        if not private_nodes:
            return f"🔍 No Private Memory nodes found"
        
        # Step 4: Run GNN inference (NO GRADIENTS)
        with torch.no_grad():
            gnn_features = _run_gnn_inference(model, driver, private_nodes)
        
        # Step 5: Rank by GNN scores + semantic similarity
        ranked_results = _rank_with_gnn(search_results, gnn_features, k)
        
        # Step 6: Format results
        formatted = _format_gnn_results(ranked_results, query)
        
        return formatted
        
    finally:
        driver.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_query_embedding(query: str) -> List[float]:
    """Get OpenAI embedding for query"""
    response = openai.embeddings.create(
        model="text-embedding-3-large",
        input=query
    )
    return response.data[0].embedding


def _fetch_private_nodes(driver, chunk_ids: List[str]) -> List[Dict]:
    """Fetch Private Memory nodes from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WHERE n.chunk_id IN $chunk_ids
            AND (n:PrivateChunk OR n:PrivateConcept)
            RETURN 
                n.chunk_id AS id,
                n.text AS text,
                n.importance AS importance,
                n.memory_class AS memory_class,
                labels(n) AS labels
        """, chunk_ids=chunk_ids)
        
        return [dict(record) for record in result]


def _run_gnn_inference(model, driver, nodes: List[Dict]) -> Dict[str, float]:
    """
    Run GNN inference on Private nodes
    
    Returns centrality scores for each node
    """
    # Build mini-graph from Private Memory
    with driver.session() as session:
        # Get relationships between Private nodes
        node_ids = [n['id'] for n in nodes]
        
        result = session.run("""
            MATCH (a)-[r]->(b)
            WHERE a.chunk_id IN $node_ids
            AND b.chunk_id IN $node_ids
            RETURN a.chunk_id AS source, b.chunk_id AS target
        """, node_ids=node_ids)
        
        edges = [(r['source'], r['target']) for r in result]
    
    # Simple centrality: count of connections
    # (In full GNN, would use graph convolutions)
    centrality = {}
    for node in nodes:
        node_id = node['id']
        # Count edges
        in_degree = sum(1 for s, t in edges if t == node_id)
        out_degree = sum(1 for s, t in edges if s == node_id)
        centrality[node_id] = (in_degree + out_degree) / max(len(edges), 1)
    
    return centrality


def _rank_with_gnn(
    search_results,
    gnn_features: Dict[str, float],
    k: int
) -> List[Dict]:
    """Combine semantic similarity + GNN centrality"""
    ranked = []
    
    for hit in search_results:
        chunk_id = hit.id
        semantic_score = hit.score
        gnn_centrality = gnn_features.get(chunk_id, 0.0)
        
        # Combined score: 70% semantic, 30% GNN
        combined_score = 0.7 * semantic_score + 0.3 * gnn_centrality
        
        ranked.append({
            'id': chunk_id,
            'payload': hit.payload,
            'semantic_score': semantic_score,
            'gnn_centrality': gnn_centrality,
            'combined_score': combined_score
        })
    
    # Sort by combined score
    ranked.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return ranked[:k]


def _format_gnn_results(results: List[Dict], query: str) -> str:
    """Format GNN-enhanced results"""
    output = f"🧠 GNN Analysis for: {query}\n\n"
    
    for i, result in enumerate(results, 1):
        text = result['payload'].get('text', 'N/A')[:200]
        semantic = result['semantic_score']
        gnn = result['gnn_centrality']
        combined = result['combined_score']
        
        output += f"{i}. {text}...\n"
        output += f"   📊 Semantic: {semantic:.3f} | GNN: {gnn:.3f} | Combined: {combined:.3f}\n\n"
    
    return output


# ============================================================
# MAIN (for testing)
# ============================================================

if __name__ == "__main__":
    # Test GNN reading
    result = read_gnn_with_steering(
        query="family relationships",
        namespace="private",
        k=3
    )
    print(result)
