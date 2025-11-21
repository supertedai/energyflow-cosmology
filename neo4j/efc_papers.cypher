// AUTH-layer paper (eksempel)
WITH datetime() AS now
MERGE (p:Paper {
  doi: '10.1234/efc.AUTH-layer.v1.0'
})
ON CREATE SET
  p.id = 'paper:AUTH-layer-v1.0',
  p.title = 'AUTH Layer – Origin, Provenance and Structural Signature of Energy-Flow Cosmology',
  p.version = '1.0',
  p.year = 2025,
  p.figshare_id = '30636863',   // juster til faktisk ID
  p.path = 'docs/papers/efc/AUTH-Layer-Origin-Provenance-and-Structural-Signature-of-Energy-Flow-Cosmology',
  p.url = 'https://figshare.com/...',   // faktisk lenke
  p.created_at = now,
  p.updated_at = now;

// Koble paper til konsepter det beskriver
MATCH (p:Paper {doi:'10.1234/efc.AUTH-layer.v1.0'})
MATCH (efc:Concept {slug:'efc-core'})
MERGE (p)-[:DESCRIBES]->(efc);

MATCH (p:Paper {doi:'10.1234/efc.AUTH-layer.v1.0'})
MATCH (imx:Concept {slug:'informational-metastructure-imx'})
MERGE (p)-[:DESCRIBES]->(imx);

MATCH (p:Paper {doi:'10.1234/efc.AUTH-layer.v1.0'})
MATCH (srm:Concept {slug:'symbiotic-reflective-methodology-srm'})
MERGE (p)-[:DESCRIBES]->(srm);
