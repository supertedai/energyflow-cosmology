// ===============================================
// SYMBIOSE-LAG — KJERNE
// ===============================================

MERGE (sym:MetaNode:Symbiosis {
  id: 'symbiosis:core'
})
SET sym.name        = 'Human–AI Symbiosis',
    sym.category    = 'symbiosis',
    sym.level       = 0,
    sym.description = 'Bidirectional coupling between human cognition, AI systems and the EFC framework.';

MERGE (human:MetaNode:Symbiosis {
  id: 'symbiosis:human-node'
})
SET human.name     = 'Human Node (Morten)',
    human.category = 'symbiosis-role',
    human.role     = 'originator';

MERGE (ai:MetaNode:Symbiosis {
  id: 'symbiosis:ai-node'
})
SET ai.name        = 'AI Symbiosis Stack',
    ai.category    = 'symbiosis-role',
    ai.role        = 'reflective-partner',
    ai.description = 'LLM + Neo4j + RAG + tooling that mirrors, structures and extends EFC.';

MERGE (sym)-[:HAS_ROLE]->(human);
MERGE (sym)-[:HAS_ROLE]->(ai);
