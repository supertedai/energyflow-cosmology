#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import torch
import torch.nn as nn
from torch_geometric.nn import SAGEConv


class SymbioseGNN(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, num_layers: int = 2):
        super().__init__()
        layers = []

        # Første lag
        layers.append(SAGEConv(in_channels=in_dim, out_channels=hidden_dim))

        # Mellomlag
        for _ in range(num_layers - 2):
            layers.append(SAGEConv(in_channels=hidden_dim, out_channels=hidden_dim))

        # Siste lag
        if num_layers > 1:
            layers.append(SAGEConv(in_channels=hidden_dim, out_channels=out_dim))

        self.layers = nn.ModuleList(layers)
        self.activation = nn.ReLU()

    def forward(self, x, edge_index):
        for i, layer in enumerate(self.layers):
            x = layer(x, edge_index)
            if i < len(self.layers) - 1:
                x = self.activation(x)
        return x
