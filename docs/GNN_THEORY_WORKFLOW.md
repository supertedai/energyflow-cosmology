# GNN-Augmented EFC Theory Development

**Graph Neural Network system for Energy-Flow Cosmology theory expansion**

This system uses GNN link prediction to suggest new theoretical connections while maintaining formal consistency with EFC principles.

---

## 🎯 **Core Philosophy**

**GNN sees ONLY crystallized theory structure - NOT document/chunk graph**

We train on:
- **Nodes**: `Concept`, `Equation`, `Model`, `Framework`
- **Edges**: `SUPPORTS`, `CONSTRAINS`, `PART_OF`, `GOVERNS`, `ANALOGOUS_TO`

We **exclude**:
- Document nodes
- Chunk nodes
- File organization edges
- Private/non-EFC content

---

## 📋 **Complete Workflow**

```
1. Export EFC Core → 2. Train GNN → 3. Generate Suggestions → 4. Validate → 5. Human Review → 6. Promote/Reject
```

### **Step 1: Export EFC Core Graph**

Extract only theory-level structure from Neo4j:

```bash
python tools/gnn_export.py --output symbiose_gnn_output/efc_core_graph.pt
```

**What it does:**
- Queries Neo4j for `Concept`, `Equation`, `Model`, `Framework` nodes
- Extracts theory-level edges (SUPPORTS, CONSTRAINS, etc.)
- Generates text embeddings for concepts
- Builds PyTorch Geometric data structure
- Saves to `.pt` file

**Output:**
```
symbiose_gnn_output/efc_core_graph.pt:
  - x: Node features (domain, layer, stability, embeddings)
  - edge_index: Edge connectivity
  - edge_type: Edge type indices
  - node_metadata: Concept names, IDs, domains
```

---

### **Step 2: Train GNN**

Train Graph Attention Network on link prediction:

```bash
python tools/gnn_train.py \
  --input symbiose_gnn_output/efc_core_graph.pt \
  --epochs 200
```

**Architecture:**
- **Base**: Graph Attention Network (GAT)
- **Layers**: 3 GAT layers with 4 attention heads
- **Task**: Predict missing edges between concepts
- **Loss**: Binary cross-entropy (positive edges vs negative samples)

**Training splits:**
- 70% train
- 15% validation
- 15% test

**Metrics:**
- **AUC-ROC**: Area under ROC curve (> 0.7 = good)
- **Hits@10**: % of correct edges in top-10 predictions

**Output:**
```
symbiose_gnn_output/efc_gnn_best.pt:
  - model_state_dict: Trained weights
  - predictor_state_dict: Link prediction head
  - val_auc: Validation performance
  - graph_metadata: Original graph data
```

---

### **Step 3: Generate Suggestions**

Use trained model to propose new relations:

```bash
python tools/gnn_inference.py \
  --model symbiose_gnn_output/efc_gnn_best.pt \
  --top-k 50 \
  --min-confidence 0.7
```

**What it does:**
- Loads trained GNN model
- Generates embeddings for all concepts
- Evaluates all possible concept pairs
- Predicts edge existence + type for each pair
- Filters by confidence threshold
- Saves top-K suggestions to Neo4j as `GNNSuggestion` nodes

**Neo4j output:**
```cypher
(:Concept {name: "Entropy Gradient"})
  -[:HAS_SUGGESTION]->
(:GNNSuggestion {
  confidence: 0.91,
  suggested_relation: "SUPPORTS",
  status: "PENDING"
})
  -[:SUGGESTS_RELATION]->
(:Concept {name: "Adaptive Energy-Flow Window"})
```

---

### **Step 4: Automated Validation**

Run 4-step validation on suggestions:

```bash
# Single suggestion
python tools/gnn_theory_validator.py --suggestion-id sugg_001

# Batch validation
python tools/gnn_theory_validator.py --batch --min-confidence 0.85
```

**4-Step Validation Process:**

#### **1️⃣ Formal Consistency**
Checks if relation violates EFC fundamentals:
- ❌ Energy conservation violations
- ❌ ∇S direction conflicts
- ❌ Ef role mismatches
- ❌ Matter-first ontology assumptions

**Result:** `formal_consistency: true/false` + list of issues

#### **2️⃣ Theory Proximity**
Measures closeness to existing structure:
- Shortest path length between concepts
- Shared parent concepts/models
- Existing implicit connections

**Result:** `theory_proximity: 0.0-1.0`
- 1.0 = Already directly connected (redundant)
- 0.85 = One intermediate concept
- 0.0 = No existing connection (novel bridge)

