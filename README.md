# Energy-Flow Cosmology (EFC)
[![DOI](https://img.shields.io/badge/DOI-10.6084/m9.figshare.30478916-blue)](https://doi.org/10.6084/m9.figshare.30478916)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--4860--5095-brightgreen)](https://orcid.org/0009-0002-4860-5095)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC--BY--4.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)
[![Workflow Status](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions)
[![Schema Workflow](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml)
[![Validation Workflow](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml)
[![Date Update](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-readme-date.yml/badge.svg)](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-readme-date.yml)


**Energy-Flow Cosmology (EFC)** is a unified thermodynamic framework that connects  
cosmic structure, dynamics, and cognition through energy flow and entropy.  
The project integrates open-science methods, machine-readable schema, and reflective human–AI collaboration.

---

## 🔹 Project Overview

| Layer | Focus | Format / Folder |
|-------|-------|-----------------|
| **Conceptual (What)** | Thermodynamic and structural models of the cosmos | [`/schema/concepts.json`](schema/concepts.json) |
| **Methodological (How)** | Reflective, open-science, and symbiotic reasoning process | [`/methodology/`](methodology/) |
| **Authorship (Who)** | Provenance and identity – [Morten Magnusson](https://orcid.org/0009-0002-4860-5095) | Integrated in [`/schema/site-graph.json`](schema/site-graph.json) |
| **Empirical / Output (Evidence)** | Validation plots, datasets, and dashboard visuals | [`/output/`](output/) |
| **Documentation (Public Interface)** | Published notes, manuscripts, and cross-references | [`/docs/`](docs/) |

---

## 🔹 Semantic Architecture

The repository functions as a **machine-readable knowledge graph** compliant with [Schema.org](https://schema.org) standards.

**Core nodes**
- **AuthNode (Who)** — authorship and provenance  
- **ConceptNode (What)** — scientific core: energy flow, entropy, structure  
- **MethodologyNode (How)** — reflective and open-science reasoning linking human and AI cognition  

All nodes are unified in [`/schema/site-graph.json`](schema/site-graph.json),  
which serves as the canonical graph root for search engines, LLMs, and metadata crawlers.

---

## 🔹 Open-Science Principles

1. **Transparency** — all concepts and reasoning are public.  
2. **Reproducibility** — definitions are semantically version-controlled.  
3. **Interoperability** — integrates ORCID, Figshare, GitHub, and WordPress schema.  
4. **Reflectivity** — includes cognitive and AI-assisted reasoning as part of the record.

---

## 🔹 Repository Layout

```
```text
energyflow-cosmology/
│
├── .github/          # GitHub workflows, actions, and automation scripts
├── api/              # API definitions and endpoints (semantic + external access)
├── data/             # Raw and processed datasets for validation
├── docs/             # Manuscripts, references, and scientific documentation
├── figshare/         # DOI-linked metadata and Figshare integration files
├── methodology/      # Reflective and open-science process documentation
├── output/           # Visual validation material and figures
├── schema/           # Semantic graph definitions (Auth, Concept, Methodology)
├── scripts/          # Python and automation utilities
└── src/              # Core source code and experimental modules
```
---

## 🔹 License

All files in this repository are released under  
**[Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)**

---

_Last updated: 2025-11-12_
