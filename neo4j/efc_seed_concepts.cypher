// ===============================================
// CORE EFC CONCEPTS
// Kjør etter schema
// ===============================================

WITH datetime() AS now

// ---- EFC Core ----
MERGE (c:EFC:Concept {slug: 'efc-core'})
ON CREATE SET
  c.id = 'concept:efc-core',
  c.name = 'Energy-Flow Cosmology (EFC)',
  c.category = 'core',
  c.level = 0,
  c.status = 'active',
  c.summary = 'Thermodynamic framework where cosmic structure, dynamics and cognition emerge from continuous energy–entropy flow between S₀ and S₁.',
  c.created_at = now,
  c.updated_at = now;

// ---- Grid–Higgs Framework ----
MERGE (c:Concept {slug: 'grid-higgs-framework'})
ON CREATE SET
  c.id = 'concept:grid-higgs-framework',
  c.name = 'Grid–Higgs Framework',
  c.category = 'structure',
  c.level = 1,
  c.status = 'active',
  c.summary = 'Discrete–continuous energy grid coupled to an effective Higgs-like field defining local inertia and emergent geometry.',
  c.created_at = now,
  c.updated_at = now;

// ---- Halo Model of Entropy ----
MERGE (c:Concept {slug: 'halo-model-of-entropy'})
ON CREATE SET
  c.id = 'concept:halo-model-of-entropy',
  c.name = 'Halo Model of Entropy',
  c.category = 'structure',
  c.level = 1,
  c.status = 'active',
  c.summary = 'Entropy halos around baryonic structures replacing dark matter with thermodynamic energy–entropy configurations.',
  c.created_at = now,
  c.updated_at = now;

// ---- s₀/s₁ speed gradient ----
MERGE (c:Concept {slug: 's0-s1-speed-gradient'})
ON CREATE SET
  c.id = 'concept:s0-s1-speed-gradient',
  c.name = 'S₀/S₁ Speed Gradient',
  c.category = 'dynamics',
  c.level = 1,
  c.status = 'active',
  c.summary = 'Variation in effective propagation speed near S₀ (low entropy) and S₁ (high entropy) boundaries due to changing energy-flow conditions.',
  c.created_at = now,
  c.updated_at = now;

// ---- Entropy–Light-Speed Relationship ----
MERGE (c:Concept {slug: 'entropy-light-speed-relationship'})
ON CREATE SET
  c.id = 'concept:entropy-light-speed-relationship',
  c.name = 'Entropy–Light-Speed Relationship',
  c.category = 'dynamics',
  c.level = 1,
  c.status = 'active',
  c.summary = 'Functional link between local entropy state / gradient and effective light propagation characteristics in EFC.',
  c.created_at = now,
  c.updated_at = now;

// ---- Energy-Flow Dynamics (EFD) ----
MERGE (c:Concept {slug: 'energy-flow-dynamics-efd'})
ON CREATE SET
  c.id = 'concept:energy-flow-dynamics-efd',
  c.name = 'Energy-Flow Dynamics (EFD)',
  c.category = 'dynamics',
  c.level = 1,
  c.status = 'active',
  c.summary = 'Dynamical description of how energy-flow potentials and entropy gradients drive structure formation and motion.',
  c.created_at = now,
  c.updated_at = now;

// ---- CEM-Cosmos ----
MERGE (c:Concept {slug: 'cem-cosmos'})
ON CREATE SET
  c.id = 'concept:cem-cosmos',
  c.name = 'CEM-Cosmos',
  c.category = 'cognition',
  c.level = 2,
  c.status = 'active',
  c.summary = 'Cosmic-scale coupling between cognition, energy and matter in the EFC framework.',
  c.created_at = now,
  c.updated_at = now;

// ---- Informational Metastructure (IMX) ----
MERGE (c:Concept {slug: 'informational-metastructure-imx'})
ON CREATE SET
  c.id = 'concept:informational-metastructure-imx',
  c.name = 'Informational Metastructure (IMX)',
  c.category = 'cognition',
  c.level = 2,
  c.status = 'active',
  c.summary = 'Meta-layer describing how information, codes and semantic structures emerge from and constrain energy-flow configurations.',
  c.created_at = now,
  c.updated_at = now;

// ---- Cross-Domain Vector Convergence (CDVC) ----
MERGE (c:Concept {slug: 'cross-domain-vector-convergence-cdvc'})
ON CREATE SET
  c.id = 'concept:cross-domain-vector-convergence-cdvc',
  c.name = 'Cross-Domain Vector Convergence (CDVC)',
  c.category = 'cognition',
  c.level = 2,
  c.status = 'active',
  c.summary = 'Alignment of structural, dynamical and cognitive vectors across domains in the EFC ecosystem.',
  c.created_at = now,
  c.updated_at = now;

// ---- Symbiotic Reflective Methodology (SRM) ----
MERGE (c:Concept {slug: 'symbiotic-reflective-methodology-srm'})
ON CREATE SET
  c.id = 'concept:symbiotic-reflective-methodology-srm',
  c.name = 'Symbiotic Reflective Methodology (SRM)',
  c.category = 'methodology',
  c.level = 2,
  c.status = 'active',
  c.summary = 'AI-augmented scientific workflow where human–AI symbiosis co-evolves with the EFC framework.',
  c.created_at = now,
  c.updated_at = now;

// ===============================================
// HIERARKISKE RELASJONER
// ===============================================

MATCH (efc:Concept {slug:'efc-core'})
MATCH (gh:Concept {slug:'grid-higgs-framework'})
MERGE (gh)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (halo:Concept {slug:'halo-model-of-entropy'})
MERGE (halo)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (spd:Concept {slug:'s0-s1-speed-gradient'})
MERGE (spd)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (efd:Concept {slug:'energy-flow-dynamics-efd'})
MERGE (efd)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (cem:Concept {slug:'cem-cosmos'})
MERGE (cem)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (imx:Concept {slug:'informational-metastructure-imx'})
MERGE (imx)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (cdvc:Concept {slug:'cross-domain-vector-convergence-cdvc'})
MERGE (cdvc)-[:PART_OF]->(efc);

MATCH (efc:Concept {slug:'efc-core'})
MATCH (srm:Concept {slug:'symbiotic-reflective-methodology-srm'})
MERGE (srm)-[:PART_OF]->(efc);

// DEPENDENCY-LAG (eksempler)
MATCH (halo:Concept {slug:'halo-model-of-entropy'})
MATCH (gh:Concept   {slug:'grid-higgs-framework'})
MERGE (halo)-[:DEPENDS_ON]->(gh);

MATCH (spd:Concept {slug:'s0-s1-speed-gradient'})
MATCH (efd:Concept {slug:'energy-flow-dynamics-efd'})
MERGE (spd)-[:DEPENDS_ON]->(efd);

MATCH (cem:Concept {slug:'cem-cosmos'})
MATCH (imx:Concept {slug:'informational-metastructure-imx'})
MERGE (cem)-[:DEPENDS_ON]->(imx);