#### **3️⃣ Energy/Entropy Intuition**
Uses LLM + EFC principles to assess:
- Does it clarify energy flow patterns?
- Does it reduce theoretical entropy?
- Does it bridge levels (cosmo ↔ bio ↔ cognition ↔ AI)?
- Does it enhance explanatory power for:
  - Halo structures
  - Rotation curves
  - CMB interpretation
  - Structure formation

**Result:** `energy_intuition: 0.0-1.0` + rationale

#### **4️⃣ Integration Level**
Classifies suggestion value:

- **TRIVIAL**: Already implicitly present
  - Example: Path length = 1 (already connected)
  - Action: Reject

- **USEFUL**: Clarifies structure
  - Example: Moderate proximity, decent intuition
  - Action: Human review

- **DEEP**: Novel insight
  - Example: Bridges distant concepts, high intuition
  - Action: Strong promote candidate

**Result:** `integration_level: TRIVIAL|USEFUL|DEEP`

---

### **Step 5: Human Review**

Review validation results:

```cypher
// Find pending suggestions requiring review
MATCH (s:GNNSuggestion {status: "PENDING"})
OPTIONAL MATCH (s)-[:HAS_VALIDATION]->(v:ValidationResult)
WHERE v.integration_level IN ["USEFUL", "DEEP"]
RETURN 
  s.source_name,
  s.target_name,
  s.suggested_relation,
  s.confidence,
  v.formal_consistency,
  v.theory_proximity,
  v.energy_intuition,
  v.integration_level,
  v.overall_rationale
ORDER BY s.confidence DESC
```

**Human decision criteria:**
1. ✅ Formal consistency must be TRUE
2. ✅ Integration level must be USEFUL or DEEP
3. ✅ Rationale must make physical sense
4. ✅ Must not conflict with unpublished work
5. ✅ Must enhance (not complicate) theory

---

### **Step 6: Promote or Reject**

After human review, finalize decision:

#### **Promote** (Accept suggestion):

```cypher
MATCH (s:GNNSuggestion {id: "sugg_001"})
MATCH (source:Concept {id: s.source_concept_id})
MATCH (target:Concept {id: s.target_concept_id})

// Create actual relation
CREATE (source)-[r:SUPPORTS {
  weight: s.confidence,
  source: "gnn_suggestion",
  promoted_at: datetime(),
  promoted_by: "morpheus",
  rationale: "Consistent with ∇S → Ef stability window theorem"
}]->(target)

// Mark as promoted
SET s.status = "PROMOTED",
    s.validated_at = datetime(),
    s.validated_by = "morpheus",
    s.rationale = "Consistent with ∇S → Ef stability window theorem"

RETURN r
```

#### **Reject** (Decline suggestion):

```cypher
MATCH (s:GNNSuggestion {id: "sugg_001"})

SET s.status = "REJECTED",
    s.rejected_at = datetime(),
    s.rejected_by = "morpheus",
    s.rejection_reason = "Conflicts with energy conservation in expanding universe context"

RETURN s
```

---

## 🗂️ **Neo4j Schema**

### **Core Theory Nodes**

```cypher
(:Concept {
  id: "energy_flow",
  name: "Energy Flow",
  description: "...",
  domain: "cosmology",           // cosmology|thermodynamics|meta|cognition|ai
  layer: "formal",               // formal|applied|meta|cognitive
  stability_score: 0.95,         // How established (0-1)
  mention_count_efc: 142,        // Mentions in EFC docs
  mention_count_private: 37,     // Mentions in private work
  efc_core: true                 // Is this core to EFC?
})

(:Equation {
  id: "i0_formula",
  symbolic_form: "I0 = γ |Ef · ∇S|",
  domain: "information_theory"
})

(:Model {
  id: "halo_model",
  name: "Halo Model of Entropy"
})
```

### **Theory-Level Relations**

```cypher
(:Concept)-[:SUPPORTS]->(:Concept)        // Strengthens
(:Concept)-[:CONSTRAINS]->(:Concept)      // Sets boundaries
(:Concept)-[:PART_OF]->(:Model)           // Component of framework
(:Equation)-[:GOVERNS]->(:Concept)        // Math defines concept
(:Concept)-[:ANALOGOUS_TO]->(:Concept)    // Weak similarity
(:Concept)-[:DERIVES_FROM]->(:Concept)    // Logical derivation
(:Concept)-[:CONFLICTS_WITH]->(:Concept)  // Theoretical tension
```

