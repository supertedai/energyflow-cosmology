#!/usr/bin/env python3
"""
neo4j_graph_layer.py - Neo4j Graph Memory Layer
================================================

LAG 2.5: NEO4J GRAPH LAYER
"Strukturenes struktur"

This stores:
- Entity relationships (Person, Concept, Module, System)
- Hierarchical structures (PART_OF, CONTAINS, DERIVES_FROM)
- Cross-domain connections (RELATES_TO, SUPPORTS, CONSTRAINS)
- Temporal evolution (EVOLVES_INTO, REPLACES)
- Meta-structure (how the system itself is organized)

This is NOT:
- Raw text storage (that's SMM)
- Absolute facts (that's CMC)
- Just another database

This is:
- The skeleton that holds everything together
- The map of how concepts relate
- The memory of structure itself

Architecture:
    Entities → Relationships → Cypher Queries → Graph Insights

Purpose:
    Answer questions like:
    - "Hvilke lag har symbiosen?"
    - "Hvordan henger EFC og entropy sammen?"
    - "Hva er alle modulene i systemet?"
    - "Hvordan har teorien utviklet seg?"
"""

import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()


# ============================================================
# DATATYPER
# ============================================================

@dataclass
class GraphNode:
    """
    A node in the knowledge graph.
    
    Types:
    - Person: Morten, family members
    - Concept: EFC, entropy, energy flow, scale invariance
    - Module: CMC, SMM, DDE, AME, MLC
    - System: Symbiose, OpenWebUI, Neo4j
    - Domain: cosmology, identity, health, tech
    - Theory: EFC v1.0, EFC v2.0, H-model
    """
    
    id: str  # Unique identifier
    label: str  # Node type (Person, Concept, Module, etc.)
    name: str  # Display name
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_neo4j(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible dict."""
        props = {
            "id": self.id,
            "name": self.name,
            **self.properties
        }
        return props


@dataclass
class GraphRelationship:
    """
    A relationship between nodes.
    
    Types:
    - PART_OF: Module is part of System
    - HAS_CHILD: Person has Person
    - RELATES_TO: Concept relates to Concept
    - SUPPORTS: Evidence supports Theory
    - CONSTRAINS: Theory constrains Prediction
    - DERIVES_FROM: Theory derives from Theory
    - EVOLVES_INTO: Version evolves into Version
    - IMPLEMENTS: Module implements Concept
    """
    
    from_id: str
    to_id: str
    type: str  # Relationship type
    properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# NEO4J GRAPH LAYER
# ============================================================

class Neo4jGraphLayer:
    """
    Graph memory layer using Neo4j.
    
    This complements CMC and SMM:
    - CMC: Individual facts (key-value)
    - SMM: Text chunks (semantic search)
    - Neo4j: Relationships (graph queries)
    
    Together they form complete memory.
    """
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j URI (default from env)
            user: Neo4j user (default from env)
            password: Neo4j password (default from env)
        """
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            print("⚠️  Neo4j credentials not found - graph layer disabled", file=sys.stderr)
            self.driver = None
            return
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            print("✨ Neo4j Graph Layer initialized", file=sys.stderr)
            print("🕸️  Structural memory active", file=sys.stderr)
        
        except Exception as e:
            print(f"⚠️  Neo4j connection failed: {e}", file=sys.stderr)
            self.driver = None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    # --------------------------------------------------------
    # NODE OPERATIONS
    # --------------------------------------------------------
    
    def create_node(self, node: GraphNode) -> bool:
        """
        Create a node in the graph.
        
        Args:
            node: GraphNode to create
        
        Returns:
            Success status
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = f"""
                MERGE (n:{node.label} {{id: $id}})
                SET n += $props
                RETURN n
                """
                
                session.run(
                    query,
                    id=node.id,
                    props=node.to_neo4j()
                )
            
            print(f"✅ Created node: {node.label}:{node.name}", file=sys.stderr)
            return True
        
        except Exception as e:
            print(f"❌ Failed to create node: {e}", file=sys.stderr)
            return False
    
    def get_node(self, node_id: str, label: Optional[str] = None) -> Optional[GraphNode]:
        """
        Retrieve a node by ID.
        
        Args:
            node_id: Node identifier
            label: Optional label filter
        
        Returns:
            GraphNode or None
        """
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                if label:
                    query = f"MATCH (n:{label} {{id: $id}}) RETURN n, labels(n) as labels"
                else:
                    query = "MATCH (n {id: $id}) RETURN n, labels(n) as labels"
                
                result = session.run(query, id=node_id)
                record = result.single()
                
                if not record:
                    return None
                
                node_data = dict(record["n"])
                node_labels = record["labels"]
                
                return GraphNode(
                    id=node_data["id"],
                    label=node_labels[0] if node_labels else "Unknown",
                    name=node_data.get("name", ""),
                    properties={k: v for k, v in node_data.items() if k not in ["id", "name"]}
                )
        
        except Exception as e:
            print(f"❌ Failed to get node: {e}", file=sys.stderr)
            return None
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and all its relationships.
        
        Args:
            node_id: Node to delete
        
        Returns:
            Success status
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run(
                    "MATCH (n {id: $id}) DETACH DELETE n",
                    id=node_id
                )
            
            print(f"🗑️  Deleted node: {node_id}", file=sys.stderr)
            return True
        
        except Exception as e:
            print(f"❌ Failed to delete node: {e}", file=sys.stderr)
            return False
    
    # --------------------------------------------------------
    # RELATIONSHIP OPERATIONS
    # --------------------------------------------------------
    
    def create_relationship(self, rel: GraphRelationship) -> bool:
        """
        Create a relationship between nodes.
        
        Args:
            rel: GraphRelationship to create
        
        Returns:
            Success status
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (a {{id: $from_id}})
                MATCH (b {{id: $to_id}})
                MERGE (a)-[r:{rel.type}]->(b)
                SET r += $props
                RETURN r
                """
                
                session.run(
                    query,
                    from_id=rel.from_id,
                    to_id=rel.to_id,
                    props=rel.properties
                )
            
            print(f"🔗 Created relationship: {rel.from_id} -{rel.type}-> {rel.to_id}", file=sys.stderr)
            return True
        
        except Exception as e:
            print(f"❌ Failed to create relationship: {e}", file=sys.stderr)
            return False
    
    def get_relationships(
        self,
        node_id: str,
        direction: str = "both",  # "in", "out", "both"
        rel_type: Optional[str] = None
    ) -> List[Tuple[GraphNode, str, GraphNode]]:
        """
        Get all relationships for a node.
        
        Args:
            node_id: Node to query
            direction: Relationship direction
            rel_type: Optional relationship type filter
        
        Returns:
            List of (from_node, rel_type, to_node) tuples
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                # Build query based on direction
                if direction == "out":
                    pattern = "(a {id: $id})-[r]->(b)"
                elif direction == "in":
                    pattern = "(a)<-[r]-(b {id: $id})"
                else:  # both
                    pattern = "(a {id: $id})-[r]-(b)"
                
                if rel_type:
                    pattern = pattern.replace("-[r]-", f"-[r:{rel_type}]-")
                
                query = f"""
                MATCH {pattern}
                RETURN a, type(r) as rel_type, b, labels(a) as a_labels, labels(b) as b_labels
                """
                
                results = session.run(query, id=node_id)
                
                relationships = []
                for record in results:
                    a_data = dict(record["a"])
                    b_data = dict(record["b"])
                    
                    from_node = GraphNode(
                        id=a_data["id"],
                        label=record["a_labels"][0] if record["a_labels"] else "Unknown",
                        name=a_data.get("name", ""),
                        properties={k: v for k, v in a_data.items() if k not in ["id", "name"]}
                    )
                    
                    to_node = GraphNode(
                        id=b_data["id"],
                        label=record["b_labels"][0] if record["b_labels"] else "Unknown",
                        name=b_data.get("name", ""),
                        properties={k: v for k, v in b_data.items() if k not in ["id", "name"]}
                    )
                    
                    relationships.append((from_node, record["rel_type"], to_node))
                
                return relationships
        
        except Exception as e:
            print(f"❌ Failed to get relationships: {e}", file=sys.stderr)
            return []
    
    # --------------------------------------------------------
    # GRAPH QUERIES
    # --------------------------------------------------------
    
    def find_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 5
    ) -> List[List[Tuple[str, str]]]:
        """
        Find paths between two nodes.
        
        Args:
            from_id: Start node
            to_id: End node
            max_depth: Maximum path length
        
        Returns:
            List of paths (each path is list of (node_name, rel_type))
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH path = (a {{id: $from_id}})-[*1..{max_depth}]-(b {{id: $to_id}})
                RETURN [node in nodes(path) | node.name] as node_names,
                       [rel in relationships(path) | type(rel)] as rel_types
                LIMIT 10
                """
                
                results = session.run(query, from_id=from_id, to_id=to_id)
                
                paths = []
                for record in results:
                    node_names = record["node_names"]
                    rel_types = record["rel_types"]
                    
                    path = [(node_names[i], rel_types[i]) for i in range(len(rel_types))]
                    path.append((node_names[-1], None))  # Last node has no outgoing rel
                    
                    paths.append(path)
                
                return paths
        
        except Exception as e:
            print(f"❌ Failed to find path: {e}", file=sys.stderr)
            return []
    
    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1,
        limit: int = 20
    ) -> List[GraphNode]:
        """
        Get neighboring nodes.
        
        Args:
            node_id: Center node
            depth: How many hops
            limit: Max results
        
        Returns:
            List of neighboring nodes
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (a {{id: $id}})-[*1..{depth}]-(b)
                RETURN DISTINCT b, labels(b) as labels
                LIMIT {limit}
                """
                
                results = session.run(query, id=node_id)
                
                neighbors = []
                for record in results:
                    node_data = dict(record["b"])
                    node_labels = record["labels"]
                    
                    neighbor = GraphNode(
                        id=node_data["id"],
                        label=node_labels[0] if node_labels else "Unknown",
                        name=node_data.get("name", ""),
                        properties={k: v for k, v in node_data.items() if k not in ["id", "name"]}
                    )
                    neighbors.append(neighbor)
                
                return neighbors
        
        except Exception as e:
            print(f"❌ Failed to get neighbors: {e}", file=sys.stderr)
            return []
    
    def query_structure(self, question: str) -> Optional[str]:
        """
        Answer structural questions using graph.
        
        Examples:
        - "Hvilke lag har symbiosen?"
        - "Hvem er barna til Morten?"
        - "Hvilke moduler implementerer CMC?"
        
        Args:
            question: Natural language question
        
        Returns:
            Answer string or None
        """
        if not self.driver:
            return None
        
        # Simple pattern matching (can be enhanced with LLM)
        question_lower = question.lower()
        
        try:
            with self.driver.session() as session:
                # Pattern: "hvilke lag" / "layers"
                if "lag" in question_lower or "layer" in question_lower:
                    if "symbiose" in question_lower:
                        query = """
                        MATCH (m:Module)-[:PART_OF]->(s:System {name: 'Symbiose'})
                        RETURN m.name as name
                        ORDER BY m.layer_number
                        """
                        results = session.run(query)
                        layers = [r["name"] for r in results]
                        
                        if layers:
                            return f"Symbiosen har {len(layers)} lag: {', '.join(layers)}"
                
                # Pattern: "barn" / "children"
                if "barn" in question_lower or "children" in question_lower:
                    query = """
                    MATCH (p:Person)-[:HAS_CHILD]->(c:Person)
                    WHERE p.name =~ '(?i).*morten.*'
                    RETURN c.name as name
                    """
                    results = session.run(query)
                    children = [r["name"] for r in results]
                    
                    if children:
                        return f"Morten har {len(children)} barn: {', '.join(children)}"
                
                # Pattern: "hvordan henger ... sammen" / "how are ... related"
                if "henger" in question_lower or "related" in question_lower:
                    # Extract concepts (simple version)
                    words = question_lower.split()
                    # This is a stub - would need better NLP
                    return "Bruker find_path() for å finne relasjoner mellom konsepter"
                
                return None
        
        except Exception as e:
            print(f"❌ Query structure failed: {e}", file=sys.stderr)
            return None
    
    # --------------------------------------------------------
    # UTILITY
    # --------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if not self.driver:
            return {"enabled": False}
        
        try:
            with self.driver.session() as session:
                # Count nodes by label
                node_counts = {}
                result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
                for record in result:
                    node_counts[record["label"]] = record["count"]
                
                # Count relationships by type
                rel_counts = {}
                result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                for record in result:
                    rel_counts[record["type"]] = record["count"]
                
                return {
                    "enabled": True,
                    "nodes": node_counts,
                    "relationships": rel_counts,
                    "total_nodes": sum(node_counts.values()),
                    "total_relationships": sum(rel_counts.values())
                }
        
        except Exception as e:
            print(f"❌ Failed to get stats: {e}", file=sys.stderr)
            return {"enabled": True, "error": str(e)}


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Neo4j Graph Layer")
    print("=" * 60)
    
    # Initialize
    graph = Neo4jGraphLayer()
    
    if not graph.driver:
        print("❌ Neo4j not available - skipping tests")
        sys.exit(0)
    
    # Test 1: Create nodes
    print("\n1️⃣ Creating nodes...")
    
    # User
    user_node = GraphNode(
        id="user_morten",
        label="Person",
        name="Morten",
        properties={"role": "creator", "domain_affinity": "parallel"}
    )
    graph.create_node(user_node)
    
    # Children
    for child_name in ["Joakim", "Isak Andreas", "Susanna"]:
        child_node = GraphNode(
            id=f"person_{child_name.lower().replace(' ', '_')}",
            label="Person",
            name=child_name,
            properties={"relation": "child"}
        )
        graph.create_node(child_node)
    
    # System
    symbiose_node = GraphNode(
        id="system_symbiose",
        label="System",
        name="Symbiose",
        properties={"version": "3.0", "type": "memory_architecture"}
    )
    graph.create_node(symbiose_node)
    
    # Modules
    modules = [
        ("CMC", "Canonical Memory Core", 1),
        ("SMM", "Semantic Mesh Memory", 2),
        ("Neo4j", "Graph Layer", 2.5),
        ("DDE", "Dynamic Domain Engine", 3),
        ("AME", "Adaptive Memory Enforcer", 4),
        ("MLC", "Meta-Learning Cortex", 5)
    ]
    
    for abbr, name, layer_num in modules:
        module_node = GraphNode(
            id=f"module_{abbr.lower()}",
            label="Module",
            name=name,
            properties={"abbreviation": abbr, "layer_number": layer_num}
        )
        graph.create_node(module_node)
    
    # Test 2: Create relationships
    print("\n2️⃣ Creating relationships...")
    
    # Family
    for child_name in ["Joakim", "Isak Andreas", "Susanna"]:
        rel = GraphRelationship(
            from_id="user_morten",
            to_id=f"person_{child_name.lower().replace(' ', '_')}",
            type="HAS_CHILD",
            properties={"verified": True}
        )
        graph.create_relationship(rel)
    
    # System structure
    for abbr, _, _ in modules:
        rel = GraphRelationship(
            from_id=f"module_{abbr.lower()}",
            to_id="system_symbiose",
            type="PART_OF",
            properties={"essential": True}
        )
        graph.create_relationship(rel)
    
    # Inter-module relationships
    graph.create_relationship(GraphRelationship(
        from_id="module_ame",
        to_id="module_cmc",
        type="USES",
        properties={"purpose": "fact_retrieval"}
    ))
    
    graph.create_relationship(GraphRelationship(
        from_id="module_ame",
        to_id="module_smm",
        type="USES",
        properties={"purpose": "context_retrieval"}
    ))
    
    # Test 3: Query
    print("\n3️⃣ Testing queries...")
    
    # Get children
    children_rels = graph.get_relationships("user_morten", direction="out", rel_type="HAS_CHILD")
    print(f"   Morten har {len(children_rels)} barn:")
    for from_node, rel_type, to_node in children_rels:
        print(f"      - {to_node.name}")
    
    # Get system modules
    module_rels = graph.get_relationships("system_symbiose", direction="in", rel_type="PART_OF")
    print(f"   Symbiose har {len(module_rels)} moduler:")
    for from_node, rel_type, to_node in module_rels:
        print(f"      - {from_node.name}")
    
    # Test 4: Structural questions
    print("\n4️⃣ Testing structural questions...")
    
    questions = [
        "Hvilke lag har symbiosen?",
        "Hvor mange barn har Morten?",
    ]
    
    for q in questions:
        answer = graph.query_structure(q)
        print(f"   Q: {q}")
        print(f"   A: {answer or 'Ingen svar funnet'}")
    
    # Test 5: Stats
    print("\n5️⃣ Graph statistics...")
    stats = graph.get_stats()
    print(f"   Nodes: {stats.get('total_nodes', 0)}")
    print(f"   Relationships: {stats.get('total_relationships', 0)}")
    print(f"   By type: {stats.get('nodes', {})}")
    
    print("\n" + "=" * 60)
    print("✅ Neo4j Graph Layer operational!")
    
    # Cleanup
    graph.close()
