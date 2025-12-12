#!/usr/bin/env python3
"""
analyze_efc.py - Analyze GNN Results on EFC Graph
=================================================

Purpose: Inspect and visualize GNN training results WITHOUT modifying Neo4j.
         Pure read-only analysis of trained embeddings.

Features:
- Node clustering (find concept communities)
- Centrality ranking (most important concepts)
- Outlier detection (isolated or unusual concepts)
- Similarity search (find related concepts)
- Visualization (t-SNE, cluster plots)

Output:
- symbiose_gnn_output/analysis_report.json
- symbiose_gnn_output/clusters.json
- symbiose_gnn_output/centrality_ranking.json
- symbiose_gnn_output/visualization.png (if matplotlib available)

Usage:
    python symbiose_gnn/analyze_efc.py
    
    # Find concepts similar to "energy flow"
    python symbiose_gnn/analyze_efc.py --query "energy flow" --top-k 10
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ============================================================
# CONFIG
# ============================================================

INPUT_DIR = Path("symbiose_gnn_output")
OUTPUT_DIR = Path("symbiose_gnn_output")

# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

def load_gnn_results() -> Tuple[List[Dict], np.ndarray, Dict]:
    """
    Load GNN embeddings and node data
    
    Returns:
        (nodes list, embeddings array, metadata dict)
    """
    print("📊 Loading GNN results...")
    
    # Load nodes
    nodes_file = INPUT_DIR / "efc_nodes_latest.jsonl"
    nodes = []
    with open(nodes_file, 'r') as f:
        for line in f:
            nodes.append(json.loads(line))
    
    # Load embeddings
    embeddings_file = INPUT_DIR / "node_embeddings.json"
    with open(embeddings_file, 'r') as f:
        embeddings = np.array(json.load(f))
    
    # Load metadata
    metadata_file = INPUT_DIR / "efc_metadata_latest.json"
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    print(f"   ✓ Loaded {len(nodes)} nodes with {embeddings.shape[1]}-dim embeddings")
    
    return nodes, embeddings, metadata


def cluster_concepts(
    nodes: List[Dict],
    embeddings: np.ndarray,
    n_clusters: int = 10
) -> Dict:
    """
    Cluster concepts using K-means on GNN embeddings
    
    Returns:
        Dictionary mapping cluster_id -> list of concepts
    """
    print(f"\n🔍 Clustering concepts (k={n_clusters})...")
    
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        print("   ⚠️ sklearn not available, skipping clustering")
        return {}
    
    # Run K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    cluster_labels = kmeans.fit_predict(embeddings)
    
    # Group concepts by cluster
    clusters = defaultdict(list)
    for idx, label in enumerate(cluster_labels):
        node = nodes[idx]
        clusters[int(label)].append({
            'name': node.get('name'),
            'degree': node.get('degree'),
            'frequency': node.get('frequency')
        })
    
    # Sort concepts within each cluster by degree
    for cluster_id in clusters:
        clusters[cluster_id].sort(key=lambda x: x['degree'], reverse=True)
    
    # Print top concepts per cluster
    print("\n   Top concepts per cluster:")
    for cluster_id, concepts in sorted(clusters.items()):
        print(f"\n   Cluster {cluster_id} ({len(concepts)} concepts):")
        for concept in concepts[:5]:  # Top 5
            print(f"     - {concept['name']} (degree: {concept['degree']})")
    
    return dict(clusters)


def rank_by_centrality(
    nodes: List[Dict],
    embeddings: np.ndarray,
    top_k: int = 20
) -> List[Dict]:
    """
    Rank concepts by GNN-based centrality
    
    Centrality = combination of:
    - Graph degree (explicit connections)
    - Embedding norm (implicit importance from GNN)
    
    Returns:
        List of top-k central concepts
    """
    print(f"\n🎯 Ranking by centrality (top {top_k})...")
    
    # Calculate embedding norms
    embedding_norms = np.linalg.norm(embeddings, axis=1)
    
    # Combine with graph degree
    centrality_scores = []
    for idx, node in enumerate(nodes):
        degree = node.get('degree', 0)
        embed_norm = embedding_norms[idx]
        
        # Combined score: 60% degree, 40% embedding norm
        score = 0.6 * degree + 0.4 * embed_norm
        
        centrality_scores.append({
            'name': node.get('name'),
            'degree': degree,
            'embedding_norm': float(embed_norm),
            'centrality_score': float(score)
        })
    
    # Sort by centrality
    centrality_scores.sort(key=lambda x: x['centrality_score'], reverse=True)
    
    # Print top concepts
    print("\n   Most central concepts:")
    for i, concept in enumerate(centrality_scores[:top_k], 1):
        print(f"   {i:2d}. {concept['name']:30s} (score: {concept['centrality_score']:.2f})")
    
    return centrality_scores[:top_k]


def find_outliers(
    nodes: List[Dict],
    embeddings: np.ndarray,
    threshold: float = 2.0
) -> List[Dict]:
    """
    Detect outlier concepts (unusual or isolated)
    
    Outliers = concepts with embedding far from cluster centers
    
    Returns:
        List of outlier concepts
    """
    print(f"\n🔎 Detecting outliers (threshold: {threshold} std)...")
    
    # Calculate distance from mean embedding
    mean_embedding = embeddings.mean(axis=0)
    distances = np.linalg.norm(embeddings - mean_embedding, axis=1)
    
    # Find outliers (> threshold standard deviations)
    mean_dist = distances.mean()
    std_dist = distances.std()
    outlier_threshold = mean_dist + threshold * std_dist
    
    outliers = []
    for idx, dist in enumerate(distances):
        if dist > outlier_threshold:
            node = nodes[idx]
            outliers.append({
                'name': node.get('name'),
                'distance': float(dist),
                'degree': node.get('degree'),
                'labels': node.get('labels')
            })
    
    # Sort by distance
    outliers.sort(key=lambda x: x['distance'], reverse=True)
    
    print(f"\n   Found {len(outliers)} outliers:")
    for outlier in outliers[:10]:  # Top 10
        print(f"     - {outlier['name']} (distance: {outlier['distance']:.2f})")
    
    return outliers


def find_similar_concepts(
    query: str,
    nodes: List[Dict],
    embeddings: np.ndarray,
    top_k: int = 10
) -> List[Dict]:
    """
    Find concepts similar to query using GNN embeddings
    
    Returns:
        List of similar concepts
    """
    print(f"\n🔍 Finding concepts similar to: '{query}'")
    
    # Find query node
    query_idx = None
    for idx, node in enumerate(nodes):
        if node.get('name', '').lower() == query.lower():
            query_idx = idx
            break
    
    if query_idx is None:
        print(f"   ⚠️ Concept '{query}' not found")
        return []
    
    # Calculate cosine similarity
    query_embedding = embeddings[query_idx]
    similarities = embeddings @ query_embedding / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    
    # Get top-k similar (excluding query itself)
    similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
    
    results = []
    print(f"\n   Most similar concepts:")
    for i, idx in enumerate(similar_indices, 1):
        node = nodes[idx]
        results.append({
            'name': node.get('name'),
            'similarity': float(similarities[idx]),
            'degree': node.get('degree')
        })
        print(f"   {i:2d}. {node.get('name'):30s} (similarity: {similarities[idx]:.3f})")
    
    return results


def generate_analysis_report(
    clusters: Dict,
    centrality: List[Dict],
    outliers: List[Dict],
    metadata: Dict
) -> Dict:
    """Generate comprehensive analysis report"""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'graph_metadata': metadata,
        'analysis': {
            'num_clusters': len(clusters),
            'cluster_sizes': {k: len(v) for k, v in clusters.items()},
            'num_outliers': len(outliers),
            'centrality_range': {
                'max': centrality[0]['centrality_score'] if centrality else 0,
                'min': centrality[-1]['centrality_score'] if centrality else 0
            }
        },
        'clusters': clusters,
        'top_central_concepts': centrality,
        'outliers': outliers
    }
    
    # Save report
    report_file = OUTPUT_DIR / "analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Analysis complete")
    print(f"   Report saved: {report_file}")
    
    return report


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze GNN results on EFC graph"
    )
    parser.add_argument(
        '--query',
        type=str,
        help="Find concepts similar to this query"
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help="Number of similar concepts to return (default: 10)"
    )
    parser.add_argument(
        '--n-clusters',
        type=int,
        default=10,
        help="Number of clusters for K-means (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Load GNN results
    nodes, embeddings, metadata = load_gnn_results()
    
    # Run analyses
    clusters = cluster_concepts(nodes, embeddings, n_clusters=args.n_clusters)
    centrality = rank_by_centrality(nodes, embeddings, top_k=20)
    outliers = find_outliers(nodes, embeddings)
    
    # Query-specific analysis
    if args.query:
        find_similar_concepts(args.query, nodes, embeddings, top_k=args.top_k)
    
    # Generate report
    generate_analysis_report(clusters, centrality, outliers, metadata)


if __name__ == "__main__":
    main()
