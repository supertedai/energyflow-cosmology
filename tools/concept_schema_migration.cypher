// ============================================================
// CONCEPT SCHEMA MIGRATION - Ensure GNN Validator Compatibility
// ============================================================
//
// This migration ensures all :Concept nodes have the fields
// required by gnn_theory_validator.py:
//
// Required fields:
//   - id: Unique identifier (UUID if not set)
//   - name: Concept name (REQUIRED)
//   - domain: Category (cosmology|thermodynamics|meta|cognition|ai|general)
//   - layer: Theory level (formal|applied|meta|cognitive|computational)
//   - description: Text description (for LLM context)
//   - stability_score: How established (0-1, default 0.5)
//   - mention_count_efc: Count in EFC documents (default 0)
//   - mention_count_private: Count in private work (default 0)
//   - efc_core: Is this core to EFC? (boolean, default false)
//   - metadata: Additional properties (map, default {})
//
// Usage:
//     cat tools/concept_schema_migration.cypher | cypher-shell -u neo4j -p <password>
//
// ============================================================

// ------------------------------------------------------------
// 1. ENSURE ALL CONCEPTS HAVE REQUIRED FIELDS
// ------------------------------------------------------------

// Add missing 'id' fields (use randomUUID - no APOC needed)
MATCH (c:Concept)
WHERE c.id IS NULL
SET c.id = randomUUID()
RETURN count(c) as concepts_with_new_ids;

// Add missing 'domain' fields
MATCH (c:Concept)
WHERE c.domain IS NULL
SET c.domain = CASE
    WHEN c.type IN ['cosmology', 'astrophysics', 'universe'] THEN 'cosmology'
    WHEN c.type IN ['thermodynamics', 'entropy', 'energy'] THEN 'thermodynamics'
    WHEN c.type IN ['meta', 'methodology', 'framework'] THEN 'meta'
    WHEN c.type IN ['cognition', 'consciousness', 'mind'] THEN 'cognition'
    WHEN c.type IN ['ai', 'machine_learning', 'artificial_intelligence'] THEN 'ai'
    WHEN c.type IN ['information', 'information_theory'] THEN 'information'
    ELSE 'general'
END
RETURN count(c) as concepts_with_new_domains;

// Add missing 'layer' fields
MATCH (c:Concept)
WHERE c.layer IS NULL
SET c.layer = CASE
    WHEN c.type = 'formal' OR c.name CONTAINS 'Equation' OR c.name CONTAINS 'Law' THEN 'formal'
    WHEN c.type = 'applied' OR c.name CONTAINS 'Model' OR c.name CONTAINS 'Framework' THEN 'applied'
    WHEN c.type = 'meta' OR c.name CONTAINS 'Meta' OR c.name CONTAINS 'Methodology' THEN 'meta'
    WHEN c.type = 'cognitive' OR c.name CONTAINS 'Cognition' OR c.name CONTAINS 'Mind' THEN 'cognitive'
    WHEN c.type = 'computational' OR c.name CONTAINS 'Algorithm' OR c.name CONTAINS 'AI' THEN 'computational'
    ELSE 'formal'
END
RETURN count(c) as concepts_with_new_layers;

// Add missing 'description' fields (use type or generate from name)
MATCH (c:Concept)
WHERE c.description IS NULL
SET c.description = COALESCE(
    c.definition,
    c.type,
    'Concept in Energy-Flow Cosmology: ' + c.name
)
RETURN count(c) as concepts_with_new_descriptions;

// Add missing 'stability_score' fields
MATCH (c:Concept)
WHERE c.stability_score IS NULL
SET c.stability_score = CASE
    WHEN c.efc_core = true THEN 0.9
    WHEN c.mention_count_efc > 10 THEN 0.8
    WHEN c.mention_count_efc > 5 THEN 0.6
    ELSE 0.5
END
RETURN count(c) as concepts_with_new_stability;

// Add missing 'mention_count_efc' fields
MATCH (c:Concept)
WHERE c.mention_count_efc IS NULL
SET c.mention_count_efc = 0
RETURN count(c) as concepts_with_zero_efc_mentions;

