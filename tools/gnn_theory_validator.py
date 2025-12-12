#!/usr/bin/env python3
"""
GNN Theory Validator - 4-Step Validation Process
=================================================

Validates GNN-suggested relations against EFC theory using:

1. **Formal Consistency** - Energy conservation, ∇S direction, Ef role
2. **Theory Proximity** - How close to existing theory structure
3. **Energy/Entropy Intuition** - Does it enhance explanatory power?
4. **Integration Level** - TRIVIAL | USEFUL | DEEP classification

Workflow:
    GNN suggests → 4-step check → Human review → PROMOTE/REJECT

Usage:
    python tools/gnn_theory_validator.py --suggestion-id sugg_001
    python tools/gnn_theory_validator.py --batch --min-confidence 0.85
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Try to import cohere, but make it optional
try:
    import cohere
    COHERE_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"⚠️  Cohere not available: {e}")
    print(f"    Will use fallback heuristic for energy intuition checks")
    COHERE_AVAILABLE = False
    cohere = None  # Define as None for type checking

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

class IntegrationLevel(Enum):
    """Classification of GNN suggestion value"""
    TRIVIAL = "TRIVIAL"    # Already indirectly implicit
    USEFUL = "USEFUL"      # Clarifies structure
    DEEP = "DEEP"          # Novel insight/connection

class ValidationDecision(Enum):
    """Final validation decision"""
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

@dataclass
class GNNSuggestion:
    """GNN-proposed relation"""
    id: str
    source_concept_id: str
    target_concept_id: str
    source_name: str
    target_name: str
    suggested_relation: str
    confidence: float
    gnn_model: str
    created_at: datetime
    
@dataclass
class ValidationResult:
    """Result of 4-step validation"""
    suggestion_id: str
    
    # Step 1: Formal consistency
    formal_consistency: bool
    formal_issues: List[str]
    
    # Step 2: Theory proximity
    theory_proximity: float  # 0-1
    existing_path_length: Optional[int]
    shared_parents: List[str]
    
    # Step 3: Energy/entropy intuition
    energy_intuition: float  # 0-1
    explanatory_power: str
    
    # Step 4: Integration level
    integration_level: IntegrationLevel
    integration_rationale: str
    
    # Final decision
    decision: ValidationDecision
    overall_rationale: str
    validated_by: Optional[str]
    validated_at: Optional[datetime]

# ============================================================
# STEP 1: FORMAL CONSISTENCY CHECK
# ============================================================

def check_formal_consistency(
    driver,
    source_id: str,
    target_id: str,
    relation_type: str
) -> Tuple[bool, List[str]]:
    """
    Check if proposed relation violates fundamental EFC principles:
    - Energy conservation
    - ∇S direction constraints
    - Ef role definitions
    - Universe as energy/entropy field model
    """
    print("🔬 Step 1: Formal Consistency Check")
    
    issues = []
    
    with driver.session() as session:
        # Get concept metadata
        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        RETURN 
            source.name as source_name,
            source.domain as source_domain,
            source.metadata as source_meta,
            target.name as target_name,
            target.domain as target_domain,
            target.metadata as target_meta
        """
        result = session.run(query, source_id=source_id, target_id=target_id)
        record = result.single()
        
        if not record:
            issues.append("Source or target concept not found")
            return False, issues
        
        source_name = record["source_name"] or ""
        target_name = record["target_name"] or ""
        source_domain = record["source_domain"] or "general"
        target_domain = record["target_domain"] or "general"
        
        # Rule 1: Energy conservation violations
        if "energy" in source_name.lower() or "energy" in target_name.lower():
            if relation_type == "CONFLICTS_WITH":
                if "conservation" in source_name.lower() or "conservation" in target_name.lower():
                    issues.append("Violates energy conservation - cannot conflict with conservation law")
        
        # Rule 2: Entropy gradient direction
        if "entropy" in source_name.lower() and "gradient" in source_name.lower():
            if relation_type == "CONSTRAINS":
                # ∇S should constrain energy flow, not vice versa
                if "energy" in target_name.lower() and "flow" not in target_name.lower():
                    issues.append("∇S should constrain energy FLOW patterns, not energy itself")
        
        # Rule 3: Ef (Energy Flow) role
        if "energy flow" in source_name.lower() or "energy-flow" in source_name.lower():
            if relation_type == "DERIVES_FROM":
                # Ef should not derive from non-fundamental concepts
                if "halo" in target_name.lower() or "window" in target_name.lower():
                    issues.append("Energy Flow is fundamental, cannot derive from emergent structures")
        
        # Rule 4: Universe model consistency
        # If relating cosmology concepts, must maintain energy/entropy-first ontology
        if source_domain == "cosmology" and target_domain == "cosmology":
            if relation_type == "SUPPORTS":
                # Keyword heuristic for ontology check
                # (Future: add explicit metadata fields for ontology validation)
                if "dark matter" in source_name.lower() and "energy flow" not in target_name.lower():
                    issues.append("Warning: Dark matter should be reinterpreted via energy-flow, not as fundamental")
    
    is_consistent = len(issues) == 0
    
    if is_consistent:
        print(f"   ✅ Formally consistent")
    else:
        print(f"   ❌ {len(issues)} formal issues:")
        for issue in issues:
            print(f"      - {issue}")
    
    return is_consistent, issues

