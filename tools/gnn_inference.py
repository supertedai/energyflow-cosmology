#!/usr/bin/env python3
"""
GNN Inference - Generate Theory Suggestions
============================================

Uses trained GNN model to:
1. Generate node embeddings for all EFC concepts
2. Predict missing relations (link prediction)
3. Create GNNSuggestion nodes in Neo4j
4. Rank suggestions by confidence

Usage:
    python tools/gnn_inference.py --model symbiose_gnn_output/efc_gnn_best.pt --top-k 50
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Import model architecture
from gnn_train import EFC_GNN, LinkPredictor

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@dataclass
class Suggestion:
    """GNN-proposed relation"""
    source_id: str
    target_id: str
    source_name: str
    target_name: str
    relation_type: str
    confidence: float

# ============================================================
# INFERENCE
# ============================================================

def load_trained_model(checkpoint_path: str):
    """Load trained GNN model and graph data"""
    print(f"📂 Loading trained model from {checkpoint_path}...")
    
    checkpoint = torch.load(checkpoint_path, map_location=DEVICE)
    
    graph_data = checkpoint['graph_metadata']
    
    # Recreate model
    model = EFC_GNN(
        in_channels=graph_data["x"].shape[1],
        hidden_channels=128,
        num_layers=3,
        num_heads=4,
        dropout=0.3
    ).to(DEVICE)
    
    predictor = LinkPredictor(
        hidden_channels=128,
        num_edge_types=len(graph_data['edge_type_names'])
    ).to(DEVICE)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    predictor.load_state_dict(checkpoint['predictor_state_dict'])
    
    model.eval()
    predictor.eval()
    
    print(f"   ✅ Model loaded (Val AUC: {checkpoint['val_auc']:.4f})")
    
    return model, predictor, graph_data

@torch.no_grad()
def generate_suggestions(
    model,
    predictor,
    graph_data,
    top_k: int = 50,
    min_confidence: float = 0.7
) -> List[Suggestion]:
    """
    Generate top-k suggestions for missing relations
    """
    print(f"\n🔮 Generating suggestions...")
    print(f"   Min confidence: {min_confidence}")
    print(f"   Top-K: {top_k}")
    
    # Prepare data
    x = graph_data["x"].to(DEVICE)
    edge_index = graph_data["edge_index"].to(DEVICE)
    
    # Get node embeddings
    z = model(x, edge_index)
    
    # Generate all possible node pairs (excluding existing edges)
    num_nodes = graph_data["num_nodes"]
    
    # Convert existing edges to set for fast lookup
    existing_edges = set()
    for i in range(edge_index.shape[1]):
        src = edge_index[0, i].item()
        dst = edge_index[1, i].item()
        existing_edges.add((src, dst))
    
    # Generate candidate pairs
    candidates = []
    for src in range(num_nodes):
        for dst in range(num_nodes):
            if src != dst and (src, dst) not in existing_edges:
                candidates.append((src, dst))
    
    print(f"   🔍 Evaluating {len(candidates)} candidate pairs...")
    
    # Batch prediction
    batch_size = 1024
    all_suggestions = []
    
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i+batch_size]
        
        # Build edge_index for batch
        batch_edge_index = torch.tensor([[src, dst] for src, dst in batch], dtype=torch.long).T.to(DEVICE)
        
        # Predict for all edge types
        for edge_type_idx, edge_type_name in enumerate(graph_data['edge_type_names']):
            batch_edge_type = torch.full((batch_edge_index.shape[1],), edge_type_idx, dtype=torch.long, device=DEVICE)
            
            # Get predictions
            preds = predictor(z, batch_edge_index, batch_edge_type)
            scores = preds[:, edge_type_idx].sigmoid()
            
            # Filter by confidence
            for j, (src, dst) in enumerate(batch):
                confidence = scores[j].item()
                
                if confidence >= min_confidence:
                    suggestion = Suggestion(
                        source_id=graph_data['idx_to_node_id'][src],
                        target_id=graph_data['idx_to_node_id'][dst],
                        source_name=graph_data['node_metadata'][src]['name'],
                        target_name=graph_data['node_metadata'][dst]['name'],
                        relation_type=edge_type_name,
                        confidence=confidence
                    )
                    all_suggestions.append(suggestion)
        
        if (i + batch_size) % 10000 == 0:
            print(f"      Processed {i+batch_size}/{len(candidates)} pairs...", end='\r')
    
    # Sort by confidence
    all_suggestions.sort(key=lambda s: s.confidence, reverse=True)
    
    # Take top-k
    top_suggestions = all_suggestions[:top_k]
    
    print(f"\n   ✅ Found {len(all_suggestions)} suggestions above threshold")
    print(f"   📊 Returning top {len(top_suggestions)}")
    
    return top_suggestions

# ============================================================
# NEO4J INTEGRATION
# ============================================================

def save_suggestions_to_neo4j(driver, suggestions: List[Suggestion], model_name: str = "efc_gnn_v1"):
    """Save suggestions as GNNSuggestion nodes in Neo4j"""
    print(f"\n💾 Saving {len(suggestions)} suggestions to Neo4j...")
    
    with driver.session() as session:
        for i, sugg in enumerate(suggestions, 1):
            query = """
            MATCH (source:Concept {id: $source_id})
            MATCH (target:Concept {id: $target_id})
            
            CREATE (s:GNNSuggestion {
                id: $suggestion_id,
                source_concept_id: $source_id,
                target_concept_id: $target_id,
                source_name: $source_name,
                target_name: $target_name,
                suggested_relation: $relation_type,
                confidence: $confidence,
                gnn_model: $model_name,
                status: "PENDING",
                created_at: datetime()
            })
            
            CREATE (source)-[:HAS_SUGGESTION]->(s)
            CREATE (s)-[:SUGGESTS_RELATION]->(target)
            
            RETURN s.id
            """
            
            session.run(
                query,
                suggestion_id=f"sugg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:04d}",
                source_id=sugg.source_id,
                target_id=sugg.target_id,
                source_name=sugg.source_name,
                target_name=sugg.target_name,
                relation_type=sugg.relation_type,
                confidence=sugg.confidence,
                model_name=model_name
            )
            
            if i % 10 == 0:
                print(f"   Saved {i}/{len(suggestions)}...", end='\r')
    
    print(f"\n   ✅ All suggestions saved to Neo4j")

def print_top_suggestions(suggestions: List[Suggestion], n: int = 10):
    """Print top-n suggestions"""
    print(f"\n🎯 Top {n} Suggestions:")
    print("=" * 80)
    
    for i, sugg in enumerate(suggestions[:n], 1):
        print(f"{i:2d}. [{sugg.confidence:.3f}] {sugg.source_name}")
        print(f"    --[{sugg.relation_type}]--> {sugg.target_name}")
        print()

# ============================================================
# MAIN
# ============================================================

def run_inference(
    checkpoint_path: str,
    top_k: int = 50,
    min_confidence: float = 0.7,
    save_to_neo4j: bool = True
):
    """Main inference pipeline"""
    print("\n🚀 GNN Inference - Theory Suggestion Generation")
    print("=" * 60)
    
    # Load model
    model, predictor, graph_data = load_trained_model(checkpoint_path)
    
    # Generate suggestions
    suggestions = generate_suggestions(model, predictor, graph_data, top_k, min_confidence)
    
    # Print top suggestions
    print_top_suggestions(suggestions, n=10)
    
    # Save to Neo4j
    if save_to_neo4j:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        try:
            save_suggestions_to_neo4j(driver, suggestions)
        finally:
            driver.close()
    
    print("\n✅ Inference complete!")
    print(f"   💡 Run validation: python tools/gnn_theory_validator.py --batch --min-confidence {min_confidence}")

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate GNN suggestions for EFC theory")
    parser.add_argument("--model", default="symbiose_gnn_output/efc_gnn_best.pt", help="Trained model checkpoint")
    parser.add_argument("--top-k", type=int, default=50, help="Number of suggestions to generate")
    parser.add_argument("--min-confidence", type=float, default=0.7, help="Minimum confidence threshold")
    parser.add_argument("--no-save", action="store_true", help="Don't save to Neo4j (dry run)")
    
    args = parser.parse_args()
    
    run_inference(
        checkpoint_path=args.model,
        top_k=args.top_k,
        min_confidence=args.min_confidence,
        save_to_neo4j=not args.no_save
    )
