import torch
from torch_geometric.data import Data
from neo4j import GraphDatabase
from .config import config


def get_driver():
    return GraphDatabase.driver(
        config["neo4j_uri"],
        auth=(config["neo4j_user"], config["neo4j_password"])
    )


def fetch_graph():
    driver = get_driver()

    nodes = []
    edges_src = []
    edges_dst = []
    idx2neo = {}

    with driver.session(database=config["neo4j_database"]) as session:

        # Fetch ALL nodes from the graph (10,183 nodes)
        print("[GNN] Fetching all nodes from Neo4j...")
        res_nodes = session.run("""
            MATCH (n)
            RETURN elementId(n) AS eid, labels(n) AS labels, n AS props
        """)

        for idx, rec in enumerate(res_nodes):
            idx2neo[idx] = rec["eid"]
            nodes.append(idx)

        # Fetch ALL edges in the graph
        print(f"[GNN] Found {len(nodes)} nodes. Fetching edges...")
        res_edges = session.run("""
            MATCH (a)-[r]->(b)
            RETURN elementId(a) AS src, elementId(b) AS dst
        """)

        neo_to_idx = {v: k for k, v in idx2neo.items()}

        for rec in res_edges:
            if rec["src"] in neo_to_idx and rec["dst"] in neo_to_idx:
                edges_src.append(neo_to_idx[rec["src"]])
                edges_dst.append(neo_to_idx[rec["dst"]])

    x = torch.randn(len(nodes), config["embedding_dim"])
    edge_index = torch.tensor([edges_src, edges_dst], dtype=torch.long)

    print(f"[GNN] Graph loaded: {len(nodes)} nodes, {len(edges_src)} edges")
    print(f"[GNN] Feature dimension: {config['embedding_dim']}")

    return idx2neo, Data(x=x, edge_index=edge_index)
