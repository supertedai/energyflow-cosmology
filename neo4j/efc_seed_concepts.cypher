// ===============================================
// CORE EFC CONCEPTS (FIXED VERSION)
// WITH now applies to entire block
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
  c.updated_at = now

// ---- Grid–Higgs Framework ----
MERGE (c2:Concept {slug: 'grid-higgs-framework'})
ON CREATE SET
  c2.id = 'concept:grid-higgs-framework',
  c2.name = 'Grid–Higgs Framework',
  c2.category = 'structure',
  c2.level = 1,
  c2.status = 'active',
  c2.summary = 'Discrete–continuous energy grid coupled to an effective Higgs-like field defining local inertia and emergent geometry.',
  c2.created_at = now,
  c2.updated_at = now

// ---- Halo Model of Entropy ----
MERGE (c3:Concept {slug: 'halo-model-of-entropy'})
ON CREATE SET
  c3.id = 'concept:halo-model-of-entropy',
  c3.name = 'Halo Model of Entropy',
  c3.category = 'structure',
  c3.level = 1,
  c3.status = 'active',
  c3.summary = 'Entropy halos around baryonic structures replacing dark matter with thermodynamic energy–entropy configurations.',
  c3.created_at = now,
  c3.updated_at = now

// ---- s₀/s₁ speed gradient ----
MERGE (c4:Concept {slug: 's0-s1-speed-gradient'})
ON CREATE SET
  c4.id = 'concept:s0-s1-speed-gradient',
  c4.name = 'S₀/S₁ Speed Gradient',
  c4.category = 'dynamics',
  c4.level = 1,
  c4.status = 'active',
  c4.summary = 'Variation in effective propagation speed near S₀ (low entropy) and S₁ (high entropy) boundaries due to changing energy-flow conditions.',
  c4.created_at = now,
  c4.updated_at = now

// ---- Entropy–Light-Speed Relationship ----
MERGE (c5:Concept {slug: 'entropy-light-speed-relationship'})
ON CREATE SET
  c5.id = 'concept:entropy-light-speed-relationship',
  c5.name = 'Entropy–Light-Speed Relationship',
  c5.category = 'dynamics',
  c5.level = 1,
  c5.status = 'active',
  c5.summary = 'Functional link between local entropy state / gradient and effective light propagation characteristics in EFC.',
  c5.created_at = now,
  c5.updated_at = now

// ---- Energy-Flow Dynamics (EFD) ----
MERGE (c6:Concept {slug: 'energy-flow-dynamics-efd'})
ON CREATE SET
  c6.id = 'concept:energy-flow-dynamics-efd',
  c6.name = 'Energy-Flow Dynamics (EFD)',
  c6.category = 'dynamics',
  c6.level = 1,
  c6.status = 'active',
  c6.summary = 'Dynamical description of how energy-flow potentials and entropy gradients drive structure formation and motion.',
  c6.created_at = now,
  c6.updated_at = now

// ---- CEM-Cosmos ----
MERGE (c7:Concept {slug: 'cem-cosmos'})
ON CREATE SET
  c7.id = 'concept:cem-cosmos',
  c7.name = 'CEM-Cosmos',
  c7.category = 'cognition',
  c7.level = 2,
  c7.status = 'active',
  c7.summary = 'Cosmic-scale coupling between cognition, energy and matter in the EFC framework.',
  c7.created_at = now,
  c7.updated_at = now

// ---- Informational Metastructure (IMX) ----
MERGE (c8:Concept {slug: 'informational-metastructure-imx'})
ON CREATE SET
  c8.id = 'concept:informational-metastructure-imx',
  c8.name = 'Informational Metastructure (IMX)',
  c8.category = 'cognition',
  c8.level = 2,
  c8.status = 'active',
  c8.summary = 'Meta-layer describing how information, codes and semantic structures emerge from and constrain energy-flow configurations.',
  c8.created_at = now,
  c8.updated_at = now

// ---- Cross-Domain Vector Convergence ----
MERGE (c9:Concept {slug: 'cross-domain-vector-convergence-cdvc'})
ON CREATE SET
  c9.id = 'concept:cross-domain-vector-convergence-cdvc',
  c9.name = 'Cross-Domain Vector Convergence (CDVC)',
  c9.category = 'cognition',
  c9.level = 2,
  c9.status = 'active',
  c9.summary = 'Alignment of structural, dynamical and cognitive vectors across domains in the EFC ecosystem.',
  c9.created_at = now,
  c9.updated_at = now

// ---- Symbiotic Reflective Methodology ----
MERGE (c10:Concept {slug: 'symbiotic-reflective-methodology-srm'})
ON CREATE SET
  c10.id = 'concept:symbiotic-reflective-methodology-srm',
  c10.name = 'Symbiotic Reflective Methodology (SRM)',
  c10.category = 'methodology',
  c10.level = 2,
  c10.status = 'active',
  c10.summary = 'AI-augmented scientific workflow where human–AI symbiosis co-evolves with the EFC framework.',
  c10.created_at = now,
  c10.updated_at = now;

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

// Dependencies
MATCH (halo:Concept {slug:'halo-model-of-entropy'})
MATCH (gh:Concept   {slug:'grid-higgs-framework'})
MERGE (halo)-[:DEPENDS_ON]->(gh);

MATCH (spd:Concept {slug:'s0-s1-speed-gradient'})
MATCH (efd:Concept {slug:'energy-flow-dynamics-efd'})
MERGE (spd)-[:DEPENDS_ON]->(efd);

MATCH (cem:Concept {slug:'cem-cosmos'})
MATCH (imx:Concept {slug:'informational-metastructure-imx'})
MERGE (cem)-[:DEPENDS_ON]->(imx);
