import torch
import torch.nn as nn
from torch.optim import Adam
from .data_loader import fetch_graph
from .model import SymbioseGNN
from .config import config
import os
import json


def train():
    os.makedirs(config["output_dir"], exist_ok=True)

    idx2neo, data = fetch_graph()

    model = SymbioseGNN()
    optimizer = Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    target = torch.zeros(data.x.shape[0], 64)

    for epoch in range(1, 51):
        optimizer.zero_grad()
        out = model(data)
        loss = criterion(out, target)
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"[GNN] Epoch {epoch}/50 - loss={loss.item():.4f}")

    torch.save(model.state_dict(), f"{config['output_dir']}/gnn_model.pt")

    with open(f"{config['output_dir']}/node_mapping.json", "w") as f:
        json.dump(idx2neo, f, indent=2)

    print(f"[GNN] Modell lagret til {config['output_dir']}/gnn_model.pt")


if __name__ == "__main__":
    train()
