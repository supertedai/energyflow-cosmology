import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from .config import config


class SymbioseGNN(nn.Module):
    def __init__(self, input_dim=config["embedding_dim"], hidden_dim=128, out_dim=64):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.conv2 = GCNConv(hidden_dim, out_dim)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = self.relu(x)
        x = self.conv2(x, edge_index)
        return x
