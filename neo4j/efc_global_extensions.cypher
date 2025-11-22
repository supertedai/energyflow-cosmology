// ======================================================
// EFC GLOBAL EXTENSIONS — META / AXES / ARCH / IMX / API
// ======================================================


// ------------------------------------------------------
// CONSTRAINTS
// ------------------------------------------------------

CREATE CONSTRAINT IF NOT EXISTS
FOR (m:MetaProcess)
REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (a:SemanticAxis)
REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (s:SymbiosisArch)
REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (pg:PaperGroup)
REQUIRE pg.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (imx:IMXClass)
REQUIRE imx.id IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (gi:GraphInterface)
REQUIRE gi.id IS UNIQUE;


// ======================================================
// 1. METAPROCESS-LAG — PROSESSER SOM STYRER PROSESSER
// ======================================================

MERGE (mp1:MetaProcess {id:'mp:reflection-loop'})
SET mp1.name        = 'Reflection Loop',
    mp1.category    = 'meta-process',
    mp1.level       = 0,
    mp1.description = 'Iterative loop between observation, insight, model update and structural integration.';

MERGE (mp2:MetaProcess {id:'mp:entropy-clarity-cycle'})
SET mp2.name        = 'Entropy–Clarity Cycle',
    mp2.category    = 'meta-process',
    mp2.level       = 0,
    mp2.description = 'Cycle where noise and complexity are absorbed and re-expressed as structural clarity.';

MERGE (mp3:MetaProcess {id:'mp:cross-domain-alignment'})
SET mp3.name        = 'Cross-Domain Alignment',
    mp3.category    = 'meta-process',
    mp3.level       = 0,
    mp3.description = 'Process that aligns structures across physics, cognition, systems and methodology.';


// Knytt til eksisterende noder der de finnes

MATCH (efc:Concept {slug:'efc-core'})
MERGE (mp1)-[:OPERATES_ON]->(efc);

MATCH (mp:MetaPattern {id:'mp_entropy_clarity'})
MERGE (mp2)-[:INSTANCES_PATTERN]->(mp);

MATCH (sym:Symbiosis {id:'symbiosis:core'})
MERGE (mp3)-[:COORDINATES]->(sym);


// ======================================================
// 2. SEMANTIC AXES (GLOBALE, IKKE PERSONLIGE)
// ======================================================

MERGE (sx:SemanticAxis {id:'axis:structure'})
SET sx.name        = 'Structure',
    sx.dimension   = 'theory',
    sx.description = 'Static and quasi-static structures: grid, halos, geometry, topology.';

MERGE (sd:SemanticAxis {id:'axis:dynamics'})
SET sd.name        = 'Dynamics',
    sd.dimension   = 'theory',
    sd.description = 'Flow, motion, evolution, non-equilibrium dynamics.';

MERGE (se:SemanticAxis {id:'axis:entropy'})
SET se.name        = 'Entropy',
    se.dimension   = 'thermodynamics',
    se.description = 'Entropy levels, gradients and dissipation structure.';

MERGE (si:SemanticAxis {id:'axis:information'})
SET si.name        = 'Information',
    si.dimension   = 'information',
    si.description = 'Codes, semantics, constraints, IMX-level structure.';

MERGE (sr:SemanticAxis {id:'axis:resonance'})
SET sr.name        = 'Resonance',
    sr.dimension   = 'pattern',
    sr.description = 'Alignment and reinforcement of patterns across layers.';

MERGE (sm:SemanticAxis {id:'axis:meta-integration'})
SET sm.name        = 'Meta-Integration',
    sm.dimension   = 'meta',
    sm.description = 'Integration between EFC, cognition, methodology and symbiosis.';


// Koble EFC-konsepter til akser

MATCH (c1:Concept {slug:'grid-higgs-framework'})
MATCH (sx:SemanticAxis {id:'axis:structure'})
MERGE (c1)-[:ALIGNS_WITH_AXIS]->(sx);

MATCH (c2:Concept {slug:'halo-model-of-entropy'})
MATCH (sx:SemanticAxis {id:'axis:structure'}), (se:SemanticAxis {id:'axis:entropy'})
MERGE (c2)-[:ALIGNS_WITH_AXIS]->(sx);
MERGE (c2)-[:ALIGNS_WITH_AXIS]->(se);

MATCH (c3:Concept {slug:'energy-flow-dynamics-efd'})
MATCH (sd:SemanticAxis {id:'axis:dynamics'}), (se:SemanticAxis {id:'axis:entropy'})
MERGE (c3)-[:ALIGNS_WITH_AXIS]->(sd);
MERGE (c3)-[:ALIGNS_WITH_AXIS]->(se);