### **GNN Suggestion Workflow**

```cypher
(:GNNSuggestion {
  id: "sugg_001",
  source_concept_id: "entropy_gradient",
  target_concept_id: "adaptive_window",
  source_name: "Entropy Gradient",
  target_name: "Adaptive Energy-Flow Window",
  suggested_relation: "SUPPORTS",
  confidence: 0.91,
  gnn_model: "efc_gnn_v1",
  status: "PENDING",              // PENDING|PROMOTED|REJECTED
  created_at: datetime()
})

(:ValidationResult {
  id: "val_001",
  suggestion_id: "sugg_001",
  formal_consistency: true,
  formal_issues: [],
  theory_proximity: 0.85,
  existing_path_length: 3,
  shared_parents: ["energy_conservation"],
  energy_intuition: 0.92,
  explanatory_power: "...",
  integration_level: "DEEP",
  integration_rationale: "...",
  decision: "PENDING",
  overall_rationale: "..."
})

// Workflow edges
(:Concept)-[:HAS_SUGGESTION]->(:GNNSuggestion)
(:GNNSuggestion)-[:SUGGESTS_RELATION]->(:Concept)
(:GNNSuggestion)-[:HAS_VALIDATION]->(:ValidationResult)
```

---

## 📊 **Interpreting Results**

### **GNN Training Metrics**

| Metric | Range | Interpretation |
|--------|-------|---------------|
| **AUC-ROC** | 0.5 | Random guessing - model is blind |
| | 0.7 | Model captures some structure |
| | 0.8+ | Strong structural understanding |
| | 0.9+ | Excellent performance |
| **Hits@10** | 0.3 | 30% of true edges in top-10 |
| | 0.5+ | Good ranking quality |

**Example output:**
```
Best epoch: 145
Val AUC:    0.83
Test AUC:   0.81
Hits@10:    0.47

✅ Model shows structural understanding (AUC > 0.7)
```

### **Validation Scores**

| Score | Range | Meaning |
|-------|-------|---------|
| **Formal Consistency** | boolean | Pass/fail - no exceptions |
| **Theory Proximity** | 0.0-1.0 | 0.95+ likely redundant |
| | | 0.5-0.8 good bridge |
| | | < 0.3 very distant |
| **Energy Intuition** | 0.0-1.0 | 0.8+ strong enhancement |
| | | 0.5-0.7 moderate value |
| | | < 0.4 weak justification |

**Decision flowchart:**
```
formal_consistency = false? → REJECT
integration_level = TRIVIAL? → REJECT
integration_level = DEEP AND intuition > 0.75? → PROMOTE
integration_level = USEFUL AND intuition > 0.6? → PENDING (human review)
else → REJECT
```

---

## 🔧 **Setup & Installation**

### **1. Install Neo4j Schema**

```bash
cat tools/gnn_suggestion_schema.cypher | cypher-shell -u neo4j -p <password>
```

### **2. Install Python Dependencies**

```bash
pip install torch torch-geometric torch-scatter torch-sparse
pip install scikit-learn numpy cohere neo4j qdrant-client
```

### **3. Verify Environment**

```bash
# Check PyTorch Geometric
python -c "import torch_geometric; print(torch_geometric.__version__)"

# Check Neo4j connection
python -c "from neo4j import GraphDatabase; print('Neo4j driver OK')"

# Check Cohere
python -c "import cohere; print('Cohere OK')"
```

---

## 📁 **File Structure**

```
tools/
  gnn_export.py              # Export EFC core from Neo4j
  gnn_train.py               # Train GNN on link prediction
  gnn_inference.py           # Generate suggestions
  gnn_theory_validator.py    # 4-step validation
  gnn_suggestion_schema.cypher  # Neo4j schema

symbiose_gnn_output/
  efc_core_graph.pt          # Exported graph data
  efc_gnn_best.pt            # Trained model checkpoint
  gnn_bridge.json            # Chunk UUID → GNN index mapping (from orchestrator)
  node_mapping.json          # Original GNN mapping (10k nodes)
```

---

## 🎓 **Example: Complete Run**

