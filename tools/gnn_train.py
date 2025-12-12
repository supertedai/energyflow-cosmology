#!/usr/bin/env python3
"""
GNN Training - Link Prediction on EFC Core Graph
=================================================

Trains a Graph Neural Network on EFC-core structure to:
1. Learn structural embeddings of concepts
2. Predict missing SUPPORTS/CONSTRAINS/etc relations
3. Generate suggestions for theory expansion

Architecture:
    - GAT (Graph Attention Network) for heterogeneous edge types
    - Link prediction head (binary classification per edge type)
    - Negative sampling for training

Usage:
    python tools/gnn_train.py --input symbiose_gnn_output/efc_core_graph.pt --epochs 200
"""

import os
import sys
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# PyTorch Geometric imports
try:
    from torch_geometric.nn import GATConv, to_hetero
    from torch_geometric.data import Data
    from torch_geometric.utils import negative_sampling
    import torch_geometric.transforms as T
except ImportError:
    print("❌ PyTorch Geometric not installed!")
    print("   Install: pip install torch-geometric torch-scatter torch-sparse")
    sys.exit(1)

# ============================================================
# CONFIG
# ============================================================

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Training hyperparameters
HIDDEN_DIM = 128
NUM_LAYERS = 3
NUM_HEADS = 4
DROPOUT = 0.3
LEARNING_RATE = 0.001
WEIGHT_DECAY = 5e-4

# Link prediction
NEG_SAMPLING_RATIO = 1.0  # 1 negative per positive edge

# ============================================================
# MODEL ARCHITECTURE
# ============================================================

class EFC_GNN(torch.nn.Module):
    """
    Graph Attention Network for EFC concepts
    
    Multi-head attention allows model to learn:
    - Which concept relations matter most
    - Different aspects of concept relationships
    - Structural patterns in theory
    """
    
    def __init__(self, in_channels: int, hidden_channels: int, num_layers: int, num_heads: int, dropout: float):
        super().__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Input projection
        self.input_proj = torch.nn.Linear(in_channels, hidden_channels)
        
        # GAT layers
        self.convs = torch.nn.ModuleList()
        for i in range(num_layers):
            in_dim = hidden_channels
            out_dim = hidden_channels // num_heads if i < num_layers - 1 else hidden_channels
            
            self.convs.append(
                GATConv(
                    in_dim,
                    out_dim,
                    heads=num_heads,
                    dropout=dropout,
                    concat=(i < num_layers - 1)
                )
            )
        
        # Layer normalization
        self.norms = torch.nn.ModuleList([
            torch.nn.LayerNorm(hidden_channels)
            for _ in range(num_layers)
        ])
    
    def forward(self, x, edge_index):
        """Forward pass - return node embeddings"""
        # Project input features
        x = self.input_proj(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # GAT layers
        for i, (conv, norm) in enumerate(zip(self.convs, self.norms)):
            x_new = conv(x, edge_index)
            x_new = norm(x_new)
            
            if i < self.num_layers - 1:
                x_new = F.relu(x_new)
                x_new = F.dropout(x_new, p=self.dropout, training=self.training)
            
            # Residual connection
            if i > 0:
                x = x + x_new
            else:
                x = x_new
        
        return x

class LinkPredictor(torch.nn.Module):
    """
    Link prediction head for edge type classification
    
    Given two node embeddings, predicts:
    - Probability of edge existing
    - Type of edge (SUPPORTS, CONSTRAINS, etc.)
    """
    
    def __init__(self, hidden_channels: int, num_edge_types: int):
        super().__init__()
        
        self.num_edge_types = num_edge_types
        
        # Edge type predictors
        self.edge_predictors = torch.nn.ModuleList([
            torch.nn.Sequential(
                torch.nn.Linear(hidden_channels * 2, hidden_channels),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.3),
                torch.nn.Linear(hidden_channels, 1)
            )
            for _ in range(num_edge_types)
        ])
    
    def forward(self, z, edge_index, edge_type):
        """
        Predict edge existence and type
        
        Args:
            z: Node embeddings (num_nodes, hidden_dim)
            edge_index: Edge indices (2, num_edges)
            edge_type: Edge types (num_edges,)
        
        Returns:
            predictions: (num_edges, num_edge_types)
        """
        # Get source and target embeddings
        src = z[edge_index[0]]
        dst = z[edge_index[1]]
        
        # Concatenate
        edge_features = torch.cat([src, dst], dim=-1)
        
        # Predict for each edge type
        predictions = []
        for i, predictor in enumerate(self.edge_predictors):
            pred = predictor(edge_features).squeeze(-1)
            predictions.append(pred)
        
        predictions = torch.stack(predictions, dim=1)  # (num_edges, num_edge_types)
        
        return predictions

