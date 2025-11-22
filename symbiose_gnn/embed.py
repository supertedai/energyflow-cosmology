import torch
import json
from .model import SymbioseGNN
from .data_loader import fetch_graph
from .config import config
import os


def embed():
    os.makedirs(config["output_dir"], exist_ok=True)

    model = SymbioseGNN()
    model.load_state_dict(torch.load(f"{config['output_dir']}/gnn_model.pt"))

    _, data = fetch_graph()
    embeddings = model(data).detach().numpy().tolist()

    out_file = f"{config['output_dir']}/node_embeddings.json"
    with open(out_file, "w") as f:
        json.dump(embeddings, f, indent=2)

    print(f"[GNN] Node embeddings saved to {out_file}")


if __name__ == "__main__":
    embed()
