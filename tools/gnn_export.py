#!/usr/bin/env python3
"""
GNN Export - Extract EFC Core Graph for Training
=================================================

Exports ONLY the crystallized EFC-core structure from Neo4j:
- Node types: Concept, Equation, Model/Framework
- Edge types: SUPPORTS, CONSTRAINS, PART_OF, GOVERNS, ANALOGOUS_TO
- Features: domain, layer, stability, embeddings, centrality

This is the CLEAN subset for GNN training - NOT the full document/chunk graph.

Usage:
    python tools/gnn_export.py --output symbiose_gnn_output/efc_core_graph.pt
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# Try to import cohere, but make it optional
try:
    import cohere
    COHERE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️  Cohere not available: {e}")
    print(f"    Will use random embeddings for testing")
    COHERE_AVAILABLE = False

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# EFC Core node types
CORE_NODE_TYPES = ["Concept", "Equation", "Model", "Framework"]

# EFC Core edge types (theory-level, not document-level)
CORE_EDGE_TYPES = [
    "SUPPORTS",        # Strengthens another concept
    "CONSTRAINS",      # Sets boundaries
    "PART_OF",         # Component of larger framework
    "GOVERNS",         # Equation governs concept
    "ANALOGOUS_TO",    # Weak similarity
    "DERIVES_FROM",    # Logical derivation
    "CONFLICTS_WITH",  # Theoretical tension
    "DEPENDS_ON",      # Dependency relation
    "APPLIES",         # Application of concept
    "ENABLES",         # Enables another concept
    "USES",            # Uses another concept
    "IMPLEMENTS",      # Implementation of concept
    "INTEGRATES",      # Integration of concepts
    "FEEDS",           # Data/information flow
    "CREATES",         # Creates/produces
    "REQUIRES",        # Requires for operation
    "BRIDGES",         # Bridges domains
    "ANALYZES",        # Analytical relation
    "RELATES_TO",      # General relation
    "ORGANIZES",       # Organizational relation
    "GUIDES",          # Guidance relation
    "INSTANTIATES",    # Instantiation
    "EMERGES_FROM",    # Emergence relation
]

# Domain categories
DOMAINS = ["cosmology", "thermodynamics", "meta", "cognition", "ai", "information", "general"]

# Layer categories
LAYERS = ["formal", "applied", "meta", "cognitive", "computational"]

@dataclass
class GNNNode:
    """GNN-ready node with features"""
    id: str
    neo4j_id: str
    type: str
    name: str
    
    # Categorical
    domain: str
    layer: str
    
    # Scalars
    stability_score: float
    mention_count_efc: int
    mention_count_private: int
    degree: int
    efc_core: bool
    
    # Embeddings
    text_embedding: np.ndarray
    
    # Additional
    metadata: Dict

@dataclass
class GNNEdge:
    """GNN-ready edge"""
    source_id: str
    target_id: str
    type: str
    weight: float
    properties: Dict

# ============================================================
# STEP 1: EXTRACT EFC CORE NODES FROM NEO4J
# ============================================================

def extract_core_nodes(driver) -> List[GNNNode]:
    """
    Extract only EFC-core nodes (Concept, Equation, Model, Framework)
    with all their features.
    
    FILTERS by authority: Only count mentions from authoritative sources.
    """
    print("🔍 Extracting EFC core nodes from Neo4j (filtered by authority)...")
    
    nodes = []
    
    with driver.session() as session:
        # Query for each core node type
        for node_type in CORE_NODE_TYPES:
            query = f"""
            MATCH (n:{node_type})
            OPTIONAL MATCH (n)-[r]-()
            
            // Count only PRIMARY authoritative mentions (trust >= 1.0)
            OPTIONAL MATCH (n)<-[:MENTIONS]-(chunk:Chunk)
            WHERE chunk.authority = "PRIMARY" AND chunk.trust >= 1.0
            
            RETURN 
                elementId(n) as neo4j_id,
                n.id as id,
                n.name as name,
                labels(n) as labels,
                properties(n) as props,
                count(DISTINCT r) as degree,
                count(DISTINCT chunk) as authoritative_mentions
            """
            
            result = session.run(query)
            
            for record in result:
                # Extract properties
                props = record["props"]
                auth_mentions = record["authoritative_mentions"]
                
                # SKIP concepts with zero authoritative mentions
                if auth_mentions == 0:
                    continue
                
                # Create GNN node (will add embedding later)
                node = GNNNode(
                    id=record["id"] or record["neo4j_id"],
                    neo4j_id=record["neo4j_id"],
                    type=node_type,
                    name=record["name"] or props.get("name", "Unknown"),
                    domain=props.get("domain", "general"),
                    layer=props.get("layer", "formal"),
                    stability_score=float(props.get("stability_score", 0.5)),
                    mention_count_efc=int(auth_mentions),  # Use authoritative count
                    mention_count_private=0,  # Reset private count
                    degree=record["degree"],
                    efc_core=bool(props.get("efc_core", True)),  # All are core now
                    text_embedding=None,  # Added later
                    metadata=props
                )
                
                nodes.append(node)
    
    print(f"   ✅ Extracted {len(nodes)} core nodes (authoritative only)")
    return nodes

# ============================================================
# STEP 2: EXTRACT EFC CORE EDGES
# ============================================================

def extract_core_edges(driver, node_ids: set) -> List[GNNEdge]:
    """
    Extract only theory-level edges between EFC core nodes
    """
    print("🔗 Extracting EFC core edges from Neo4j...")
    
    edges = []
    
    with driver.session() as session:
        # Build edge type filter
        edge_filter = " OR ".join([f"type(r) = '{et}'" for et in CORE_EDGE_TYPES])
        
        query = f"""
        MATCH (source)-[r]->(target)
        WHERE (source.id IN $node_ids OR elementId(source) IN $node_ids)
          AND (target.id IN $node_ids OR elementId(target) IN $node_ids)
          AND ({edge_filter})
        RETURN 
            COALESCE(source.id, elementId(source)) as source_id,
            COALESCE(target.id, elementId(target)) as target_id,
            type(r) as edge_type,
            properties(r) as props
        """
        
        result = session.run(query, node_ids=list(node_ids))
        
        for record in result:
            props = record["props"] or {}
            
            edge = GNNEdge(
                source_id=record["source_id"],
                target_id=record["target_id"],
                type=record["edge_type"],
                weight=float(props.get("weight", 1.0)),
                properties=props
            )
            
            edges.append(edge)
    
    print(f"   ✅ Extracted {len(edges)} core edges")
    return edges

# ============================================================
# STEP 3: GENERATE TEXT EMBEDDINGS FOR NODES
# ============================================================

def generate_embeddings(nodes: List[GNNNode]) -> List[GNNNode]:
    """
    Generate embeddings for node descriptions using Cohere (or random for testing)
    """
    print("🧠 Generating text embeddings for nodes...")
    
    # Prepare texts
    texts = []
    for node in nodes:
        # Create canonical description
        desc = f"{node.name}"
        if node.metadata.get("description"):
            desc += f": {node.metadata['description']}"
        elif node.metadata.get("definition"):
            desc += f": {node.metadata['definition']}"
        
        texts.append(desc)
    
    if COHERE_AVAILABLE:
        # Generate embeddings in batches using Cohere
        cohere_client = cohere.Client(COHERE_API_KEY)
        
        batch_size = 96
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            response = cohere_client.embed(
                texts=batch,
                model="embed-english-v3.0",
                input_type="search_document"
            )
            all_embeddings.extend(response.embeddings)
            print(f"     Embedded {min(i+batch_size, len(texts))}/{len(texts)} nodes...", end='\r')
        
        print(f"     ✅ Generated {len(all_embeddings)} embeddings")
    else:
        # Fallback: Use random embeddings for testing
        print("     ⚠️  Using random embeddings (Cohere unavailable)")
        embedding_dim = 1024  # Same as Cohere embed-english-v3.0
        all_embeddings = [
            np.random.randn(embedding_dim).astype(np.float32) 
            for _ in texts
        ]
        # Normalize
        all_embeddings = [e / np.linalg.norm(e) for e in all_embeddings]
        print(f"     ✅ Generated {len(all_embeddings)} random embeddings (dim={embedding_dim})")
    
    # Assign embeddings to nodes
    for node, embedding in zip(nodes, all_embeddings):
        node.text_embedding = np.array(embedding, dtype=np.float32)
    
    return nodes

# ============================================================
# STEP 4: BUILD PyTorch Geometric DATA STRUCTURE
# ============================================================

def build_pyg_data(nodes: List[GNNNode], edges: List[GNNEdge]) -> Dict:
    """
    Build PyTorch Geometric compatible data structure
    """
    print("🏗️  Building PyTorch Geometric data structure...")
    
    # Create node ID mapping
    node_id_to_idx = {node.id: idx for idx, node in enumerate(nodes)}
    
    # Node features matrix
    node_features = []
    
    for node in nodes:
        # Categorical features (one-hot)
        domain_vec = [1.0 if node.domain == d else 0.0 for d in DOMAINS]
        layer_vec = [1.0 if node.layer == l else 0.0 for l in LAYERS]
        type_vec = [1.0 if node.type == t else 0.0 for t in CORE_NODE_TYPES]
        
        # Scalar features
        scalars = [
            node.stability_score,
            float(node.mention_count_efc) / 100.0,  # Normalize
            float(node.mention_count_private) / 100.0,
            float(node.degree) / 50.0,
            1.0 if node.efc_core else 0.0
        ]
        
        # Text embedding
        text_emb = node.text_embedding.tolist()
        
        # Concatenate all features
        features = domain_vec + layer_vec + type_vec + scalars + text_emb
        node_features.append(features)
    
    node_features = np.array(node_features, dtype=np.float32)
    
    # Edge indices and types
    edge_index = []
    edge_types = []
    edge_weights = []
    
    for edge in edges:
        if edge.source_id in node_id_to_idx and edge.target_id in node_id_to_idx:
            source_idx = node_id_to_idx[edge.source_id]
            target_idx = node_id_to_idx[edge.target_id]
            
            edge_index.append([source_idx, target_idx])
            edge_types.append(CORE_EDGE_TYPES.index(edge.type))
            edge_weights.append(edge.weight)
    
    edge_index = np.array(edge_index, dtype=np.int64).T
    edge_types = np.array(edge_types, dtype=np.int64)
    edge_weights = np.array(edge_weights, dtype=np.float32)
    
    print(f"   ✅ Built graph: {len(nodes)} nodes, {len(edges)} edges")
    print(f"   📊 Feature dim: {node_features.shape[1]}")
    
    return {
        "x": torch.from_numpy(node_features),
        "edge_index": torch.from_numpy(edge_index),
        "edge_type": torch.from_numpy(edge_types),
        "edge_weight": torch.from_numpy(edge_weights),
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "node_id_to_idx": node_id_to_idx,
        "idx_to_node_id": {idx: node.id for idx, node in enumerate(nodes)},
        "node_metadata": [
            {
                "id": node.id,
                "neo4j_id": node.neo4j_id,
                "type": node.type,
                "name": node.name,
                "domain": node.domain,
                "layer": node.layer,
                "efc_core": node.efc_core
            }
            for node in nodes
        ],
        "edge_type_names": CORE_EDGE_TYPES,
        "domain_names": DOMAINS,
        "layer_names": LAYERS
    }

# ============================================================
# MAIN EXPORT FUNCTION
# ============================================================

def export_gnn_graph(output_path: str = "symbiose_gnn_output/efc_core_graph.pt"):
    """
    Main export function
    """
    print("\n🚀 GNN Export - EFC Core Graph")
    print("=" * 60)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Step 1: Extract nodes
        nodes = extract_core_nodes(driver)
        
        if len(nodes) == 0:
            print("⚠️  No EFC core nodes found in Neo4j!")
            print("   Make sure you have Concept/Equation/Model nodes with proper labels")
            return
        
        # Step 2: Extract edges
        node_ids = {node.id for node in nodes}
        edges = extract_core_edges(driver, node_ids)
        
        # Step 3: Generate embeddings
        nodes = generate_embeddings(nodes)
        
        # Step 4: Build PyG data
        data = build_pyg_data(nodes, edges)
        
        # Save to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save(data, output_file)
        
        print(f"\n✅ GNN graph exported to: {output_file}")
        print(f"   📊 {data['num_nodes']} nodes, {data['num_edges']} edges")
        print(f"   🔢 Feature dimension: {data['x'].shape[1]}")
        print(f"   🏷️  Edge types: {len(CORE_EDGE_TYPES)}")
        
    finally:
        driver.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export EFC core graph for GNN training")
    parser.add_argument("--output", default="symbiose_gnn_output/efc_core_graph.pt", help="Output file path")
    
    args = parser.parse_args()
    
    export_gnn_graph(args.output)
