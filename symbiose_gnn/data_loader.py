#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Dict, Tuple

import torch
from torch_geometric.data import Data
from neo4j import GraphDatabase

from .config import config


def get_driver():
    return GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_user, config.neo4j_password),
        database=config.neo4j_database,
    )


def fetch_graph() -> Tuple[Dict[int, str], Data]:
    """
    Henter EFCPaper + MetaNode + ADDRESSES fra Neo4j og bygger en heterogen graf
    projisert til en enkel node-type med features.
    """

    driver = get_driver()
    with driver.session() as session:
        # Hent alle noder
        q_nodes = """
        MATCH (n)
        WHERE n:EFCPaper OR n:MetaNode
        RETURN id(n) AS id, labels(n) AS labels, n AS props
        """
        nodes = session.run(q_nodes).data()

        # Hent alle relasjoner
        q_edges = """
        MATCH (a)-[r]->(b)
        WHERE (a:EFCPaper OR a:MetaNode)
          AND (b:EFCPaper OR b:MetaNode)
        RETURN id(a) AS src, id(b) AS dst, type(r) AS type
        """
        edges = session.run(q_edges).data()

    # Map Neo4j-id -> kontinuerlig index
    neo2idx: Dict[int, int] = {}
    idx2neo: Dict[int, int] = {}
    node_labels: Dict[int, str] = {}

    for i, row in enumerate(nodes):
        nid = row["id"]
        neo2idx[nid] = i
        idx2neo[i] = nid
        # enkel type: "paper" / "meta"
        labs = row["labels"]
        if "EFCPaper" in labs:
            node_labels[i] = "EFCPaper"
        elif "MetaNode" in labs:
            node_labels[i] = "MetaNode"
        else:
            node_labels[i] = "Other"

    # Bygg edge_index
    src_list = []
    dst_list = []
    for e in edges:
        src = neo2idx.get(e["src"])
        dst = neo2idx.get(e["dst"])
        if src is None or dst is None:
            continue
        src_list.append(src)
        dst_list.append(dst)

    if not src_list:
        raise RuntimeError("Ingen kanter funnet i grafen – kan ikke trene GNN.")

    edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)

    # Enkle node-features:
    #  - type som one-hot: [is_paper, is_meta]
    #  - grad (antall naboer)
    num_nodes = len(nodes)
    x = torch.zeros((num_nodes, 3), dtype=torch.float32)  # [paper, meta, degree]

    degree = torch.zeros(num_nodes, dtype=torch.float32)
    for s, d in zip(src_list, dst_list):
        degree[s] += 1.0
        degree[d] += 1.0

    for i in range(num_nodes):
        t = node_labels[i]
        if t == "EFCPaper":
            x[i, 0] = 1.0
        elif t == "MetaNode":
            x[i, 1] = 1.0
        x[i, 2] = degree[i]

    data = Data(x=x, edge_index=edge_index)

    # Lagre mapping for senere (for å vite hvilken node som er hvilken)
    mapping_path = config.out_dir / "node_mapping.json"
    mapping = {
        "idx2neo": idx2neo,
        "node_labels": node_labels,
    }
    mapping_path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")

    return idx2neo, data
