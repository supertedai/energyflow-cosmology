#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

from .config import config
from .data_loader import fetch_graph
from .model import SymbioseGNN


def load_optional_labels(idx2neo):
    """
    Hvis du legger inn f.eks. p.resonance_score på noder i Neo4j senere,
    kan du hente dem her og bruke ekte labels.

    Nå: dummy – ingen labels → None.
    """
    return None  # du kan utvide senere


def train():
    idx2neo, data = fetch_graph()
    x, edge_index = data.x, data.edge_index

    labels = load_optional_labels(idx2neo)

    in_dim = x.size(1)
    out_dim = config.embed_dim

    model = SymbioseGNN(
        in_dim=in_dim,
        hidden_dim=config.hidden_dim,
        out_dim=out_dim,
        num_layers=config.num_layers,
    )

    model.train()

    if labels is not None:
        # Supervised (f.eks. regressjon på resonans)
        y = torch.tensor(labels, dtype=torch.float32)
        loss_fn = nn.MSELoss()
    else:
        # Self-supervised dummy:
        # Lær å predikere degree (x[:,2]) fra embedding.
        y = x[:, 2]  # degree
        loss_fn = nn.MSELoss()

    optimizer = optim.Adam(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)

    for epoch in range(config.epochs):
        optimizer.zero_grad()
        out = model(x, edge_index)  # [N, embed_dim]

        # enkel lesout: predikér y fra embedding med lineær projeksjon
        head = torch.nn.Linear(config.embed_dim, 1)
        pred = head(out).squeeze(-1)

        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"[GNN] Epoch {epoch+1}/{config.epochs} - loss={loss.item():.4f}")

    # lagre model
    model_path = config.out_dir / "gnn_model.pt"
    torch.save(model.state_dict(), model_path)
    print(f"[GNN] Modell lagret til {model_path}")


if __name__ == "__main__":
    train()