# ============================================================
# STEP 2: THEORY PROXIMITY CHECK
# ============================================================

def check_theory_proximity(
    driver,
    source_id: str,
    target_id: str
) -> Tuple[float, Optional[int], List[str]]:
    """
    Check how close the suggestion is to existing theory structure:
    - Shortest path length between concepts
    - Shared parent concepts/models
    - Existing implicit connections
    
    Returns:
        proximity_score: 0-1 (1 = very close, 0 = distant)
        path_length: steps between concepts (None if no path)
        shared_parents: list of shared parent concept IDs
    """
    print("🔍 Step 2: Theory Proximity Check")
    
    with driver.session() as session:
        # Find shortest path
        path_query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        MATCH path = shortestPath((source)-[*]-(target))
        RETURN length(path) as path_length
        """
        path_result = session.run(path_query, source_id=source_id, target_id=target_id)
        path_record = path_result.single()
        path_length = path_record["path_length"] if path_record else None
        
        # Find shared parent concepts
        parent_query = """
        MATCH (source:Concept {id: $source_id})-[:PART_OF|DERIVES_FROM]->(parent)
        MATCH (target:Concept {id: $target_id})-[:PART_OF|DERIVES_FROM]->(parent)
        RETURN collect(DISTINCT parent.name) as shared_parents
        """
        parent_result = session.run(parent_query, source_id=source_id, target_id=target_id)
        parent_record = parent_result.single()
        shared_parents = parent_record["shared_parents"] if parent_record else []
        
        # Calculate proximity score
        if path_length is None:
            proximity = 0.0  # No connection at all
        elif path_length == 1:
            proximity = 0.95  # Already directly connected (likely redundant)
        elif path_length == 2:
            proximity = 0.85  # One concept between them
        elif path_length == 3:
            proximity = 0.65  # Two concepts between
        else:
            proximity = max(0.3, 1.0 - (path_length * 0.15))
        
        # Boost proximity if shared parents
        if shared_parents:
            proximity = min(1.0, proximity + 0.1 * len(shared_parents))
        
        print(f"   📊 Proximity score: {proximity:.2f}")
        if path_length:
            print(f"   📏 Existing path length: {path_length}")
        else:
            print(f"   📏 No existing path (new bridge!)")
        if shared_parents:
            print(f"   👥 Shared parents: {', '.join(shared_parents)}")
        
        return proximity, path_length, shared_parents

# ============================================================
# STEP 3: ENERGY/ENTROPY INTUITION CHECK
# ============================================================

def check_energy_intuition(
    driver,
    cohere_client,
    source_id: str,
    target_id: str,
    relation_type: str
) -> Tuple[float, str]:
    """
    Use LLM + EFC principles to assess if relation enhances explanatory power:
    - Does it clarify energy flow patterns?
    - Does it reduce theoretical entropy?
    - Does it bridge levels (cosmo ↔ bio ↔ cognition ↔ AI)?
    
    Returns:
        intuition_score: 0-1 (1 = strong enhancement, 0 = no value)
        explanation: textual rationale
    """
    print("💡 Step 3: Energy/Entropy Intuition Check")
    
    with driver.session() as session:
        # Get concept details
        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        OPTIONAL MATCH (source)-[r]-(connected)
        WITH source, target, collect(DISTINCT type(r)) as source_rels
        OPTIONAL MATCH (target)-[r2]-(connected2)
        RETURN 
            source.name as source_name,
            source.description as source_desc,
            source.domain as source_domain,
            target.name as target_name,
            target.description as target_desc,
            target.domain as target_domain,
            source_rels,
            collect(DISTINCT type(r2)) as target_rels
        """
        result = session.run(query, source_id=source_id, target_id=target_id)
        record = result.single()
        
        # Check if Cohere is available - if not, use fallback immediately
        if not COHERE_AVAILABLE:
            print(f"   ⚠️  Cohere unavailable - using domain-based heuristic")
            
            # Fallback: heuristic scoring based on domain match
            score = 0.5
            if record['source_domain'] == record['target_domain']:
                score = 0.6  # Same domain slightly better
            
            rationale = f"Cohere unavailable - domain-based heuristic (domains: {record['source_domain']}, {record['target_domain']})"
            return score, rationale
        
        # Build prompt for LLM
        prompt = f"""You are an expert in Energy-Flow Cosmology (EFC), a theoretical framework where:
- The universe is modeled as energy/entropy fields (NOT matter/spacetime-first)
- Energy Flow (Ef) and Entropy Gradient (∇S) are fundamental
- I₀ = γ |Ef · ∇S| governs information/insight emergence
- Conservation of energy is sacred
- Structures emerge from energy-flow stability windows

A Graph Neural Network has suggested a new relation:

**Source Concept:** {record['source_name']}
Domain: {record['source_domain']}
Description: {record.get('source_desc', 'N/A')}
Existing relations: {', '.join(record['source_rels']) if record['source_rels'] else 'None'}

**Target Concept:** {record['target_name']}
Domain: {record['target_domain']}
Description: {record.get('target_desc', 'N/A')}
Existing relations: {', '.join(record['target_rels']) if record['target_rels'] else 'None'}

**Suggested Relation Type:** {relation_type}

Evaluate this suggestion on:
1. Does it clarify energy flow patterns?
2. Does it reduce theoretical entropy (less ad hoc assumptions)?
3. Does it bridge levels (cosmology ↔ biology ↔ cognition ↔ AI)?
4. Does it enhance explanatory power for:
   - Halo structures
   - Rotation curves
   - CMB interpretation
   - Structure formation

Respond in JSON format:
{{
    "score": 0.0-1.0,
    "rationale": "Brief explanation (2-3 sentences)",
    "enhances_energy_flow": true/false,
    "reduces_entropy": true/false,
    "bridges_levels": true/false
}}
"""
        
        # Call LLM with error handling
        import json
        try:
            response = cohere_client.chat(
                model="command-r-plus-08-2024",
                message=prompt,
                temperature=0.3
            )
            
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(result_text)
            score = float(evaluation.get("score", 0.5))
            rationale = evaluation.get("rationale", "No rationale provided")
            
            # Clamp score to valid range
            score = max(0.0, min(1.0, score))
            
            print(f"   💡 Intuition score: {score:.2f}")
            print(f"   📝 {rationale}")
            
            return score, rationale
            
        except Exception as e:
            print(f"   ⚠️  LLM evaluation failed: {e}")
            print(f"   Using fallback heuristic based on concept domains...")
            
            # Fallback: heuristic scoring based on domain match
            score = 0.5
            if record['source_domain'] == record['target_domain']:
                score = 0.6  # Same domain slightly better
            
            rationale = f"LLM evaluation unavailable ({type(e).__name__}) - using domain-based heuristic"
            return score, rationale

