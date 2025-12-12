#!/usr/bin/env python3
"""
Semantic Augmentation Engine
=============================

Transforms flat RAG graph into structured knowledge graph by:
1. Analyzing chunk-concept relationships
2. Extracting semantic structure (hypotheses, mechanisms, relations)
3. Building theory-level graph with proper ontology

This is a ONE-TIME augmentation of existing data.
Future ingests will use updated orchestrator.

Usage:
    python tools/semantic_augmenter.py --batch-size 50 --max-concepts 1000
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase
import openai

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# Load ontology
ONTOLOGY_PATH = Path(__file__).parent.parent / "schema" / "symbiose_ontology.json"
with open(ONTOLOGY_PATH) as f:
    ONTOLOGY = json.load(f)

# ============================================================
# ANALYSIS PROMPT
# ============================================================

ANALYSIS_PROMPT = """You are a semantic structure analyzer for scientific knowledge graphs.

Given a CONCEPT and the TEXT CHUNKS that mention it, extract:

1. **Node Types**: Classify what this concept represents:
   - Concept (theoretical entity)
   - Hypothesis (testable claim)
   - Mechanism (causal process)
   - Equation (mathematical formulation)
   - Model (coherent framework)
   - Assumption (foundational premise)
   - Observation (empirical data)
   - Prediction (testable consequence)

2. **Properties**:
   - domain (cosmology, thermodynamics, quantum, information, cognition, meta, general)
   - layer (formal, applied, meta, cognitive, computational)
   - definition (concise explanation)

3. **Relationships**: What does this concept DO in the theory?
   Identify relationships like:
   - SUPPORTS (strengthens another concept)
   - CONTRADICTS (conflicts with)
   - DERIVES_FROM (logically follows from)
   - PART_OF (component of larger structure)
   - CAUSES (causal relationship)
   - EXPLAINS (provides explanation)
   - DEPENDS_ON (functional dependency)
   - IMPLIES (logical implication)
   - CONSTRAINS (sets boundaries)
   - ENABLES (makes possible)
   - TESTS (empirically validates)

Output JSON format:
{
  "primary_type": "Concept|Hypothesis|Mechanism|Equation|Model|Assumption|Observation|Prediction",
  "properties": {
    "domain": "...",
    "layer": "...",
    "definition": "...",
    "confidence": "speculative|provisional|established|foundational"
  },
  "relationships": [
    {
      "type": "SUPPORTS|CONTRADICTS|DERIVES_FROM|...",
      "target_concept": "name of related concept",
      "properties": {
        "strength": 0.0-1.0,
        "reasoning": "brief explanation"
      }
    }
  ],
  "extracted_entities": [
    {
      "name": "...",
      "type": "Hypothesis|Mechanism|Equation|...",
      "description": "..."
    }
  ]
}

Be conservative: only extract what is CLEARLY stated or strongly implied.
"""

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ConceptAnalysis:
    """Analysis result for one concept"""
    concept_name: str
    primary_type: str
    properties: Dict
    relationships: List[Dict]
    extracted_entities: List[Dict]
    chunk_count: int

# ============================================================
# NEO4J QUERIES
# ============================================================

def get_concepts_with_chunks(driver, limit: int = None) -> List[Tuple[str, List[str]]]:
    """
    Get all concepts with their associated chunk texts.
    
    Returns:
        List of (concept_name, [chunk_texts])
    """
    with driver.session() as session:
        query = """
        MATCH (concept:Concept)<-[:MENTIONS]-(chunk:Chunk)
        WHERE chunk.authority = 'PRIMARY' AND chunk.trust >= 1.0
        WITH concept.name as name, collect(chunk.text) as chunks
        RETURN name, chunks
        ORDER BY size(chunks) DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = session.run(query)
        return [(record["name"], record["chunks"]) for record in result]

def apply_augmentation(driver, analysis: ConceptAnalysis):
    """
    Apply semantic augmentation to graph:
    1. Update concept node type and properties
    2. Create new entity nodes
    3. Create semantic relationships
    """
    with driver.session() as session:
        # 1. Update concept node
        session.run("""
        MATCH (c:Concept {name: $name})
        SET c.primary_type = $primary_type,
            c.domain = $domain,
            c.layer = $layer,
            c.definition = $definition,
            c.confidence = $confidence
        """, {
            "name": analysis.concept_name,
            "primary_type": analysis.primary_type,
            **analysis.properties
        })
        
        # 2. Create extracted entities
        for entity in analysis.extracted_entities:
            # Determine node label
            label = entity["type"]
            
            session.run(f"""
            MERGE (n:{label} {{name: $name}})
            ON CREATE SET
                n.description = $description,
                n.source = 'semantic_augmentation',
                n.created_at = datetime()
            """, {
                "name": entity["name"],
                "description": entity.get("description", "")
            })
            
            # Link to original concept
            session.run(f"""
            MATCH (c:Concept {{name: $concept_name}})
            MATCH (e:{label} {{name: $entity_name}})
            MERGE (c)-[:RELATES_TO]->(e)
            """, {
                "concept_name": analysis.concept_name,
                "entity_name": entity["name"]
            })
        
        # 3. Create semantic relationships
        for rel in analysis.relationships:
            rel_type = rel["type"]
            target = rel["target_concept"]
            props = rel.get("properties", {})
            
            # Find or create target concept
            session.run("""
            MERGE (target:Concept {name: $target_name})
            ON CREATE SET target.source = 'semantic_augmentation'
            """, {"target_name": target})
            
            # Create relationship
            session.run(f"""
            MATCH (source:Concept {{name: $source_name}})
            MATCH (target:Concept {{name: $target_name}})
            MERGE (source)-[r:{rel_type}]->(target)
            SET r += $properties
            """, {
                "source_name": analysis.concept_name,
                "target_name": target,
                "properties": props
            })