```bash
# 1. Export EFC core structure
python tools/gnn_export.py

# Expected output:
# 🔍 Extracting EFC core nodes from Neo4j...
#    ✅ Extracted 247 core nodes
# 🔗 Extracting EFC core edges from Neo4j...
#    ✅ Extracted 431 core edges
# 🧠 Generating text embeddings for nodes...
#    ✅ Generated 247 embeddings
# ✅ GNN graph exported to: symbiose_gnn_output/efc_core_graph.pt

# 2. Train GNN
python tools/gnn_train.py --epochs 200

# Expected output:
# Epoch 190 | Loss: 0.1423 | Val AUC: 0.8251 | Hits@10: 0.4632
# ...
# Best epoch: 175
# Test AUC:   0.8103
# ✅ Model shows structural understanding

# 3. Generate suggestions
python tools/gnn_inference.py --top-k 50 --min-confidence 0.75

# Expected output:
# 🎯 Top 10 Suggestions:
# 1. [0.912] Entropy Gradient
#     --[SUPPORTS]--> Adaptive Energy-Flow Window
# 2. [0.887] Information Emergence
#     --[DERIVES_FROM]--> Energy-Flow Stability
# ...
# ✅ 50 suggestions saved to Neo4j

# 4. Validate suggestions
python tools/gnn_theory_validator.py --batch --min-confidence 0.85

# Expected output:
# 🔬 Validating GNN Suggestion: sugg_001
# 🔬 Step 1: Formal Consistency Check
#    ✅ Formally consistent
# 🔍 Step 2: Theory Proximity Check
#    📊 Proximity score: 0.73
# 💡 Step 3: Energy/Entropy Intuition Check
#    💡 Intuition score: 0.89
# 🎯 Step 4: Integration Level Classification
#    🏷️  Integration Level: DEEP
# 🎯 Decision: PROMOTED

# 5. Review in Neo4j
cypher-shell -u neo4j -p <password>
> MATCH (s:GNNSuggestion {status: "PENDING"})
  OPTIONAL MATCH (s)-[:HAS_VALIDATION]->(v)
  WHERE v.decision = "PROMOTED"
  RETURN s.source_name, s.target_name, s.confidence, v.integration_level;

# 6. Promote accepted suggestions
> MATCH (s:GNNSuggestion {id: "sugg_001"})
  MATCH (src:Concept {id: s.source_concept_id})
  MATCH (tgt:Concept {id: s.target_concept_id})
  CREATE (src)-[:SUPPORTS {
    weight: s.confidence,
    source: "gnn_suggestion",
    promoted_by: "morpheus"
  }]->(tgt)
  SET s.status = "PROMOTED";
```

---

## 🚨 **Important Notes**

### **What GNN Can Do**
✅ Discover implicit structural patterns  
✅ Suggest clarifying connections  
✅ Bridge distant concept clusters  
✅ Rank suggestions by confidence  
✅ Learn from theory evolution over time  

### **What GNN Cannot Do**
❌ Prove mathematical theorems  
❌ Replace physical intuition  
❌ Validate against unpublished work  
❌ Understand causality  
❌ Make final decisions (requires human)  

### **Validation Philosophy**
- **Formal consistency**: Zero tolerance - math must work
- **Theory proximity**: Context - is this novel or redundant?
- **Energy intuition**: Core EFC - does it enhance Ef/∇S understanding?
- **Integration level**: Value - does this actually help?

---

## 📚 **References**

**Energy-Flow Cosmology:**
- See `docs/ENERGY_FLOW_COSMOLOGY.md`
- Figshare: [EFC Formal Specification](...)

**GNN Architecture:**
- Graph Attention Networks (Veličković et al., 2018)
- PyTorch Geometric Documentation

**Link Prediction:**
- "Link Prediction in Knowledge Graphs" (surveys)
- Negative sampling strategies

---

## 🤝 **Contributing**

When adding new EFC concepts to Neo4j:

1. **Always** set:
   - `domain` (cosmology/thermo/meta/cognition/ai)
   - `layer` (formal/applied/meta/cognitive)
   - `efc_core` (true for foundational concepts)

2. **Label** theory-level relations explicitly:
   - Use SUPPORTS for reinforcement
   - Use CONSTRAINS for boundaries
   - Use PART_OF for hierarchy

3. **Re-export** and **retrain** after major graph changes:
   ```bash
   python tools/gnn_export.py
   python tools/gnn_train.py --epochs 200
   ```

---

## 📞 **Support**

For questions about:
- **GNN training**: Check `tools/gnn_train.py` docstrings
- **Validation logic**: See `tools/gnn_theory_validator.py` Step 1-4 functions
- **Neo4j schema**: Read `tools/gnn_suggestion_schema.cypher` comments
- **EFC theory**: Consult primary EFC documentation

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Status**: Production-ready with existing data, awaiting EFC core concept population
