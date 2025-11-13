# **CHANGELOG.md — Energy-Flow Cosmology (EFC)**

*Chronological record of all major updates, features, fixes, and structural changes.*

---

# **📦 v1.3.0 — Core Stabilization & Validation Suite**

**Date:** 2025-11-13
**Author:** Morten Magnusson

### **Overview**

This version stabilizes the entire computational core of EFC, introduces a validated SPARC pipeline, resolves all Git merge conflicts, synchronizes the development environments across macOS ↔ Codespaces ↔ GitHub, and fixes multiple GitHub Actions workflows.
It is the first complete “computationally consistent” release of EFC.

---

## **✨ Added**

### **SPARC validation pipeline**

* `scripts/parse_sparc_table1.py`
* `scripts/run_sparc_validation.py`
* Added processed SPARC datasets (`sparc_table1.csv`, `sparc_table1.json`)

### **Baseline EFC run**

* Implemented `run_efc_baseline.py`
* Generates:

  * `output/validation/rotation_curve.json`
  * `output/run_metadata.json`

---

## **🛠️ Fixed**

### **EFC computational core**

* Cleaned and unified:

  * `compute_energy_flow`
  * `energy_flow_rate`
  * `entropy_gradient`
* Removed deprecated: `efc_potential`
* Repaired vector norms, gradient directions, radial masks
* Eliminated all merge markers across modules

### **Parameter handling**

* Corrected `parameters.json` schema (removed invalid keys)
* Ensured deterministic behavior via `seed`

---

## **🔧 Git / Repository**

* Resolved a complex divergent-history event
* Fixed multiple interactive rebase states
* Recovered from VS Code editor socket failure
* Hard-synced Codespaces ↔ GitHub
* Fully reset macOS checkout to `origin/main`
* Cleaned all conflicts in:

  * `efc_entropy.py`
  * `efc_core.py`
  * `sparc_io.py`
  * `efc_validation.py`
  * `efc_potential.py`
  * `__init__.py`
  * `run_efc_baseline.py`

---

## **⚙️ GitHub Actions**

### Figshare export workflow fixed

* Repaired YAML structure
* Repaired embedded Python block
* Corrected secret names
* Added runtime safety checks for missing secrets
* Verified workflow execution
* Ensured no CI failures except when secrets intentionally absent

---

## **🌐 Sync & Environments**

* Codespaces, GitHub, and macOS now in perfect sync
* Clean, conflict-free, rebase-validated state

---

# **📦 v1.2.0 — Full Semantic Framework Integration**

**Date:** 2025-11-10

### **Overview**

EFC now includes a full cross-platform semantic infrastructure linking GitHub ↔ WordPress ↔ Figshare ↔ ORCID using JSON-LD.

---

## **✨ Added**

### **Semantic schema system**

* `schema/concepts.json` — master concept graph
* `schema/docs-index.json` — unified Figshare DOI index
* Introduced:

  * EFC-S
  * EFC-D
  * Grid–Higgs Framework (GHF)
  * Halo Model of Entropy (HME)
  * Informational Metastructure Extension (IMX)

### **WordPress JSON-LD Loader**

Child-theme PHP hook:

* Loads JSON-LD directly from GitHub raw
* Ensures all site pages always use latest schema
* Validated via Google Rich Results + Schema.org tools

---

## **🔧 Automation**

* `.github/workflows/update-schema.yml`
* Nightly + on-commit validation
* Auto-commit schema changes when needed
* Validates:

  * `schema/*.json`
  * `site-graph.json`
  * `sitemap.xml`

---

## **📚 Documentation**

* Updated project README
* Added cross-domain linkage overview
* Validated all DOIs and `sameAs` references

---

# **📦 v1.1.0 — Semantic Integration & GitHub–WordPress Bridge**

**Date:** 2025-11-09

### **✨ Added**

* First working schema loader in WordPress
* Base semantic graph (`site-graph.json`)
* Verified full sync between:

  * GitHub
  * WordPress site
  * Figshare DOIs
* Ensured schema visible to search engines + AI models

---

# **📦 v1.0.0 — Initial Repository Setup**

**Date:** 2025-11-01

### **✨ Added**

* Base repo structure:

  ```
  /schema
  /docs
  /data
  /website
  /scripts
  ```
* Initial Figshare-linked documents
* Creative Commons license
* Project metadata, initial index files

---

# **📌 Upcoming: v1.4 — Knowledge Graph API**

### Planned:

* Neo4j export schema
* `/graph/` folder for ontology layers
* API auto-generation for concept+evidence nodes
* LLM resonance logs (`feedback.json`)
* WordPress dashboard for live semantic health

---

# **📄 License**

Distributed under **CC-BY-4.0**
© 2025 — *Morten Magnusson* — Energy-Flow Cosmology Initiative

---