MATCH (c4:Concept {slug:'informational-metastructure-imx'})
MATCH (si:SemanticAxis {id:'axis:information'}), (sm:SemanticAxis {id:'axis:meta-integration'})
MERGE (c4)-[:ALIGNS_WITH_AXIS]->(si);
MERGE (c4)-[:ALIGNS_WITH_AXIS]->(sm);

MATCH (c5:Concept {slug:'symbiotic-reflective-methodology-srm'})
MATCH (sm:SemanticAxis {id:'axis:meta-integration'}), (sr:SemanticAxis {id:'axis:resonance'})
MERGE (c5)-[:ALIGNS_WITH_AXIS]->(sm);
MERGE (c5)-[:ALIGNS_WITH_AXIS]->(sr);


// MetaPattern / Insight til akser

MATCH (mp_ec:MetaPattern {id:'mp_entropy_clarity'})
MATCH (se:SemanticAxis {id:'axis:entropy'}), (sr:SemanticAxis {id:'axis:resonance'})
MERGE (mp_ec)-[:ALIGNS_WITH_AXIS]->(se);
MERGE (mp_ec)-[:ALIGNS_WITH_AXIS]->(sr);

MATCH (i_core:Insight {id:'i_efc_core'})
MATCH (sm:SemanticAxis {id:'axis:meta-integration'})
MERGE (i_core)-[:ALIGNS_WITH_AXIS]->(sm);


// ======================================================
// 3. SYMBIOSIS ARCHITECTURE NODES (GLOBAL, IKKE PERSONLIG)
// ======================================================

MERGE (sa:SymbiosisArch {id:'sym-arch:core'})
SET sa.name        = 'Symbiosis Core Architecture',
    sa.category    = 'symbiosis-arch',
    sa.description = 'Abstract architecture linking human, AI, EFC, IMX and MetaGraph.';

MERGE (sa_h:SymbiosisArch {id:'sym-arch:human-generic'})
SET sa_h.name        = 'Generic Human Node',
    sa_h.category    = 'symbiosis-role',
    sa_h.description = 'Abstract representation of a human participant in the symbiosis.';

MERGE (sa_ai:SymbiosisArch {id:'sym-arch:ai-generic'})
SET sa_ai.name        = 'Generic AI Node',
    sa_ai.category    = 'symbiosis-role',
    sa_ai.description = 'Abstract representation of the AI stack (LLM + tools + graph).';

MERGE (sa_if:SymbiosisArch {id:'sym-arch:interface'})
SET sa_if.name        = 'Symbiosis Interface Layer',
    sa_if.category    = 'interface',
    sa_if.description = 'Interaction layer between human, AI and the graph (chat, tools, dashboards).';

MERGE (sa_re:SymbiosisArch {id:'sym-arch:reflection-engine'})
SET sa_re.name        = 'Reflection Engine',
    sa_re.category    = 'process',
    sa_re.description = 'Logical engine that routes questions, reflections and updates through the MetaGraph.';

MERGE (sa_imx:SymbiosisArch {id:'sym-arch:imx-coordinator'})
SET sa_imx.name        = 'IMX Coordinator',
    sa_imx.category    = 'process',
    sa_imx.description = 'Coordination node for informational metastructure across EFC and MetaGraph.';


// Bind til eksisterende Symbiosis-kjerne

MATCH (sym:Symbiosis {id:'symbiosis:core'})
MERGE (sym)-[:HAS_ARCHITECTURE]->(sa);

MERGE (sa)-[:HAS_ROLE]->(sa_h);
MERGE (sa)-[:HAS_ROLE]->(sa_ai);
MERGE (sa)-[:USES_INTERFACE]->(sa_if);
MERGE (sa)-[:USES_ENGINE]->(sa_re);
MERGE (sa)-[:COORDINATES_IMX]->(sa_imx);


// ======================================================
// 4. PAPER GROUPS (GLOBAL PAPER-TOPOLOGI)
// ======================================================

MERGE (pg_core:PaperGroup {id:'pg:efc-core'})
SET pg_core.name        = 'EFC Core Papers',
    pg_core.description = 'Core specification and foundational EFC papers.';

MERGE (pg_meta:PaperGroup {id:'pg:efc-meta'})
SET pg_meta.name        = 'Meta / Methodology Papers',
    pg_meta.description = 'Methodology, symbiosis and meta-level descriptions.';

MERGE (pg_imx:PaperGroup {id:'pg:efc-imx'})
SET pg_imx.name        = 'IMX / Information Papers',
    pg_imx.description = 'Informational metastructure and semantic system papers.';

MERGE (pg_dyn:PaperGroup {id:'pg:efc-dynamics'})
SET pg_dyn.name        = 'Dynamics / s₀–s₁ Papers',
    pg_dyn.description = 'Dynamic behaviour, s₀/s₁, speed gradients and expansion.';