# ============================================================
# STEP 4: INTEGRATION LEVEL CLASSIFICATION
# ============================================================

def classify_integration_level(
    formal_consistent: bool,
    proximity: float,
    intuition: float,
    path_length: Optional[int]
) -> Tuple[IntegrationLevel, str]:
    """
    Classify suggestion as TRIVIAL | USEFUL | DEEP
    """
    print("🎯 Step 4: Integration Level Classification")
    
    # TRIVIAL: Already very close, redundant
    if path_length == 1:
        return IntegrationLevel.TRIVIAL, "Already directly connected - redundant"
    
    if proximity > 0.9 and path_length == 2:
        return IntegrationLevel.TRIVIAL, "Already implicitly connected via one intermediate"
    
    # DEEP: Novel bridge with high intuition
    if path_length is None or path_length > 4:
        if intuition > 0.75 and formal_consistent:
            return IntegrationLevel.DEEP, "Novel bridge between distant concepts with high explanatory power"
    
    # USEFUL: Clarifies structure
    if formal_consistent and intuition > 0.6:
        if proximity < 0.8:
            return IntegrationLevel.USEFUL, "Clarifies non-obvious structural connection"
    
    # Default: TRIVIAL if not clearly useful/deep
    if intuition < 0.5:
        return IntegrationLevel.TRIVIAL, "Low explanatory value - likely noise"
    
    return IntegrationLevel.USEFUL, "Moderate structural clarification"