# ============================================================
# TRAINING UTILITIES
# ============================================================

def split_edges(edge_index, edge_type, train_ratio=0.7, val_ratio=0.15):
    """
    Split edges into train/val/test
    
    Returns:
        train_edge_index, train_edge_type,
        val_edge_index, val_edge_type,
        test_edge_index, test_edge_type
    """
    num_edges = edge_index.shape[1]
    perm = torch.randperm(num_edges)
    
    train_size = int(train_ratio * num_edges)
    val_size = int(val_ratio * num_edges)
    
    train_idx = perm[:train_size]
    val_idx = perm[train_size:train_size + val_size]
    test_idx = perm[train_size + val_size:]
    
    return (
        edge_index[:, train_idx], edge_type[train_idx],
        edge_index[:, val_idx], edge_type[val_idx],
        edge_index[:, test_idx], edge_type[test_idx]
    )

def compute_auc(pos_scores, neg_scores):
    """Compute AUC-ROC for link prediction"""
    from sklearn.metrics import roc_auc_score
    
    scores = torch.cat([pos_scores, neg_scores]).cpu().numpy()
    labels = np.concatenate([np.ones(len(pos_scores)), np.zeros(len(neg_scores))])
    
    return roc_auc_score(labels, scores)

def compute_hits_at_k(pos_scores, neg_scores, k=10):
    """Compute Hits@K metric"""
    # For each positive edge, count how many negatives score higher
    hits = 0
    for pos_score in pos_scores:
        rank = (neg_scores >= pos_score).sum().item() + 1
        if rank <= k:
            hits += 1
    
    return hits / len(pos_scores)

# ============================================================
# TRAINING LOOP
# ============================================================

def train_epoch(model, predictor, optimizer, data, train_edge_index, train_edge_type):
    """Single training epoch"""
    model.train()
    predictor.train()
    
    optimizer.zero_grad()
    
    # Forward pass - get node embeddings
    z = model(data.x, train_edge_index)
    
    # Positive edges
    pos_pred = predictor(z, train_edge_index, train_edge_type)
    
    # Negative sampling
    neg_edge_index = negative_sampling(
        edge_index=train_edge_index,
        num_nodes=data.num_nodes,
        num_neg_samples=int(train_edge_index.shape[1] * NEG_SAMPLING_RATIO)
    )
    
    # Random edge types for negatives
    neg_edge_type = torch.randint(0, predictor.num_edge_types, (neg_edge_index.shape[1],), device=DEVICE)
    
    neg_pred = predictor(z, neg_edge_index, neg_edge_type)
    
    # Loss: binary cross-entropy
    # Positive edges should have high scores, negatives low
    pos_labels = torch.ones(pos_pred.shape[0], device=DEVICE)
    neg_labels = torch.zeros(neg_pred.shape[0], device=DEVICE)
    
    # Get predictions for correct edge type
    pos_scores = pos_pred[torch.arange(len(train_edge_type)), train_edge_type]
    neg_scores = neg_pred[torch.arange(len(neg_edge_type)), neg_edge_type]
    
    loss = F.binary_cross_entropy_with_logits(pos_scores, pos_labels) + \
           F.binary_cross_entropy_with_logits(neg_scores, neg_labels)
    
    loss.backward()
    optimizer.step()
    
    return loss.item()

@torch.no_grad()
def evaluate(model, predictor, data, edge_index, edge_type):
    """Evaluate model on validation/test set"""
    model.eval()
    predictor.eval()
    
    # Get embeddings
    z = model(data.x, data.edge_index)
    
    # Positive predictions
    pos_pred = predictor(z, edge_index, edge_type)
    pos_scores = pos_pred[torch.arange(len(edge_type)), edge_type].sigmoid()
    
    # Negative sampling
    neg_edge_index = negative_sampling(
        edge_index=data.edge_index,
        num_nodes=data.num_nodes,
        num_neg_samples=edge_index.shape[1]
    )
    neg_edge_type = torch.randint(0, predictor.num_edge_types, (neg_edge_index.shape[1],), device=DEVICE)
    
    neg_pred = predictor(z, neg_edge_index, neg_edge_type)
    neg_scores = neg_pred[torch.arange(len(neg_edge_type)), neg_edge_type].sigmoid()
    
    # Metrics
    auc = compute_auc(pos_scores, neg_scores)
    hits10 = compute_hits_at_k(pos_scores, neg_scores, k=10)
    
    return auc, hits10

# ============================================================
# MAIN TRAINING FUNCTION
# ============================================================

