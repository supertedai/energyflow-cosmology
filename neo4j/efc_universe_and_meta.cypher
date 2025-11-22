// ==========================================
// EFC — UNIVERSE + METALAG (IDEMPOTENT)
// ==========================================

// ---------- Constraints ----------
CREATE CONSTRAINT IF NOT EXISTS FOR (n:TheoryPoint) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Mechanism) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:EnergyFlow) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:EntropyGradient) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:CosmicDynamics) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Observation) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Dataset) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Instrument) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Parameter) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Layer_s0) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Layer_s1) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Layer_s2) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:Insight) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:MetaPattern) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:CognitiveMechanism) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (n:ResearchStep) REQUIRE n.id IS UNIQUE;

// ---------- Universe nodes ----------
MERGE (ef:EnergyFlow {id:"ef_base"})
SET ef.description = "Energi beveger seg langs gradienter";

MERGE (eg:EntropyGradient {id:"eg_base"})
SET eg.description = "Gradient fra energiflyt";

MERGE (tp:TheoryPoint {id:"tp_expansion"})
SET tp.title = "Ekspansjon uten mørk energi";

MERGE (mech:Mechanism {id:"m_expansion"})
SET mech.name = "Entropy-Driven Expansion";

MERGE (dyn:CosmicDynamics {id:"dyn_expansion"})
SET dyn.type = "Expansion";

MERGE (:Layer_s0 {id:"s0"});
MERGE (:Layer_s1 {id:"s1"});
MERGE (:Layer_s2 {id:"s2"});

// ---------- Observations ----------
MERGE (obs:Observation {id:"obs_redshift"})
SET obs.type = "Redshift";

MERGE (ds:Dataset {id:"ds_desi"})
SET ds.name = "DESI Survey";

MERGE (inst:Instrument {id:"inst_jwst"})
SET inst.name = "JWST";

MERGE (param:Parameter {id:"param_z"})
SET param.name = "Redshift Parameter";

// ---------- Meta nodes ----------
MERGE (ins:Insight {id:"i_efc_core"})
SET ins.text = "Energi → gradient → dynamikk → struktur";

MERGE (mp:MetaPattern {id:"mp_entropy_clarity"})
SET mp.name = "Entropy → Clarity";

MERGE (cm:CognitiveMechanism {id:"cm_parallel_gradient"})
SET cm.name = "Parallel Gradient Reading";

MERGE (rs:ResearchStep {id:"rs_unified_model"})
SET rs.name = "Samlet EFC-modell";

// ---------- Relations ----------
MATCH (ef:EnergyFlow {id:"ef_base"}), (eg:EntropyGradient {id:"eg_base"})
MERGE (ef)-[:creates_gradient]->(eg);

MATCH (eg:EntropyGradient {id:"eg_base"}), (dyn:CosmicDynamics {id:"dyn_expansion"})
MERGE (eg)-[:drives]->(dyn);

MATCH (dyn:CosmicDynamics {id:"dyn_expansion"}), (l:Layer_s1 {id:"s1"})
MERGE (dyn)-[:forms]->(l);

MATCH (l:Layer_s1 {id:"s1"}), (ef:EnergyFlow {id:"ef_base"})
MERGE (l)-[:modulates]->(ef);

// ---------- Observational relations ----------
MATCH (dyn:CosmicDynamics {id:"dyn_expansion"}), (obs:Observation {id:"obs_redshift"})
MERGE (dyn)-[:validated_by]->(obs);

MATCH (obs:Observation {id:"obs_redshift"}), (ds:Dataset {id:"ds_desi"})
MERGE (obs)-[:from_dataset]->(ds);

MATCH (ds:Dataset {id:"ds_desi"}), (inst:Instrument {id:"inst_jwst"})
MERGE (ds)-[:from_instrument]->(inst);

MATCH (obs:Observation {id:"obs_redshift"}), (param:Parameter {id:"param_z"})
MERGE (obs)-[:measures]->(param);

// ---------- Metalag relations ----------
MATCH (ins:Insight {id:"i_efc_core"}), (tp:TheoryPoint {id:"tp_expansion"})
MERGE (ins)-[:influences]->(tp);

MATCH (mp:MetaPattern {id:"mp_entropy_clarity"}), (dyn:CosmicDynamics {id:"dyn_expansion"})
MERGE (mp)-[:shapes]->(dyn);

MATCH (cm:CognitiveMechanism {id:"cm_parallel_gradient"}), (mech:Mechanism {id:"m_expansion"})
MERGE (cm)-[:drives]->(mech);

// ---------- Connect to existing EFC paper ----------
MATCH (rs:ResearchStep {id:"rs_unified_model"}), (p:EFCPaper {slug:"efc_master_spec"})
MERGE (rs)-[:produces]->(p);