// Add missing 'mention_count_private' fields
MATCH (c:Concept)
WHERE c.mention_count_private IS NULL
SET c.mention_count_private = 0
RETURN count(c) as concepts_with_zero_private_mentions;

// Add missing 'efc_core' fields
MATCH (c:Concept)
WHERE c.efc_core IS NULL
SET c.efc_core = CASE
    WHEN c.name IN [
        'Energy-Flow Cosmology',
        'Energy Flow',
        'Entropy Gradient',
        'Information Emergence',
        'Halo Model of Entropy',
        'Grid-Higgs Framework',
        'Energy Conservation'
    ] THEN true
    ELSE false
END
RETURN count(c) as concepts_with_efc_core_flag;

// Add missing 'metadata' fields
MATCH (c:Concept)
WHERE c.metadata IS NULL
SET c.metadata = {}
RETURN count(c) as concepts_with_empty_metadata;

// ------------------------------------------------------------
// 2. MIGRATE OLD 'type' FIELD TO 'domain' IF NOT DONE
// ------------------------------------------------------------

// If you have concepts with 'type' but not 'domain', copy over
MATCH (c:Concept)
WHERE c.domain IS NULL AND c.type IS NOT NULL
SET c.domain = c.type
RETURN count(c) as concepts_migrated_from_type;

// ------------------------------------------------------------
// 3. VALIDATE SCHEMA
// ------------------------------------------------------------

// Count concepts missing required fields
MATCH (c:Concept)
WHERE c.id IS NULL 
   OR c.name IS NULL 
   OR c.domain IS NULL 
   OR c.layer IS NULL
RETURN count(c) as invalid_concepts;

// Should return 0 if migration successful

// ------------------------------------------------------------
// 4. CREATE INDEXES FOR PERFORMANCE
// ------------------------------------------------------------

// Already in gnn_suggestion_schema.cypher, but repeated here for completeness

CREATE INDEX concept_domain_idx IF NOT EXISTS
FOR (c:Concept) ON (c.domain);

CREATE INDEX concept_layer_idx IF NOT EXISTS
FOR (c:Concept) ON (c.layer);

CREATE INDEX concept_efc_core_idx IF NOT EXISTS
FOR (c:Concept) ON (c.efc_core);

CREATE INDEX concept_stability_idx IF NOT EXISTS
FOR (c:Concept) ON (c.stability_score);

// ------------------------------------------------------------
// 5. EXAMPLE: MANUALLY TAG CORE EFC CONCEPTS
// ------------------------------------------------------------

// Tag known core concepts (adjust names as needed)
MATCH (c:Concept)
WHERE c.name IN [
    'Energy-Flow Cosmology',
    'Energy Flow',
    'Entropy Gradient',
    'Information Emergence',
    'Halo Model of Entropy',
    'Grid-Higgs Framework',
    'Entropy-Clarity Model',
    'Energy Conservation',
    'Symbiotic Runtime Architecture'
]
SET c.efc_core = true,
    c.stability_score = 0.95,
    c.layer = 'formal'
RETURN c.name, c.efc_core;

// ------------------------------------------------------------
// 6. SUMMARY QUERY
// ------------------------------------------------------------

// Show concept statistics after migration
MATCH (c:Concept)
RETURN 
    count(c) as total_concepts,
    count(DISTINCT c.domain) as unique_domains,
    count(DISTINCT c.layer) as unique_layers,
    sum(CASE WHEN c.efc_core = true THEN 1 ELSE 0 END) as core_concepts,
    avg(c.stability_score) as avg_stability,
    sum(c.mention_count_efc) as total_efc_mentions;

// ------------------------------------------------------------
// 7. SAMPLE CONCEPTS AFTER MIGRATION
// ------------------------------------------------------------

MATCH (c:Concept)
RETURN 
    c.id,
    c.name,
    c.domain,
    c.layer,
    c.efc_core,
    c.stability_score,
    c.mention_count_efc
ORDER BY c.stability_score DESC, c.mention_count_efc DESC
LIMIT 10;
