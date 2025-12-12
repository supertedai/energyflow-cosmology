#!/usr/bin/env python3
"""
export_efc_for_gnn.py - Export EFC Graph for Offline GNN Training
=================================================================

Purpose: Extract clean EFC graph data (nodes, edges, features) to static files
         for offline GNN training. NO runtime modifications to Neo4j.

Output files:
- symbiose_gnn_output/efc_nodes.jsonl        (node features)
- symbiose_gnn_output/efc_edges.jsonl        (edge list)
- symbiose_gnn_output/efc_metadata.json      (graph statistics)

Safety:
- Read-only operation
- No writes to Neo4j/Qdrant
- Complete snapshot at export time
- Versioned output (timestamp)

Usage:
    python tools/export_efc_for_gnn.py
    
    # With filters
    python tools/export_efc_for_gnn.py --min-degree 2 --exclude-isolated
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

OUTPUT_DIR = Path("symbiose_gnn_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# EXPORT FUNCTIONS
# ============================================================

def export_efc_graph(
    min_degree: int = 0,
    exclude_isolated: bool = False,
    include_chunks: bool = False
) -> Dict:
    """
    Export EFC graph to offline files for GNN training
    
    Args:
        min_degree: Minimum node degree (connections) to include
        exclude_isolated: Skip nodes with no connections
        include_chunks: Include :Chunk nodes (default: only :Concept)
        
    Returns:
        Dictionary with export statistics
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        print("🔍 Fetching EFC graph from Neo4j...")
        print(f"   Filters: min_degree={min_degree}, exclude_isolated={exclude_isolated}")
        
        # Step 1: Export nodes
        nodes_file = OUTPUT_DIR / f"efc_nodes_{timestamp}.jsonl"
        node_count = _export_nodes(
            driver, 
            nodes_file, 
            min_degree=min_degree,
            exclude_isolated=exclude_isolated,
            include_chunks=include_chunks
        )
        
        # Step 2: Export edges
        edges_file = OUTPUT_DIR / f"efc_edges_{timestamp}.jsonl"
        edge_count = _export_edges(driver, edges_file, include_chunks=include_chunks)
        
        # Step 3: Export metadata
        metadata_file = OUTPUT_DIR / f"efc_metadata_{timestamp}.json"
        metadata = _export_metadata(driver, node_count, edge_count, include_chunks=include_chunks)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Export complete:")
        print(f"   Nodes: {node_count}")
        print(f"   Edges: {edge_count}")
        print(f"   Files:")
        print(f"     - {nodes_file}")
        print(f"     - {edges_file}")
        print(f"     - {metadata_file}")
        
        # Create symlinks to latest
        _create_latest_symlinks(timestamp)
        
        return {
            'timestamp': timestamp,
            'node_count': node_count,
            'edge_count': edge_count,
            'files': {
                'nodes': str(nodes_file),
                'edges': str(edges_file),
                'metadata': str(metadata_file)
            }
        }
        
    finally:
        driver.close()


def _export_nodes(
    driver,
    output_file: Path,
    min_degree: int = 0,
    exclude_isolated: bool = False,
    include_chunks: bool = False
) -> int:
    """Export node features to JSONL"""
    
    # Build query based on filters
    if include_chunks:
        labels = "WHERE (n:Concept OR n:Chunk)"
    else:
        labels = "WHERE n:Concept"
    
    query = f"""
        MATCH (n)
        {labels}
        OPTIONAL MATCH (n)-[r]-(m)
        WITH n, count(r) AS degree
        WHERE degree >= $min_degree
        RETURN 
            id(n) AS node_id,
            labels(n) AS labels,
            n.name AS name,
            n.text AS text,
            n.chunk_id AS chunk_id,
            n.document_id AS document_id,
            n.timestamp AS timestamp,
            degree,
            CASE 
                WHEN n:Concept THEN coalesce(n.frequency, 1)
                ELSE 1
            END AS frequency
        ORDER BY degree DESC
    """
    
    count = 0
    with driver.session() as session:
        with open(output_file, 'w') as f:
            result = session.run(query, min_degree=min_degree)
            
            for record in result:
                # Skip isolated nodes if requested
                if exclude_isolated and record['degree'] == 0:
                    continue
                
                node = {
                    'node_id': record['node_id'],
                    'labels': record['labels'],
                    'name': record['name'],
                    'text': record['text'][:500] if record['text'] else None,  # Truncate long text
                    'chunk_id': record['chunk_id'],
                    'document_id': record['document_id'],
                    'timestamp': record['timestamp'],
                    'degree': record['degree'],
                    'frequency': record['frequency']
                }
                
                f.write(json.dumps(node) + '\n')
                count += 1
    
    print(f"   ✓ Exported {count} nodes")
    return count


