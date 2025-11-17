# **Energy-Flow Cosmology — Architecture v2**

**Version:** 2.0
**Status:** Validated against current repository structure
**Date:** 2025-11-17

This document describes the complete architecture of the Energy-Flow Cosmology (EFC) repository.
It defines all layers: theory, code, data, validation, methodology, meta-reflection, API, and publication.

The system is organized into **six structural layers**.

---

# **1. Theory Layer (Core Physics)**

**Directories:**

* `theory/`
* `theory/formal/`
* `docs/efc_master.*`
* `docs/sections/`
* `src/efc/core/`
* `src/efc/entropy/`
* `src/efc/potential/`
* `src/efc/validation/`

**Contents:**

* Formal mathematical definitions (EFC-S, EFC-D, EFC-C₀)
* Notation, parameters, structure models
* Master specification (HTML / TeX / PDF)
* Field diagrams, entropy profiles, rotation curves
* Python model implementation (Ef, S, density, gradients)

**Function:**
This is the scientific core of EFC.
No meta, symbiosis, cognition, or methodology files appear here.

---

# **2. Data & Validation Layer**

**Directories:**

* `data/raw/`
* `data/external/`
* `data/processed/`
* `data/sparc/`
* `output/validation/`
* `notebooks/`

**Contents:**

* Raw observational data (SPARC, NGC)
* Parsed and processed datasets
* Validation plots, JSON outputs
* Notebooks comparing EFC vs ΛCDM

**Function:**
Ground-truth testing and empirical calibration of the EFC framework.

---

# **3. API & Semantic Layer**

**Directories:**

* `api/`
* `api/v1/`
* `schema/`
* `schema/*.json|jsonld`

**Contents:**

* `ConceptNode` definitions
* `MethodologyNode`
* `MetaNode`
* Index files, metadata, mapping
* Schema for website, Figshare, and search engines

**Function:**
Machine-readable interface to the entire EFC system.
Defines how EFC is indexed, queried, and integrated externally.

---

# **4. Methodology Layer (Scientific Method)**

**Directories:**

* `methodology/`

**Contents:**

* Epistemology
* Author method note
* Open-method and open-process
* Reproducibility guidelines

**Function:**
Defines how research is performed: transparency, reflection, reproducibility.

---

# **5. Meta Layer (Cognition, Reflection, Symbiosis)**

**Directories:**

* `meta/cognition/`
* `meta/reflection/`
* `meta/symbiosis/`
* `meta/meta-process/`
* `meta/resources/`
* `meta/personal/`
* `meta/architecture.*`
* `meta/topology-of-insight.md`
* `meta/metascope.md`

**Contents:**

* Cognitive field, entropy-clarity, transient representations
* Reflection schema, state-map, resonance-links
* Symbiosis protocols, system coherence, vector alignment
* Internal process documentation
* Meta-architecture and system-level perspective

**Function:**
Describes the reflective, cognitive and symbiotic layers behind EFC development.
This is not part of the physics model — it documents the *thinking system* and *process*.

---

# **6. Publication & Integration Layer**

**Directories:**

* `figshare/`
* `schema/`
* `app/dashboard/`
* `integrations/wp/`
* `sitemap.xml`, `sitemap-links.json`

**Contents:**

* Figshare index and links
* Website schema, docs-index, site-graph
* Dashboard UI (HTML/JS/CSS)
* WordPress loader plugin

**Function:**
External publishing, search-engine semantics, and user-facing interfaces.

---

# **7. Toolbox & Execution Layer**

**Directories:**

* `scripts/`
* `output/`
* `lib/`
* `notebooks/`

**Contents:**

* Data parsers, SPARC fetchers
* Plot generators, model runners
* API builders, schema updaters
* Integration utilities

**Function:**
Execution logic for the full system: simulation, validation, automation, schema updating.

---

# **Structural Summary**

```
1. Theory         → physics, models, formalism
2. Data           → raw data, processing, validation
3. API/Semantic   → machine-readable knowledge graph
4. Methodology    → scientific method and epistemology
5. Meta           → cognition, reflection, symbiosis
6. Publication    → external interfaces, dashboard, schema
7. Toolbox        → scripts and utilities
```

Each layer is fully separated and consistent.
There is no leakage between meta-reflection and physics.
The architecture is stable, clean, and logically coherent.
