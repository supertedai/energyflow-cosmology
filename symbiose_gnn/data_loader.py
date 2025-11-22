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

        res_nodes = session.run("""
            MATCH (n)
            WHERE n:EFCPaper OR n:MetaNode
            RETURN elementId(n) AS eid, labels(n) AS labels, n AS props
        """)

        for idx, rec in enumerate(res_nodes):
            idx2neo[idx] = rec["eid"]
            nodes.append(idx)

        res_edges = session.run("""
            MATCH (a)-[r]->(b)
            WHERE (a:EFCPaper OR a:MetaNode)
              AND (b:EFCPaper OR b:MetaNode)
            RETURN elementId(a) AS src, elementId(b) AS dst
        """)

        neo_to_idx = {v: k for k, v in idx2neo.items()}

        for rec in res_edges:
            if rec["src"] in neo_to_idx and rec["dst"] in neo_to_idx:
                edges_src.append(neo_to_idx[rec["src"]])
                edges_dst.append(neo_to_idx[rec["dst"]])

    x = torch.randn(len(nodes), config["embedding_dim"])
    edge_index = torch.tensor([edges_src, edges_dst], dtype=torch.long)

    return idx2neo, Data(x=x, edge_index=edge_index)