def _export_edges(
    driver,
    output_file: Path,
    include_chunks: bool = False
) -> int:
    """Export edge list to JSONL"""
    
    if include_chunks:
        labels = "WHERE (a:Concept OR a:Chunk) AND (b:Concept OR b:Chunk)"
    else:
        labels = "WHERE a:Concept AND b:Concept"
    
    # Get all relationships between EFC nodes
    query = f"""
        MATCH (a)-[r]->(b)
        {labels}
        RETURN 
            id(a) AS source_id,
            id(b) AS target_id,
            type(r) AS rel_type,
            a.name AS source_name,
            b.name AS target_name
    """
    
    count = 0
    with driver.session() as session:
        with open(output_file, 'w') as f:
            result = session.run(query)
            
            for record in result:
                edge = {
                    'source_id': record['source_id'],
                    'target_id': record['target_id'],
                    'rel_type': record['rel_type'],
                    'source_name': record['source_name'],
                    'target_name': record['target_name']
                }
                
                f.write(json.dumps(edge) + '\n')
                count += 1
    
    print(f"   ✓ Exported {count} edges")
    return count


def _export_metadata(
    driver,
    node_count: int,
    edge_count: int,
    include_chunks: bool = False
) -> Dict:
    """Collect graph statistics"""
    
    with driver.session() as session:
        # Get relationship type distribution
        rel_types = session.run("""
            MATCH (a)-[r]->(b)
            WHERE (a:Concept OR a:Chunk) AND (b:Concept OR b:Chunk)
            RETURN type(r) AS rel_type, count(r) AS count
            ORDER BY count DESC
        """).data()
        
        # Get degree distribution
        degree_stats = session.run("""
            MATCH (n)
            WHERE n:Concept OR n:Chunk
            OPTIONAL MATCH (n)-[r]-(m)
            WITH n, count(r) AS degree
            RETURN 
                min(degree) AS min_degree,
                max(degree) AS max_degree,
                avg(degree) AS avg_degree,
                percentileCont(degree, 0.5) AS median_degree
        """).single()
        
        # Get label distribution
        label_dist = session.run("""
            MATCH (n)
            WHERE n:Concept OR n:Chunk
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
        """).data()
    
    metadata = {
        'export_timestamp': datetime.now().isoformat(),
        'node_count': node_count,
        'edge_count': edge_count,
        'include_chunks': include_chunks,
        'relationship_types': rel_types,
        'degree_statistics': {
            'min': degree_stats['min_degree'],
            'max': degree_stats['max_degree'],
            'avg': float(degree_stats['avg_degree']) if degree_stats['avg_degree'] else 0,
            'median': float(degree_stats['median_degree']) if degree_stats['median_degree'] else 0
        },
        'label_distribution': label_dist,
        'graph_properties': {
            'directed': True,
            'weighted': False,
            'multigraph': False
        }
    }
    
    print(f"   ✓ Collected metadata")
    return metadata


def _create_latest_symlinks(timestamp: str):
    """Create symlinks to latest export files"""
    
    files = [
        (f"efc_nodes_{timestamp}.jsonl", "efc_nodes_latest.jsonl"),
        (f"efc_edges_{timestamp}.jsonl", "efc_edges_latest.jsonl"),
        (f"efc_metadata_{timestamp}.json", "efc_metadata_latest.json")
    ]
    
    for source, target in files:
        source_path = OUTPUT_DIR / source
        target_path = OUTPUT_DIR / target
        
        # Remove old symlink if exists
        if target_path.is_symlink() or target_path.exists():
            target_path.unlink()
        
        # Create new symlink
        target_path.symlink_to(source_path.name)
    
    print(f"   ✓ Created symlinks to latest exports")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Export EFC graph for offline GNN training"
    )
    parser.add_argument(
        '--min-degree',
        type=int,
        default=0,
        help="Minimum node degree to include (default: 0)"
    )
    parser.add_argument(
        '--exclude-isolated',
        action='store_true',
        help="Exclude nodes with no connections"
    )
    parser.add_argument(
        '--include-chunks',
        action='store_true',
        help="Include :Chunk nodes (default: only :Concept)"
    )
    
    args = parser.parse_args()
    
    export_efc_graph(
        min_degree=args.min_degree,
        exclude_isolated=args.exclude_isolated,
        include_chunks=args.include_chunks
    )


if __name__ == "__main__":
    main()
