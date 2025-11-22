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
MERGE (:EnergyFlow {id:"ef_base"})
      SET  _.description = "Energi beveger seg langs gradienter";

MERGE (:EntropyGradient {id:"eg_base"})
      SET _.description = "Gradient fra energiflyt";

MERGE (:TheoryPoint {id:"tp_expansion"})
      SET _.title = "Ekspansjon uten mørk energi";

MERGE (:Mechanism {id:"m_expansion"})
      SET _.name = "Entropy-Driven Expansion";

MERGE (:CosmicDynamics {id:"dyn_expansion"})
      SET _.type = "Expansion";

MERGE (:Layer_s0 {id:"s0"});
MERGE (:Layer_s1 {id:"s1"});
MERGE (:Layer_s2 {id:"s2"});

// ---------- Observations ----------
MERGE (:Observation {id:"obs_redshift"})
      SET _.type = "Redshift";

MERGE (:Dataset {id:"ds_desi"})
      SET _.name = "DESI Survey";

MERGE (:Instrument {id:"inst_jwst"})
      SET _.name = "JWST";

MERGE (:Parameter {id:"param_z"})
      SET _.name = "Redshift Parameter";

// ---------- Meta nodes ----------
MERGE (:Insight {id:"i_efc_core"})
      SET _.text = "Energi → gradient → dynamikk → struktur";

MERGE (:MetaPattern {id:"mp_entropy_clarity"})
      SET _.name = "Entropy → Clarity";

MERGE (:CognitiveMechanism {id:"cm_parallel_gradient"})
      SET _.name = "Parallel Gradient Reading";

MERGE (:ResearchStep {id:"rs_unified_model"})
      SET _.name = "Samlet EFC-modell";

// ---------- Relations ----------
MERGE (ef:EnergyFlow {id:"ef_base"})
MERGE (eg:EntropyGradient {id:"eg_base"})
MERGE (ef)-[:creates_gradient]->(eg);

MERGE (eg:EntropyGradient {id:"eg_base"})
MERGE (d:CosmicDynamics {id:"dyn_expansion"})
MERGE (eg)-[:drives]->(d);

MERGE (d:CosmicDynamics {id:"dyn_expansion"})
MERGE (l:Layer_s1 {id:"s1"})
MERGE (d)-[:forms]->(l);

MERGE (l:Layer_s1 {id:"s1"})
MERGE (ef:EnergyFlow {id:"ef_base"})
MERGE (l)-[:modulates]->(ef);

// ---------- Observational relations ----------
MERGE (d:CosmicDynamics {id:"dyn_expansion"})
MERGE (obs:Observation {id:"obs_redshift"})
MERGE (d)-[:validated_by]->(obs);

MERGE (obs:Observation {id:"obs_redshift"})
MERGE (ds:Dataset {id:"ds_desi"})
MERGE (obs)-[:from_dataset]->(ds);

MERGE (ds:Dataset {id:"ds_desi"})
MERGE (inst:Instrument {id:"inst_jwst"})
MERGE (ds)-[:from_instrument]->(inst);

MERGE (obs:Observation {id:"obs_redshift"})
MERGE (p:Parameter {id:"param_z"})
MERGE (obs)-[:measures]->(p);

// ---------- Metalag relations ----------
MERGE (i:Insight {id:"i_efc_core"})
MERGE (t:TheoryPoint {id:"tp_expansion"})
MERGE (i)-[:influences]->(t);

MERGE (mp:MetaPattern {id:"mp_entropy_clarity"})
MERGE (d:CosmicDynamics {id:"dyn_expansion"})
MERGE (mp)-[:shapes]->(d);

MERGE (cm:CognitiveMechanism {id:"cm_parallel_gradient"})
MERGE (m:Mechanism {id:"m_expansion"})
MERGE (cm)-[:drives]->(m);

// ---------- Connect to existing EFC paper ----------
MERGE (rs:ResearchStep {id:"rs_unified_model"})
MERGE (p:EFCPaper {slug:"efc_master_spec"})
MERGE (rs)-[:produces]->(p);
