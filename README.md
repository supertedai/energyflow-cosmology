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

### 🔧 Core Workflows

| Workflow | File | Purpose |
|---------|------|----------|
| **Update EFC System** | `.github/workflows/update_efc_system.yml` | Full pipeline: Fetch → Merge → API rebuild → Sync |
| **Schema Validation** | `.github/workflows/update-schema.yml` | Validates JSON-LD schema + regenerates metadata |
| **Validation Pipeline** | `.github/workflows/run-validation.yml` | Runs SPARC/JWST validation + baseline model |
| **Export to Figshare** | `.github/workflows/export_figshare.yml` | Uploads outputs to DOI-linked Figshare articles |
| **README Date Update** | `.github/workflows/update-readme-date.yml` | Auto-updates timestamp in README |
| **API Autogeneration** | `.github/workflows/generate_api.yml` | Rebuilds the semantic API in `/api/` |
| **Import Tests** | `.github/workflows/check-imports.yml` | Ensures clean imports for `/src` and `/scripts` |
| **File Mapping Consistency** | `.github/workflows/validate_project_map.yml` | Validates site-graph.json ↔ actual file structure |
| **Static Analysis** | `.github/workflows/static-analysis.yml` | Linting and structural checks |
| **Formal Spec Build (LaTeX)** | `.github/workflows/build_efc_pdf.yml` | Builds `efc_formal_spec.pdf` |
| **Dataset Sync** | `.github/workflows/sync_datasets.yml` | Ensures SPARC/JWST data availability |
| **Dashboard Auto-Update** | `.github/workflows/update_dashboard.yml` | Regenerates dashboard figures in `/output/` |

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

## 📚 Repository Layout

