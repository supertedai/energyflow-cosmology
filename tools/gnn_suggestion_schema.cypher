// ============================================================
// GNN SUGGESTION SCHEMA - Neo4j Constraints & Indexes
// ============================================================
// 
// This schema supports the GNN → Theory validation workflow:
// 
// 1. GNN proposes: (:Concept)-[:SUGGESTS_RELATION]->(:Concept)
// 2. Theory validation: 4-step check (formell, nærhet, energi, integrasjon)
// 3. Human approval: SUGGESTS_RELATION → PROMOTED or REJECTED
// 4. History tracking: who, when, why
//
// Usage:
//     cat tools/gnn_suggestion_schema.cypher | cypher-shell -u neo4j -p <password>
// ============================================================

// ------------------------------------------------------------
// 1. CORE NODE CONSTRAINTS
// ------------------------------------------------------------

// Concept nodes (EFC concepts)
CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT concept_name IF NOT EXISTS
FOR (c:Concept) REQUIRE c.name IS NOT NULL;

// Equation nodes
CREATE CONSTRAINT equation_id IF NOT EXISTS
FOR (e:Equation) REQUIRE e.id IS UNIQUE;

// Model/Framework nodes
CREATE CONSTRAINT model_id IF NOT EXISTS
FOR (m:Model) REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT framework_id IF NOT EXISTS
FOR (f:Framework) REQUIRE f.id IS UNIQUE;

// ------------------------------------------------------------
// 2. GNN SUGGESTION NODES
// ------------------------------------------------------------

// GNN-proposed relation (before validation)
CREATE CONSTRAINT gnn_suggestion_id IF NOT EXISTS
FOR (s:GNNSuggestion) REQUIRE s.id IS UNIQUE;

// Validation result node
CREATE CONSTRAINT validation_result_id IF NOT EXISTS
FOR (v:ValidationResult) REQUIRE v.id IS UNIQUE;

// ------------------------------------------------------------
// 3. INDEXES FOR EFFICIENT QUERIES
// ------------------------------------------------------------

// Search concepts by domain
CREATE INDEX concept_domain IF NOT EXISTS
FOR (c:Concept) ON (c.domain);

// Search concepts by layer
CREATE INDEX concept_layer IF NOT EXISTS
FOR (c:Concept) ON (c.layer);

// Find EFC core concepts
CREATE INDEX concept_efc_core IF NOT EXISTS
FOR (c:Concept) ON (c.efc_core);

// Find suggestions by status
CREATE INDEX suggestion_status IF NOT EXISTS
FOR (s:GNNSuggestion) ON (s.status);

// Find suggestions by confidence
CREATE INDEX suggestion_confidence IF NOT EXISTS
FOR (s:GNNSuggestion) ON (s.confidence);

// Timestamp index for history tracking
CREATE INDEX suggestion_timestamp IF NOT EXISTS
FOR (s:GNNSuggestion) ON (s.created_at);

// Validation result timestamp
CREATE INDEX validation_timestamp IF NOT EXISTS
FOR (v:ValidationResult) ON (v.validated_at);

// ------------------------------------------------------------
// 4. EXAMPLE DATA MODEL
// ------------------------------------------------------------

// Example: GNN suggests new relation
//
// (:Concept {name: "Entropy Gradient"})-[:SUGGESTS_RELATION {
//     confidence: 0.91,
//     edge_type: "SUPPORTS",
//     gnn_model: "efc_gnn_v1",
//     created_at: datetime()
// }]->(:Concept {name: "Adaptive Energy-Flow Window"})
//
// After validation:
//
// (:GNNSuggestion {
//     id: "sugg_001",
//     source_concept_id: "entropy_gradient",
//     target_concept_id: "adaptive_window",
//     suggested_relation: "SUPPORTS",
//     confidence: 0.91,
//     status: "PROMOTED",  // or "REJECTED" or "PENDING"
//     gnn_model: "efc_gnn_v1",
//     created_at: datetime(),
//     validated_at: datetime(),
//     validated_by: "morpheus",
//     rationale: "Consistent with ∇S → Ef stability window theorem"
// })
//
// (:ValidationResult {
//     id: "val_001",
//     suggestion_id: "sugg_001",
//     formal_consistency: true,
//     theory_proximity: 0.85,
//     energy_intuition: 0.92,
//     integration_level: "DEEP",  // TRIVIAL | USEFUL | DEEP
//     conflicts: [],
//     supporting_concepts: ["energy_conservation", "entropy_flow"],
//     decision: "PROMOTED",
//     rationale: "..."
// })

// ------------------------------------------------------------
// 5. SUGGESTED CYPHER QUERIES
// ------------------------------------------------------------

// Find all pending GNN suggestions:
// MATCH (s:GNNSuggestion {status: "PENDING"})
// RETURN s
// ORDER BY s.confidence DESC

// Find high-confidence suggestions:
// MATCH (s:GNNSuggestion)
// WHERE s.confidence > 0.85 AND s.status = "PENDING"
// RETURN s

// Promote a suggestion:
// MATCH (s:GNNSuggestion {id: "sugg_001"})
// MATCH (source:Concept {id: s.source_concept_id})
// MATCH (target:Concept {id: s.target_concept_id})
// CREATE (source)-[r:SUPPORTS {
//     weight: s.confidence,
//     source: "gnn_suggestion",
//     promoted_at: datetime(),
//     promoted_by: "morpheus"
// }]->(target)
// SET s.status = "PROMOTED"
// RETURN r

// Reject a suggestion:
// MATCH (s:GNNSuggestion {id: "sugg_001"})
// SET s.status = "REJECTED",
//     s.rejected_at = datetime(),
//     s.rejected_by = "morpheus",
//     s.rejection_reason = "Conflicts with energy conservation"
// RETURN s

// Find all promoted suggestions:
// MATCH (s:GNNSuggestion {status: "PROMOTED"})
// RETURN s.id, s.source_concept_id, s.target_concept_id, s.suggested_relation, s.rationale

// History: Who validated what when:
// MATCH (s:GNNSuggestion)
// WHERE s.status IN ["PROMOTED", "REJECTED"]
// RETURN s.validated_by, s.status, count(*) as total
// ORDER BY total DESC