# ============================================================
# LLM ANALYSIS
# ============================================================

def analyze_concept(concept_name: str, chunks: List[str]) -> ConceptAnalysis:
    """
    Use LLM to analyze concept and extract semantic structure.
    """
    # Limit context size (max 5 chunks, 3000 chars each)
    context_chunks = chunks[:5]
    context_text = "\n\n---\n\n".join([c[:3000] for c in context_chunks])
    
    messages = [
        {"role": "system", "content": ANALYSIS_PROMPT},
        {"role": "user", "content": f"""
Concept: {concept_name}

Context (from {len(chunks)} chunks):
{context_text}

Analyze this concept and provide structured output.
"""}
    ]
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return ConceptAnalysis(
            concept_name=concept_name,
            primary_type=result.get("primary_type", "Concept"),
            properties=result.get("properties", {}),
            relationships=result.get("relationships", []),
            extracted_entities=result.get("extracted_entities", []),
            chunk_count=len(chunks)
        )
        
    except Exception as e:
        print(f"  ⚠️  Analysis failed: {e}")
        return ConceptAnalysis(
            concept_name=concept_name,
            primary_type="Concept",
            properties={},
            relationships=[],
            extracted_entities=[],
            chunk_count=len(chunks)
        )

# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Semantic augmentation of knowledge graph")
    parser.add_argument("--batch-size", type=int, default=50, help="Concepts per batch")
    parser.add_argument("--max-concepts", type=int, help="Limit total concepts (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze but don't write to Neo4j")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧠 SEMANTIC AUGMENTATION ENGINE")
    print("=" * 80)
    print()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Get concepts
    print(f"📊 Loading concepts from Neo4j...")
    concepts = get_concepts_with_chunks(driver, limit=args.max_concepts)
    print(f"   Found {len(concepts)} concepts with PRIMARY chunks")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - will not write to Neo4j")
        print()
    
    # Process in batches
    processed = 0
    augmented = 0
    errors = 0
    
    for i in range(0, len(concepts), args.batch_size):
        batch = concepts[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        total_batches = (len(concepts) + args.batch_size - 1) // args.batch_size
        
        print(f"📦 Batch {batch_num}/{total_batches} ({len(batch)} concepts)")
        print("-" * 80)
        
        for concept_name, chunks in batch:
            processed += 1
            print(f"[{processed}/{len(concepts)}] Analyzing: {concept_name} ({len(chunks)} chunks)")
            
            try:
                # Analyze
                analysis = analyze_concept(concept_name, chunks)
                
                # Apply to graph
                if not args.dry_run:
                    apply_augmentation(driver, analysis)
                
                # Report
                print(f"  ✅ Type: {analysis.primary_type}")
                print(f"     Domain: {analysis.properties.get('domain', 'N/A')}")
                print(f"     Relations: {len(analysis.relationships)}")
                print(f"     Extracted: {len(analysis.extracted_entities)}")
                
                augmented += 1
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                errors += 1
            
            print()
        
        print()
    
    # Summary
    print("=" * 80)
    print("✅ AUGMENTATION COMPLETE")
    print("=" * 80)
    print(f"Processed:  {processed}")
    print(f"Augmented:  {augmented}")
    print(f"Errors:     {errors}")
    print()
    
    # Final stats
    if not args.dry_run:
        with driver.session() as session:
            # Node types
            labels = session.run("CALL db.labels()").data()
            print("📦 Node Types:")
            for label in labels:
                count = session.run(f"MATCH (n:{label['label']}) RETURN count(n) as cnt").single()["cnt"]
                print(f"   {label['label']}: {count}")
            
            print()
            
            # Relationship types
            rels = session.run("CALL db.relationshipTypes()").data()
            print("🔗 Relationship Types:")
            for rel in rels:
                count = session.run(f"MATCH ()-[r:{rel['relationshipType']}]->() RETURN count(r) as cnt").single()["cnt"]
                print(f"   {rel['relationshipType']}: {count}")
    
    driver.close()

if __name__ == "__main__":
    main()
