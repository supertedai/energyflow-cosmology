# 🔭 Energy-Flow Cosmology (EFC)

**DOI (Codebase)** · **DOI (Data & Validation)** · **ORCID**  
**License: CC BY 4.0**

Energy-Flow Cosmology (EFC) is a thermodynamic framework describing cosmic
structure, dynamics, and cognition through energy flow and entropy.  
This repository functions as a self-updating scientific system that integrates
semantic data, automated validation, open documentation, and reproducible workflows.

---

## 📘 Overview

EFC combines:

- Thermodynamic first principles (energy, entropy, gradients)
- A computational cosmology model (EFC-S, EFC-D, GHF, IMX)
- Automated pipelines for validation and data synchronization
- A machine-readable semantic API
- Full open-science provenance linking GitHub ↔ Figshare ↔ ORCID ↔ Website

The goal is a transparent, reproducible, reflective scientific process.

---

## 🧩 System Architecture

The repository operates as a semantic graph with five node types:

| Node | Purpose | Location |
|------|---------|----------|
| **AuthNode** | Authorship, ORCID, provenance | `/schema/site-graph.json` |
| **ConceptNode** | Core scientific definitions (Ef, ∇S, GHF, IMX) | `/schema/concepts.json` |
| **MethodologyNode** | Reflective reasoning and open-science workflow | `/methodology/` |
| **EmpiricalNode** | Validation datasets and plots | `/output/` |
| **IntegrationNode** | CI/CD pipelines, Figshare sync, API build | `.github/workflows/` |

---

## ⚙️ Automated Workflows

EFC includes a full CI/CD chain covering schema integrity, API regeneration,
validation, metadata integration, Figshare export, and repository consistency.

### 🔧 Core Workflows (Live Status)

| Workflow | File | Purpose | Status |
|---------|------|----------|--------|
| **Update EFC System** | `.github/workflows/update_efc_system.yml` | Full CI pipeline: Fetch → Merge → API rebuild → Sync | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update_efc_system.yml/badge.svg?branch=main) |
| **Update Schema** | `.github/workflows/update-schema.yml` | Validates and refreshes schema files | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg?branch=main) |
| **Validate Schema (Independent)** | `.github/workflows/validate-schema.yml` | Checks schema JSON-LD correctness | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/validate-schema.yml/badge.svg?branch=main) |
| **Update Concepts** | `.github/workflows/update-concepts.yml` | Rebuilds concepts from Figshare/GitHub | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-concepts.yml/badge.svg?branch=main) |
| **Update API** | `.github/workflows/update-api.yml` | Regenerates the semantic API in `/api/` | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-api.yml/badge.svg?branch=main) |
| **Run Validation** | `.github/workflows/run-validation.yml` | SPARC/JWST validation + baseline run | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml/badge.svg?branch=main) |
| **Export to Figshare** | `.github/workflows/export_figshare.yml` | Uploads validation outputs to Figshare DOIs | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/export_figshare.yml/badge.svg?branch=main) |
| **Fetch Figshare Metadata** | `.github/workflows/fetch-figshare.yml` | Retrieves and syncs DOI metadata | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/fetch-figshare.yml/badge.svg?branch=main) |
| **Build EFC Plugin** | `.github/workflows/build-efc-plugin.yml` | Builds and tests the EFC plugin package | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/build-efc-plugin.yml/badge.svg?branch=main) |
| **Build Dashboard** | `.github/workflows/build-dashboard.yml` | Rebuilds dashboard assets in `/output/` | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/build-dashboard.yml/badge.svg?branch=main) |
| **Build Formal Spec (LaTeX)** | `.github/workflows/build_efc_pdf.yml` | Builds `theory/formal/efc_formal_spec.pdf` | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/build_efc_pdf.yml/badge.svg?branch=main) |
| **Update README Date** | `.github/workflows/update-readme-date.yml` | Auto-updates “Last updated” field | ![](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-readme-date.yml/badge.svg?branch=main) |

---

## 🔬 Computational Core (`/src/`)

| Module | Purpose |
|--------|---------|
| **efc_core.py** | EFCModel, state computation, flow dynamics |
| **efc_entropy.py** | EFC-S: entropy field S(r) and ∇S |
| **efc_potential.py** | Energy-flow potential (Ef), field evolution |
| **efc_validation.py** | Validation utilities for SPARC/JWST |
| **sparc_io.py** | SPARC rotation curve loader |
| **jwst_io.py** | JWST observational data parsing |

---

## 📊 Validation Pipelines

### **SPARC (Rotation Curves)**
- Parser: `parse_sparc_table1.py`
- Validation: `run_sparc_validation.py`
- Outputs → `/output/validation/`

### **Baseline EFC Model**
- Script: `run_efc_baseline.py`
- Produces:
  - `rotation_curve.json`
  - `run_metadata.json` (includes Git commit hash)

### **JWST Validation**
- Script: `validate_efc.py --dataset jwst`
- Compares EFC predictions to high-redshift observations

---

## 🧠 Reflective Layer (Symbiosis)

EFC includes a meta-scientific reflection loop:

| Stage | Purpose | Component |
|-------|---------|-----------|
| **Fetch** | Retrieve DOI metadata | `fetch_figshare.py` |
| **Merge** | Integrate with schema | `update_concepts.py` |
| **API** | Rebuild machine-readable API | `update_efc_api.py` |
| **Publish** | Export and sync | GitHub Actions |
| **Reflect** | Human–AI evaluation | `/methodology/` |
| **Refine** | Update theory + schema | `/schema/` |

This loop drives continuous improvement and reproducibility.

---

energyflow-cosmology/
│
├── .github/          # CI/CD workflows
├── api/              # Regenerated semantic API
├── data/             # Raw + processed datasets
├── docs/             # Manuscripts and references
├── figshare/         # DOI-linked metadata
├── methodology/      # Open-science + epistemology
├── output/           # Validation results and plots
├── schema/           # Semantic definitions (Auth, Concept, Methodology)
├── scripts/          # Automation + validation scripts
└── src/              # Computational EFC core

---

## 📄 License

**Creative Commons Attribution 4.0 (CC BY 4.0)**  
Free to share, remix, and build upon with attribution.

© 2025 — **Morten Magnusson**, Energy-Flow Cosmology Initiative

---

## 📅 Last updated
2025-11-14
