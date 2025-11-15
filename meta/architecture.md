# `project/architecture.md`

```md
# 🏗️ EFC Architecture  
Theory → Code → Data → Semantics

This document provides a concise overview of how the Energy-Flow Cosmology (EFC) system is structured.  
It describes how theory maps to Python code, how data flows through the model, and how semantics are maintained.

---

## 1. Theory Layer

EFC is defined by four core theoretical components:

- **EFC-S** — structure (halo model, energy field, entropy profile)  
- **EFC-D** — dynamics (energy-flow, expansion, potential)  
- **EFC-C** — cognition (resonance, model revision)  
- **IMX** — informational metastructure  

These live under:

```

/theory/
architecture.md
efc-s.md
efc-d.md
efc-c.md
imx.md

```

The theory layer defines the foundational equations and parameters.  
All model behaviour in `src/efc/` is derived directly from this layer.

---

## 2. Source Code Layer (`src/efc/`)

Core implementation of the physical model:

```

src/efc/
│
├── efc_core.py        → main model (energy-flow, expansion rate, core relations)
├── efc_potential.py   → Φ(Ef, S) and related potential functions
├── efc_entropy.py     → entropy field and gradient
├── efc_validation.py  → model utilities for astrophysical datasets
└── **init**.py        → public API surface

```

### Main responsibilities

- compute energy-flow potential  
- compute entropy gradients  
- estimate expansion rate  
- provide a stable API for validation and dashboard layers  
- ensure consistent behaviour across workflows

---

## 3. Script Layer (`scripts/`)

Utility and automation scripts:

```

scripts/
│
├── run_efc_baseline.py   → baseline model runs
├── validate_efc.py       → JWST / DESI / SPARC validation
├── check_imports.py      → import test gate
└── update_efc_api.py     → generate api/v1/ JSON-LD endpoints

```

### Role of the script layer

- bridge between model and datasets  
- run reproducible pipelines  
- validate implementation integrity  
- regenerate API outputs, dashboard assets and semantic data  

---

## 4. Data Layer (`data/` + external datasets)

Datasets used for numerical validation:

```

data/
│
├── jwst/     → early galaxy catalogs
├── desi/     → BAO + H(z)
└── sparc/    → rotation curves

```

These are consumed by `validate_efc.py`, which:

- imports `src/efc/*`  
- computes EFC predictions  
- produces plots and metrics under `output/`

---

## 5. Output Layer (`output/`)

The model writes reproducible outputs:

```

output/
│
├── validation/   → JWST / DESI / SPARC results
└── baseline/     → standard model runs

```

These outputs are:

- used by the dashboard  
- exported to Figshare  
- versioned by GitHub workflows  
- linked to DOIs for provenance

---

## 6. Semantic Layer (`schema/` + `figshare/` + `methodology/`)

EFC has a semantic layer used by search engines, AI systems and dashboards.

```

schema/
concepts.json        → concept graph
site-graph.json      → AuthNode + site structure
methodology-index.json

figshare/
figshare-index.json
figshare-links.json

methodology/
open-method.md
author-method-note.md
open-process.json

```

Purpose:

- unify concepts, definitions and provenance  
- maintain consistency across GitHub, Figshare, ORCID and the website  
- generate stable JSON-LD used by `/api/v1/`  
- feed external crawlers and LLMs with structured data  

---

## 7. API Layer (`api/v1/`)

Generated automatically by `update_efc_api.py`.

```

api/v1/
│
├── index.json           → list of all terms
└── <term>.json          → JSON-LD for each concept

````

Used by:

- energyflow-cosmology.com  
- dashboard visualisations  
- external tools and validation pipelines  
- semantic crawlers and AI systems

---

## 8. Reflection Layer (`reflection/`)

The system writes introspective data about:

- semantic consistency  
- workflow status  
- resonance across concepts  
- cross-links between theory, data and outputs  

Used to monitor stability and coherence of the EFC knowledge graph.

---

## 9. End-to-End Architecture Diagram

```mermaid
flowchart TD

%% Theory
T1[theory/EFC-S / EFC-D / EFC-C / IMX]
T2[theory/architecture.md]
T1 --> T2

%% Source Code
subgraph SRC[src/efc/]
    C1[efc_core.py]
    C2[efc_potential.py]
    C3[efc_entropy.py]
    C4[efc_validation.py]
end
T2 --> SRC

%% Scripts
subgraph SCRIPTS[scripts/]
    S1[run_efc_baseline.py]
    S2[validate_efc.py]
    S3[check_imports.py]
    S4[update_efc_api.py]
end
SRC --> S1
SRC --> S2
SRC --> S3
SRC --> S4

%% Data
subgraph DATA[data/ + external]
    D1[JWST]
    D2[DESI]
    D3[SPARC]
end
DATA --> S2

S2 --> OUT1[output/validation]
S1 --> OUT2[output/baseline]

%% Semantics
subgraph SEM[Semantic Layer]
    SC1[schema/concepts.json]
    SC2[schema/site-graph.json]
    SC3[figshare-index.json]
    SC4[methodology/]
end
SC1 --> S4
S4 --> API[api/v1]

%% Open Science
OUT1 --> FS[Export to Figshare]
OUT2 --> FS
SC1 --> FS
SC3 --> FS
FS --> DOI[Figshare DOIs]

%% Reflection
API --> REF[reflection/]
T1 --> REF
SC2 --> REF
FS --> REF
````

---

**This file describes how the full EFC system is structured—
from theory → implementation → validation → semantics → public API.**

```

---

```
