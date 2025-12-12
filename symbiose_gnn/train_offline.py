#!/usr/bin/env python3
"""
train_offline.py - Offline GNN Training on Exported EFC Graph
=============================================================

Purpose: Train GNN on exported EFC graph data WITHOUT touching Neo4j.
         Pure offline training for maximum safety and control.

Input:
- symbiose_gnn_output/efc_nodes_latest.jsonl
- symbiose_gnn_output/efc_edges_latest.jsonl
- symbiose_gnn_output/efc_metadata_latest.json

Output:
- symbiose_gnn_output/gnn_model.pt           (trained weights)
- symbiose_gnn_output/node_embeddings.json   (GNN embeddings)
- symbiose_gnn_output/training_log.json      (loss curve, metrics)

Safety:
- NO database connections
- NO runtime modifications
- Pure file-based training
- Reproducible with random seed

Usage:
    python symbiose_gnn/train_offline.py
    
    # With custom params
    python symbiose_gnn/train_offline.py --epochs 200 --hidden-dim 256
"""

import os
import sys
import json
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

import torch_geometric
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ============================================================
# CONFIG
# ============================================================

INPUT_DIR = Path("symbiose_gnn_output")
OUTPUT_DIR = Path("symbiose_gnn_output")

DEFAULT_EMBEDDING_DIM = 128
DEFAULT_HIDDEN_DIM = 256
DEFAULT_OUTPUT_DIM = 64
DEFAULT_EPOCHS = 100
DEFAULT_LR = 0.01

RANDOM_SEED = 42

# ============================================================
# GNN MODEL (Offline Variant)
# ============================================================

class OfflineSymbioseGNN(nn.Module):
    """
    GNN for EFC concept graph
    
    Architecture:
    - Input: Node features (frequency, degree, etc.)
    - Hidden: 2 GCN layers with ReLU
    - Output: Node embeddings
    
    Training task: Link prediction (reconstruct graph structure)
    """
    
    def __init__(
        self,
        input_dim: int = DEFAULT_EMBEDDING_DIM,
        hidden_dim: int = DEFAULT_HIDDEN_DIM,
        output_dim: int = DEFAULT_OUTPUT_DIM
    ):
        super().__init__()
        
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        self.conv2 = GCNConv(hidden_dim, output_dim)
        
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        
        # Layer 1
        x = self.conv1(x, edge_index)
        x = self.relu(x)
        x = self.dropout(x)
        
        # Layer 2
        x = self.conv2(x, edge_index)
        
        return x
    
    def decode(self, z, edge_index):
        """Decode edge existence from node embeddings"""
        src, dst = edge_index
        return (z[src] * z[dst]).sum(dim=-1)


# ============================================================
# DATA LOADING
# ============================================================

def load_exported_graph() -> Tuple[Data, Dict]:
    """
    Load exported EFC graph from JSONL files
    
    Returns:
        (PyTorch Geometric Data object, metadata dict)
    """
    print("📁 Loading exported graph...")
    
    # Load metadata
    metadata_file = INPUT_DIR / "efc_metadata_latest.json"
    if not metadata_file.exists():
        raise FileNotFoundError(
            f"Metadata not found: {metadata_file}\n"
            "Run: python tools/export_efc_for_gnn.py"
        )
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"   Graph: {metadata['node_count']} nodes, {metadata['edge_count']} edges")
    
    # Load nodes
    nodes_file = INPUT_DIR / "efc_nodes_latest.jsonl"
    nodes = []
    node_id_map = {}  # Neo4j ID -> index
    
    with open(nodes_file, 'r') as f:
        for idx, line in enumerate(f):
            node = json.loads(line)
            nodes.append(node)
            node_id_map[node['node_id']] = idx
    
    print(f"   ✓ Loaded {len(nodes)} nodes")
    
    # Load edges
    edges_file = INPUT_DIR / "efc_edges_latest.jsonl"
    edges = []
    
    with open(edges_file, 'r') as f:
        for line in f:
            edge = json.loads(line)
            
            # Map Neo4j IDs to indices
            src_idx = node_id_map.get(edge['source_id'])
            tgt_idx = node_id_map.get(edge['target_id'])
            
            if src_idx is not None and tgt_idx is not None:
                edges.append([src_idx, tgt_idx])
    
    print(f"   ✓ Loaded {len(edges)} edges")
    
    # Build node features
    node_features = []
    for node in nodes:
        features = [
            float(node.get('degree', 0)),
            float(node.get('frequency', 1)),
            1.0 if 'Concept' in node['labels'] else 0.0,
            1.0 if 'Chunk' in node['labels'] else 0.0
        ]
        node_features.append(features)
    
    # Convert to tensors
    x = torch.tensor(node_features, dtype=torch.float)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    # Pad features to match embedding dim if needed
    if x.size(1) < DEFAULT_EMBEDDING_DIM:
        padding = torch.zeros(x.size(0), DEFAULT_EMBEDDING_DIM - x.size(1))
        x = torch.cat([x, padding], dim=1)
    
    # Create PyG Data object
    data = Data(x=x, edge_index=edge_index)
    
    print(f"   ✓ Created PyG graph: {data}")
    
    return data, metadata


