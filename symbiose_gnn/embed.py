import os
import json
import torch
from .config import config
from .data_loader import fetch_graph
from .model import GNN

def embed():
    idx2neo, data = fetch_graph()

    model = GNN(1, config["hidden_dim"], config["hidden_dim"])
    model.load_state_dict(torch.load(f"{config['output_dir']}/gnn_model.pt"))
    model.eval()

    embeddings = model(data).detach().numpy()
    node_map = {idx: neo for idx, neo in idx2neo.items()}

    os.makedirs(config["output_dir"], exist_ok=True)

    with open(f"{config['output_dir']}/node_embeddings.json", "w") as f:
        json.dump(embeddings.tolist(), f)

    with open(f"{config['output_dir']}/node_mapping.json", "w") as f:
        json.dump(node_map, f)

    print("[GNN] Embeddings saved")

if __name__ == "__main__":
    embed()