def train_gnn(graph_path: str, epochs: int = 200, output_dir: str = "symbiose_gnn_output"):
    """
    Main training function
    """
    print("\n🚀 GNN Training - EFC Link Prediction")
    print("=" * 60)
    
    # Load graph
    print(f"📂 Loading graph from {graph_path}...")
    graph_data = torch.load(graph_path)
    
    # Create PyG Data object
    data = Data(
        x=graph_data["x"].to(DEVICE),
        edge_index=graph_data["edge_index"].to(DEVICE),
        edge_type=graph_data["edge_type"].to(DEVICE),
        edge_weight=graph_data["edge_weight"].to(DEVICE),
        num_nodes=graph_data["num_nodes"]
    )
    
    print(f"   📊 {data.num_nodes} nodes, {data.edge_index.shape[1]} edges")
    print(f"   🔢 Feature dim: {data.x.shape[1]}")
    print(f"   🏷️  Edge types: {len(graph_data['edge_type_names'])}")
    
    # Split edges
    print("\n🔀 Splitting edges (70% train, 15% val, 15% test)...")
    train_edge_index, train_edge_type, val_edge_index, val_edge_type, test_edge_index, test_edge_type = \
        split_edges(data.edge_index, data.edge_type)
    
    print(f"   Train: {train_edge_index.shape[1]} edges")
    print(f"   Val:   {val_edge_index.shape[1]} edges")
    print(f"   Test:  {test_edge_index.shape[1]} edges")
    
    # Initialize model
    print(f"\n🏗️  Building GNN model...")
    print(f"   Hidden dim: {HIDDEN_DIM}")
    print(f"   Layers: {NUM_LAYERS}")
    print(f"   Heads: {NUM_HEADS}")
    
    model = EFC_GNN(
        in_channels=data.x.shape[1],
        hidden_channels=HIDDEN_DIM,
        num_layers=NUM_LAYERS,
        num_heads=NUM_HEADS,
        dropout=DROPOUT
    ).to(DEVICE)
    
    predictor = LinkPredictor(
        hidden_channels=HIDDEN_DIM,
        num_edge_types=len(graph_data['edge_type_names'])
    ).to(DEVICE)
    
    optimizer = torch.optim.Adam(
        list(model.parameters()) + list(predictor.parameters()),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )
    
    print(f"\n🏃 Training for {epochs} epochs...")
    print("=" * 60)
    
    best_val_auc = 0.0
    best_epoch = 0
    
    for epoch in range(1, epochs + 1):
        # Train
        loss = train_epoch(model, predictor, optimizer, data, train_edge_index, train_edge_type)
        
        # Evaluate every 10 epochs
        if epoch % 10 == 0:
            val_auc, val_hits10 = evaluate(model, predictor, data, val_edge_index, val_edge_type)
            
            print(f"Epoch {epoch:3d} | Loss: {loss:.4f} | Val AUC: {val_auc:.4f} | Hits@10: {val_hits10:.4f}")
            
            # Save best model
            if val_auc > best_val_auc:
                best_val_auc = val_auc
                best_epoch = epoch
                
                output_path = Path(output_dir) / "efc_gnn_best.pt"
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'predictor_state_dict': predictor.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_auc': val_auc,
                    'val_hits10': val_hits10,
                    'graph_metadata': graph_data
                }, output_path)
    
    # Final test evaluation
    print("\n" + "=" * 60)
    print("🎯 Final Test Evaluation")
    
    # Load best model
    checkpoint = torch.load(Path(output_dir) / "efc_gnn_best.pt")
    model.load_state_dict(checkpoint['model_state_dict'])
    predictor.load_state_dict(checkpoint['predictor_state_dict'])
    
    test_auc, test_hits10 = evaluate(model, predictor, data, test_edge_index, test_edge_type)
    
    print(f"   Best epoch: {best_epoch}")
    print(f"   Val AUC:    {best_val_auc:.4f}")
    print(f"   Test AUC:   {test_auc:.4f}")
    print(f"   Hits@10:    {test_hits10:.4f}")
    
    if test_auc > 0.7:
        print("\n✅ Model shows structural understanding (AUC > 0.7)")
    elif test_auc > 0.6:
        print("\n⚠️  Model has moderate performance (AUC 0.6-0.7)")
    else:
        print("\n❌ Model needs more data or tuning (AUC < 0.6)")
    
    print(f"\n💾 Model saved to: {output_dir}/efc_gnn_best.pt")

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train GNN on EFC core graph")
    parser.add_argument("--input", default="symbiose_gnn_output/efc_core_graph.pt", help="Input graph file")
    parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs")
    parser.add_argument("--output-dir", default="symbiose_gnn_output", help="Output directory")
    
    args = parser.parse_args()
    
    train_gnn(args.input, args.epochs, args.output_dir)