# ============================================================
# TRAINING
# ============================================================

def train_gnn_offline(
    epochs: int = DEFAULT_EPOCHS,
    hidden_dim: int = DEFAULT_HIDDEN_DIM,
    output_dim: int = DEFAULT_OUTPUT_DIM,
    lr: float = DEFAULT_LR
) -> Dict:
    """
    Train GNN on exported EFC graph (offline)
    
    Returns:
        Training statistics
    """
    # Set random seed for reproducibility
    torch.manual_seed(RANDOM_SEED)
    
    # Load data
    data, metadata = load_exported_graph()
    
    # Initialize model
    model = OfflineSymbioseGNN(
        input_dim=data.x.size(1),
        hidden_dim=hidden_dim,
        output_dim=output_dim
    )
    
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCEWithLogitsLoss()
    
    print(f"\n🧠 Training GNN:")
    print(f"   Architecture: {data.x.size(1)} -> {hidden_dim} -> {output_dim}")
    print(f"   Epochs: {epochs}")
    print(f"   Learning rate: {lr}")
    
    # Training loop
    training_log = []
    
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        # Forward pass
        z = model(data)
        
        # Link prediction loss
        # Positive samples: existing edges
        pos_edge_index = data.edge_index
        pos_pred = model.decode(z, pos_edge_index)
        pos_loss = criterion(pos_pred, torch.ones(pos_pred.size(0)))
        
        # Negative samples: random non-edges
        neg_edge_index = torch_geometric.utils.negative_sampling(
            edge_index=data.edge_index,
            num_nodes=data.x.size(0),
            num_neg_samples=pos_edge_index.size(1)
        )
        neg_pred = model.decode(z, neg_edge_index)
        neg_loss = criterion(neg_pred, torch.zeros(neg_pred.size(0)))
        
        # Total loss
        loss = pos_loss + neg_loss
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Log progress
        if epoch % 10 == 0:
            print(f"   Epoch {epoch:3d}/{epochs}: Loss = {loss.item():.4f}")
        
        training_log.append({
            'epoch': epoch,
            'loss': loss.item(),
            'pos_loss': pos_loss.item(),
            'neg_loss': neg_loss.item()
        })
    
    print(f"\n✅ Training complete")
    
    # Save model
    model_path = OUTPUT_DIR / "gnn_model.pt"
    torch.save(model.state_dict(), model_path)
    print(f"   ✓ Saved model: {model_path}")
    
    # Generate embeddings
    model.eval()
    with torch.no_grad():
        embeddings = model(data).cpu().numpy().tolist()
    
    embeddings_path = OUTPUT_DIR / "node_embeddings.json"
    with open(embeddings_path, 'w') as f:
        json.dump(embeddings, f)
    print(f"   ✓ Saved embeddings: {embeddings_path}")
    
    # Save training log
    log_path = OUTPUT_DIR / "training_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            'metadata': metadata,
            'training': {
                'epochs': epochs,
                'hidden_dim': hidden_dim,
                'output_dim': output_dim,
                'lr': lr,
                'random_seed': RANDOM_SEED
            },
            'log': training_log
        }, f, indent=2)
    print(f"   ✓ Saved training log: {log_path}")
    
    return {
        'final_loss': training_log[-1]['loss'],
        'model_path': str(model_path),
        'embeddings_path': str(embeddings_path)
    }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Train GNN on exported EFC graph (offline)"
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=DEFAULT_EPOCHS,
        help=f"Number of training epochs (default: {DEFAULT_EPOCHS})"
    )
    parser.add_argument(
        '--hidden-dim',
        type=int,
        default=DEFAULT_HIDDEN_DIM,
        help=f"Hidden layer dimension (default: {DEFAULT_HIDDEN_DIM})"
    )
    parser.add_argument(
        '--output-dim',
        type=int,
        default=DEFAULT_OUTPUT_DIM,
        help=f"Output embedding dimension (default: {DEFAULT_OUTPUT_DIM})"
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=DEFAULT_LR,
        help=f"Learning rate (default: {DEFAULT_LR})"
    )
    
    args = parser.parse_args()
    
    train_gnn_offline(
        epochs=args.epochs,
        hidden_dim=args.hidden_dim,
        output_dim=args.output_dim,
        lr=args.lr
    )


if __name__ == "__main__":
    main()