# ============================================================
# MAIN VALIDATION FUNCTION
# ============================================================

def validate_suggestion(
    driver,
    cohere_client,
    suggestion_id: str
) -> ValidationResult:
    """
    Run complete 4-step validation on a GNN suggestion
    """
    print(f"\n🔬 Validating GNN Suggestion: {suggestion_id}")
    print("=" * 60)
    
    # Load suggestion from Neo4j
    with driver.session() as session:
        query = """
        MATCH (s:GNNSuggestion {id: $suggestion_id})
        RETURN s
        """
        result = session.run(query, suggestion_id=suggestion_id)
        record = result.single()
        
        if not record:
            raise ValueError(f"Suggestion {suggestion_id} not found")
        
        s = record["s"]
        
        # Handle Neo4j datetime - convert to Python datetime if needed
        created_at = s["created_at"]
        if hasattr(created_at, 'to_native'):
            # Neo4j DateTime object
            created_at = created_at.to_native()
        elif isinstance(created_at, str):
            # Parse string datetime
            from dateutil import parser
            created_at = parser.parse(created_at)
        
        suggestion = GNNSuggestion(
            id=s["id"],
            source_concept_id=s["source_concept_id"],
            target_concept_id=s["target_concept_id"],
            source_name=s.get("source_name", "Unknown"),
            target_name=s.get("target_name", "Unknown"),
            suggested_relation=s["suggested_relation"],
            confidence=float(s["confidence"]),
            gnn_model=s["gnn_model"],
            created_at=created_at
        )
    
    print(f"📋 {suggestion.source_name} -[{suggestion.suggested_relation}]-> {suggestion.target_name}")
    print(f"🎲 Confidence: {suggestion.confidence:.2f}\n")
    
    # Step 1: Formal consistency
    formal_ok, formal_issues = check_formal_consistency(
        driver,
        suggestion.source_concept_id,
        suggestion.target_concept_id,
        suggestion.suggested_relation
    )
    
    # Step 2: Theory proximity
    proximity, path_length, shared_parents = check_theory_proximity(
        driver,
        suggestion.source_concept_id,
        suggestion.target_concept_id
    )
    
    # Step 3: Energy intuition
    intuition, explanation = check_energy_intuition(
        driver,
        cohere_client,
        suggestion.source_concept_id,
        suggestion.target_concept_id,
        suggestion.suggested_relation
    )
    
    # Step 4: Integration level
    integration, integration_rationale = classify_integration_level(
        formal_ok, proximity, intuition, path_length
    )
    
    print(f"\n   🏷️  Integration Level: {integration.value}")
    print(f"   📝 {integration_rationale}")
    
    # Final decision
    if not formal_ok:
        decision = ValidationDecision.REJECTED
        rationale = f"Formal consistency violation: {'; '.join(formal_issues)}"
    elif integration == IntegrationLevel.TRIVIAL:
        decision = ValidationDecision.REJECTED
        rationale = "Trivial - no significant value added"
    elif integration == IntegrationLevel.DEEP and intuition > 0.75:
        decision = ValidationDecision.PROMOTED
        rationale = f"Deep insight with high explanatory power ({intuition:.2f})"
    elif integration == IntegrationLevel.USEFUL and intuition > 0.6:
        decision = ValidationDecision.PENDING
        rationale = "Useful clarification - requires human review"
    else:
        decision = ValidationDecision.REJECTED
        rationale = "Insufficient value or confidence"
    
    print(f"\n🎯 Decision: {decision.value}")
    print(f"📝 Rationale: {rationale}")
    
    # Create validation result
    result = ValidationResult(
        suggestion_id=suggestion_id,
        formal_consistency=formal_ok,
        formal_issues=formal_issues,
        theory_proximity=proximity,
        existing_path_length=path_length,
        shared_parents=shared_parents,
        energy_intuition=intuition,
        explanatory_power=explanation,
        integration_level=integration,
        integration_rationale=integration_rationale,
        decision=decision,
        overall_rationale=rationale,
        validated_by=None,  # Set by human
        validated_at=None   # Set by human
    )
    
    # Save to Neo4j
    save_validation_result(driver, result)
    
    return result

