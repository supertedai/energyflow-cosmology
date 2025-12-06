import torch
import torch.nn as nn
from torch.optim import Adam
from .data_loader import fetch_graph
from .model import SymbioseGNN
from .config import config
import os
import json


def train():
    print("=" * 60)
    print("🧠 SYMBIOSE GNN TRAINING")
    print("=" * 60)
    
    os.makedirs(config["output_dir"], exist_ok=True)

    # Load full Neo4j graph
    idx2neo, data = fetch_graph()
    
    print(f"\n📊 Training Configuration:")
    print(f"   Nodes: {data.x.shape[0]}")
    print(f"   Edges: {data.edge_index.shape[1]}")
    print(f"   Input dim: {data.x.shape[1]}")
    print(f"   Output dim: {config['embedding_dim']}")
    print(f"   Epochs: 100")
    print(f"   Learning rate: 0.001")

    model = SymbioseGNN()
    optimizer = Adam(model.parameters(), lr=0.001)
    
    # Self-supervised reconstruction loss
    # GNN learns to reconstruct node features from graph structure
    criterion = nn.MSELoss()

    print(f"\n🔄 Starting training...")
    for epoch in range(1, 101):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        embeddings = model(data)
        
        # Reconstruction loss: try to predict original features
        loss = criterion(embeddings, data.x)
        
        # Backward pass
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"   Epoch {epoch:3d}/100 - Loss: {loss.item():.4f}")

    print(f"\n✅ Training complete!")
    
    # Save model
    model_path = f"{config['output_dir']}/gnn_model.pt"
    torch.save(model.state_dict(), model_path)
    print(f"   Model saved: {model_path}")
    
    # Save node mapping
    mapping_path = f"{config['output_dir']}/node_mapping.json"
    with open(mapping_path, "w") as f:
        json.dump(idx2neo, f, indent=2)
    print(f"   Mapping saved: {mapping_path}")
    
    print("\n📊 Next step: Run embed.py to generate embeddings for all nodes")


if __name__ == "__main__":
    train()