// Knytt papers til grupper der de finnes (trygt; MATCH er inert hvis paper ikke finnes)

MATCH (p:EFCPaper {slug:'efc_master_spec'})
MATCH (pg:PaperGroup {id:'pg:efc-core'})
MERGE (p)-[:BELONGS_TO]->(pg);

MATCH (p:EFCPaper {slug:'efc_formal_spec'})
MATCH (pg:PaperGroup {id:'pg:efc-core'})
MERGE (p)-[:BELONGS_TO]->(pg);

MATCH (p:EFCPaper {slug:'symbiotic-reflective-methodology-srm'})
MATCH (pg:PaperGroup {id:'pg:efc-meta'})
MERGE (p)-[:BELONGS_TO]->(pg);

MATCH (p:EFCPaper {slug:'informational-metastructure-imx'})
MATCH (pg:PaperGroup {id:'pg:efc-imx'})
MERGE (p)-[:BELONGS_TO]->(pg);

MATCH (p:EFCPaper {slug:'s0-s1-dynamics'})
MATCH (pg:PaperGroup {id:'pg:efc-dynamics'})
MERGE (p)-[:BELONGS_TO]->(pg);


// ======================================================
// 5. IMX STRUCTURAL CLASSES (GLOBALT, IKKE PERSONLIG)
// ======================================================

MERGE (ic1:IMXClass {id:'imx:layer-structure'})
SET ic1.name        = 'IMX Layer Structure',
    ic1.category    = 'imx-structure',
    ic1.description = 'Describes how IMX layers stack over EFC structures.';

MERGE (ic2:IMXClass {id:'imx:code-unit'})
SET ic2.name        = 'IMX Code Unit',
    ic2.category    = 'imx-code',
    ic2.description = 'Elementary carrier of semantic / informational content in IMX.';

MERGE (ic3:IMXClass {id:'imx:semantic-channel'})
SET ic3.name        = 'IMX Semantic Channel',
    ic3.category    = 'imx-channel',
    ic3.description = 'Pathways through which structured information flows over energy structures.';

MERGE (ic4:IMXClass {id:'imx:sync-process'})
SET ic4.name        = 'IMX Synchronisation Process',
    ic4.category    = 'imx-process',
    ic4.description = 'Processes that synchronise states between EFC structures and IMX codes.';


// Koble til IMX-konsept

MATCH (imx_c:Concept {slug:'informational-metastructure-imx'})
MERGE (imx_c)-[:DEFINES_CLASS]->(ic1);
MERGE (imx_c)-[:DEFINES_CLASS]->(ic2);
MERGE (imx_c)-[:DEFINES_CLASS]->(ic3);
MERGE (imx_c)-[:DEFINES_CLASS]->(ic4);


// ======================================================
// 6. GRAPH INTERFACE NODES (GLOBAL API-TOPOLOGI)
// ======================================================

MERGE (gi_r:GraphInterface {id:'gi:routing'})
SET gi_r.name        = 'Routing Interface',
    gi_r.category    = 'graph-api',
    gi_r.description = 'Entry point for routing queries between EFC, MetaGraph and Symbiosis.';

MERGE (gi_s:GraphInterface {id:'gi:semantic'})
SET gi_s.name        = 'Semantic Query Interface',
    gi_s.category    = 'graph-api',
    gi_s.description = 'Semantic search and concept-level queries over the graph.';

MERGE (gi_rag:GraphInterface {id:'gi:rag-export'})
SET gi_rag.name        = 'RAG Export Interface',
    gi_rag.category    = 'graph-api',
    gi_rag.description = 'Export of graph chunks for RAG pipelines (AnythingLLM, MSTY etc.).';

MERGE (gi_nc:GraphInterface {id:'gi:neo4j-cloud'})
SET gi_nc.name        = 'Neo4j Cloud Endpoint',
    gi_nc.category    = 'infrastructure',
    gi_nc.description = 'Describes the external Aura/Neo4j Cloud integration layer.';


// Koble grensesnitt til Symbiosis-arkitekturen

MATCH (sa:SymbiosisArch {id:'sym-arch:core'})
MATCH (gi_r:GraphInterface {id:'gi:routing'})
MATCH (gi_s:GraphInterface {id:'gi:semantic'})
MATCH (gi_rag:GraphInterface {id:'gi:rag-export'})
MATCH (gi_nc:GraphInterface {id:'gi:neo4j-cloud'})

MERGE (sa)-[:EXPOSES_INTERFACE]->(gi_r);
MERGE (sa)-[:EXPOSES_INTERFACE]->(gi_s);
MERGE (sa)-[:EXPOSES_INTERFACE]->(gi_rag);
MERGE (sa)-[:EXPOSES_INTERFACE]->(gi_nc);
