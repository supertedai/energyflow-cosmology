// ==========================================
// EFC — UNIVERSE + METALAG
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
CREATE (:EnergyFlow {id:"ef_base", description:"Energi beveger seg langs gradienter"});
CREATE (:EntropyGradient {id:"eg_base", description:"Gradient fra energiflyt"});
CREATE (:TheoryPoint {id:"tp_expansion", title:"Ekspansjon uten mørk energi"});
CREATE (:Mechanism {id:"m_expansion", name:"Entropy-Driven Expansion"});

CREATE (:CosmicDynamics {id:"dyn_expansion", type:"Expansion"});

CREATE (:Layer_s0 {id:"s0"});
CREATE (:Layer_s1 {id:"s1"});
CREATE (:Layer_s2 {id:"s2"});

// ---------- Observation nodes ----------
CREATE (:Observation {id:"obs_redshift", type:"Redshift"});
CREATE (:Dataset {id:"ds_desi", name:"DESI Survey"});
CREATE (:Instrument {id:"inst_jwst", name:"JWST"});
CREATE (:Parameter {id:"param_z", name:"Redshift Parameter"});

// ---------- Meta nodes ----------
CREATE (:Insight {id:"i_efc_core", text:"Energi → gradient → dynamikk → struktur"});
CREATE (:MetaPattern {id:"mp_entropy_clarity", name:"Entropy → Clarity"});
CREATE (:CognitiveMechanism {id:"cm_parallel_gradient", name:"Parallel Gradient Reading"});
CREATE (:ResearchStep {id:"rs_unified_model", name:"Samlet EFC-modell"});

// ---------- Universe causal chain ----------
MATCH (ef:EnergyFlow {id:"ef_base"}), (eg:EntropyGradient {id:"eg_base"})
CREATE (ef)-[:creates_gradient]->(eg);

MATCH (eg:EntropyGradient {id:"eg_base"}), (d:CosmicDynamics {id:"dyn_expansion"})
CREATE (eg)-[:drives]->(d);

MATCH (d:CosmicDynamics {id:"dyn_expansion"}), (l:Layer_s1 {id:"s1"})
CREATE (d)-[:forms]->(l);

MATCH (l:Layer_s1 {id:"s1"}), (ef:EnergyFlow {id:"ef_base"})
CREATE (l)-[:modulates]->(ef);

// ---------- Observational chain ----------
MATCH (d:CosmicDynamics {id:"dyn_expansion"}), (obs:Observation {id:"obs_redshift"})
CREATE (d)-[:validated_by]->(obs);

MATCH (obs:Observation {id:"obs_redshift"}), (ds:Dataset {id:"ds_desi"})
CREATE (obs)-[:from_dataset]->(ds);

MATCH (ds:Dataset {id:"ds_desi"}), (inst:Instrument {id:"inst_jwst"})
CREATE (ds)-[:from_instrument]->(inst);

MATCH (obs:Observation {id:"obs_redshift"}), (p:Parameter {id:"param_z"})
CREATE (obs)-[:measures]->(p);

// ---------- Metalag ----------
MATCH (i:Insight {id:"i_efc_core"}), (t:TheoryPoint {id:"tp_expansion"})
CREATE (i)-[:influences]->(t);

MATCH (mp:MetaPattern {id:"mp_entropy_clarity"}), (d:CosmicDynamics {id:"dyn_expansion"})
CREATE (mp)-[:shapes]->(d);

MATCH (cm:CognitiveMechanism {id:"cm_parallel_gradient"}), (m:Mechanism {id:"m_expansion"})
CREATE (cm)-[:drives]->(m);

// ---------- Connect metalag to EFCPaper (existing graph) ----------
MATCH (rs:ResearchStep {id:"rs_unified_model"}), (p:EFCPaper {slug:"efc_master_spec"})
CREATE (rs)-[:produces]->(p);