def save_validation_result(driver, result: ValidationResult):
    """Save validation result to Neo4j"""
    with driver.session() as session:
        query = """
        MERGE (v:ValidationResult {id: $result_id})
        SET v.suggestion_id = $suggestion_id,
            v.formal_consistency = $formal_consistency,
            v.formal_issues = $formal_issues,
            v.theory_proximity = $theory_proximity,
            v.existing_path_length = $existing_path_length,
            v.shared_parents = $shared_parents,
            v.energy_intuition = $energy_intuition,
            v.explanatory_power = $explanatory_power,
            v.integration_level = $integration_level,
            v.integration_rationale = $integration_rationale,
            v.decision = $decision,
            v.overall_rationale = $overall_rationale,
            v.validated_at = datetime()
        
        WITH v
        MATCH (s:GNNSuggestion {id: $suggestion_id})
        MERGE (s)-[:HAS_VALIDATION]->(v)
        SET s.status = $decision
        
        RETURN v
        """
        
        session.run(
            query,
            result_id=f"val_{result.suggestion_id}",
            suggestion_id=result.suggestion_id,
            formal_consistency=result.formal_consistency,
            formal_issues=result.formal_issues,
            theory_proximity=result.theory_proximity,
            existing_path_length=result.existing_path_length,
            shared_parents=result.shared_parents,
            energy_intuition=result.energy_intuition,
            explanatory_power=result.explanatory_power,
            integration_level=result.integration_level.value,
            integration_rationale=result.integration_rationale,
            decision=result.decision.value,
            overall_rationale=result.overall_rationale
        )

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate GNN suggestions against EFC theory")
    parser.add_argument("--suggestion-id", help="Validate single suggestion")
    parser.add_argument("--batch", action="store_true", help="Validate all pending suggestions")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence threshold")
    
    args = parser.parse_args()
    
    # Connect
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    cohere_client = cohere.Client(COHERE_API_KEY) if COHERE_AVAILABLE else None
    
    try:
        if args.suggestion_id:
            # Single validation
            validate_suggestion(driver, cohere_client, args.suggestion_id)
        
        elif args.batch:
            # Batch validation
            print("🔄 Batch validation of pending suggestions...")
            
            with driver.session() as session:
                query = """
                MATCH (s:GNNSuggestion)
                WHERE s.status = "PENDING" AND s.confidence >= $min_conf
                RETURN s.id as id
                ORDER BY s.confidence DESC
                """
                results = session.run(query, min_conf=args.min_confidence)
                
                suggestion_ids = [r["id"] for r in results]
                
                print(f"Found {len(suggestion_ids)} pending suggestions\n")
                
                for i, sugg_id in enumerate(suggestion_ids, 1):
                    print(f"\n{'='*60}")
                    print(f"Processing {i}/{len(suggestion_ids)}")
                    validate_suggestion(driver, cohere_client, sugg_id)
        
        else:
            parser.print_help()
    
    finally:
        driver.close()
