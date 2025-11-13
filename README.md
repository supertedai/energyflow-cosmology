# 🔭 Energy-Flow Cosmology (EFC)

[![DOI (Codebase)](https://img.shields.io/badge/DOI-10.6084/m9.figshare.30604004-blue)](https://doi.org/10.6084/m9.figshare.30604004)
[![DOI (Data & Validation)](https://img.shields.io/badge/DOI-10.6084/m9.figshare.30478916-blue)](https://doi.org/10.6084/m9.figshare.30478916)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4860--5095-brightgreen)](https://orcid.org/0009-0002-4860-5095)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC--BY--4.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

[![Workflow: Update EFC System](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update_efc_system.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update_efc_system.yml)
[![Workflow: Schema Validation](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml)
[![Workflow: Validation Plots](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml)

[![Workflow: README Date Update](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-readme-date.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-readme-date.yml)


---

# 📘 Overview

**Energy-Flow Cosmology (EFC)** is a thermodynamic framework describing cosmic structure, dynamics, and cognition through energy flow and entropy.

This repository acts as a **self-updating semantic and computational system**, integrating:

* GitHub
* Figshare
* ORCID
* Energyflow-Cosmology.com (WordPress)
* Automated validation pipelines
* A machine-readable semantic API

---

# 🧩 System Architecture

The repository functions as a **semantic graph**, organized into five node types:

| Node                | Purpose                                        | Location                  |
| ------------------- | ---------------------------------------------- | ------------------------- |
| **AuthNode**        | Authorship, ORCID, provenance                  | `/schema/site-graph.json` |
| **ConceptNode**     | Core scientific definitions: Ef, ∇S, GHF, IMX  | `/schema/concepts.json`   |
| **MethodologyNode** | Reflective reasoning and open-science workflow | `/methodology/`           |
| **EmpiricalNode**   | Validation datasets, rotation curves           | `/output/`                |
| **IntegrationNode** | Automation, Figshare sync, API build           | `.github/workflows/`      |

---

# ⚙️ Automated Workflows

EFC includes a full automation chain.

| Workflow                   | Purpose                                             |
| -------------------------- | --------------------------------------------------- |
| **update-schema.yml**      | Validates all schema files and regenerates metadata |
| **update_efc_system.yml**  | Full pipeline: Fetch → Merge → API rebuild          |
| **run-validation.yml**     | Runs EFC validation (SPARC, JWST, rotation curves)  |
| **export_figshare.yml**    | Exports validation outputs to Figshare DOIs         |
| **update-readme-date.yml** | Auto-updates the README timestamp                   |

---

# 🔬 Computational Core (`src/`)

| Module              | Function                                        |
| ------------------- | ----------------------------------------------- |
| `efc_core.py`       | EFCModel, parameter handling, state computation |
| `efc_entropy.py`    | EFC-S: entropy field S(r) and gradient ∇S       |
| `efc_potential.py`  | Energy-flow: Ef = ρ(1–S), dEf/dt                |
| `efc_validation.py` | General validation utilities                    |
| `sparc_io.py`       | SPARC rotation curve data loader                |

---

# 📊 Validation Pipelines

### **SPARC (Galaxy Rotation Curves)**

* Parser: `parse_sparc_table1.py`
* Validation: `run_sparc_validation.py`
* Output stored in `/output/validation/`

### **Baseline EFC Run**

* `run_efc_baseline.py`
* Generates:

  * `rotation_curve.json`
  * `run_metadata.json` (with Git commit hash)

---

# 🧠 Reflective Layer

EFC includes a built-in meta-scientific loop:

| Stage       | Purpose                            | Component            |
| ----------- | ---------------------------------- | -------------------- |
| **Fetch**   | Retrieves DOI metadata             | `fetch_figshare.py`  |
| **Merge**   | Combines metadata with schema      | `update_concepts.py` |
| **API**     | Rebuilds semantic API              | `update_efc_api.py`  |
| **Publish** | Outputs data to Figshare + Website | GitHub Actions       |
| **Reflect** | Human–AI evaluation                | `/methodology/`      |
| **Refine**  | Update models, definitions, schema | `/schema/`           |

This loop drives the evolution of EFC as a transparent, reproducible, and reflective scientific system.

---

# 📚 Repository Layout

```
energyflow-cosmology/
│
├── .github/          # Automation and workflows  
├── api/              # Machine-readable semantic API  
├── data/             # Raw + processed datasets  
├── docs/             # Manuscripts, references  
├── figshare/         # DOI-linked metadata  
├── methodology/      # Reflective open-science notes  
├── output/           # Validation results and plots  
├── schema/           # Semantic definitions (Auth, Concept, Methodology)  
├── scripts/          # Automation + validation scripts  
└── src/              # Computational EFC core  
```

---

# 📄 License

All content is released under
**Creative Commons Attribution 4.0 (CC-BY-4.0)**.

© 2025 — *Morten Magnusson*, Energy-Flow Cosmology Initiative

---

# 📅 Last updated

**2025-11-13**

---

