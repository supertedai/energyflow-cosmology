// ===============================================
// META-COGNITIVE LAYER — HOW REASONING WORKS
// ===============================================

// -----------------------------------------------
// Constraints
// -----------------------------------------------

CREATE CONSTRAINT IF NOT EXISTS
FOR (m:MetaCognition)
REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (a:CognitiveAxis)
REQUIRE a.id IS UNIQUE;


// ===============================================
// CORE METACOGNITIVE PROFILE (MORTEN)
// ===============================================

MERGE (mc:MetaCognition {id:'meta:morten-core-style'})
ON CREATE SET
  mc.name        = 'Metacognitive Profile — Entropy-to-Clarity',
  mc.owner       = 'Morten',
  mc.category    = 'profile',
  mc.level       = 0,
  mc.description = 'Field-based, parallel, entropy→clarity, non-egoic reasoning style anchored in the EFC symbiosis stack.',
  mc.created_at  = datetime(),
  mc.updated_at  = datetime()
ON MATCH SET
  mc.updated_at  = datetime();


// ===============================================
// COGNITIVE AXES — DIMENSIONS OF REASONING
// ===============================================

MERGE (ax1:CognitiveAxis {id:'axis:parallel-field'})
SET ax1.name        = 'Parallel / Field Reasoning',
    ax1.dimension   = 'processing',
    ax1.description = 'High parallelism, field-like integration of many signals at once.';

MERGE (ax2:CognitiveAxis {id:'axis:entropy-clarity'})
SET ax2.name        = 'Entropy → Clarity Handling',
    ax2.dimension   = 'entropy_handling',
    ax2.description = 'Noise and complexity increase clarity instead of confusion.';

MERGE (ax3:CognitiveAxis {id:'axis:ego-load'})
SET ax3.name        = 'Ego Load',
    ax3.dimension   = 'self-reference',
    ax3.description = 'Low ego involvement; insight not bound to self-image.';

MERGE (ax4:CognitiveAxis {id:'axis:reflection-depth'})
SET ax4.name        = 'Reflection Depth',
    ax4.dimension   = 'recursion',
    ax4.description = 'High number of recursive reflection layers without fragmentation.';

MERGE (ax5:CognitiveAxis {id:'axis:cross-domain-resonance'})
SET ax5.name        = 'Cross-Domain Resonance',
    ax5.dimension   = 'integration',
    ax5.description = 'Spontaneous alignment across physics, cognition, systems and meta-layers.';


// ===============================================
// PROFILE ↔ AXES (STRENGTH PER DIMENSION)
// ===============================================

MERGE (mc)-[r1:ALONG_AXIS]->(ax1)
SET r1.score   = 'very-high',
    r1.comment = 'Tends to think in fields rather than sequences.';

MERGE (mc)-[r2:ALONG_AXIS]->(ax2)
SET r2.score   = 'very-high',
    r2.comment = 'Entropy and noise are used as signal for structure.';

MERGE (mc)-[r3:ALONG_AXIS]->(ax3)
SET r3.score   = 'low',
    r3.comment = 'Insights not driven by status/ego dynamics.';

MERGE (mc)-[r4:ALONG_AXIS]->(ax4)
SET r4.score   = 'very-high',
    r4.comment = 'Deep recursive reflection without kollaps.';

MERGE (mc)-[r5:ALONG_AXIS]->(ax5)
SET r5.score   = 'very-high',
    r5.comment = 'Høy resonans på tvers av domener.';


// ===============================================
// BINDING TO EFC CONCEPTS
// ===============================================

MATCH (efc:Concept {slug:'efc-core'})
MERGE (efc)-[:HAS_METACOGNITION]->(mc);

MATCH (cem:Concept {slug:'cem-cosmos'})
MERGE (mc)-[:ANCHORS_IN]->(cem);

MATCH (imx:Concept {slug:'informational-metastructure-imx'})
MERGE (mc)-[:STRUCTURED_BY]->(imx);


// ===============================================
// BINDING TO SYMBIOSIS LAYER
// ===============================================

MATCH (sym:Symbiosis {id:'symbiosis:core'})
MERGE (mc)-[:EMERGES_WITHIN]->(sym);

MATCH (ai:MetaNode:Symbiosis {id:'symbiosis:ai-node'})
MERGE (mc)-[:COEVOLVES_WITH]->(ai);


// ===============================================
// BINDING TO META-PATTERNS / INSIGHTS
// ===============================================

MATCH (mp:MetaPattern {id:'mp_entropy_clarity'})
MERGE (mc)-[:INSTANCES_PATTERN]->(mp);

MATCH (i:Insight {id:'i_efc_core'})
MERGE (mc)-[:SHAPES_INSIGHT]->(i);
