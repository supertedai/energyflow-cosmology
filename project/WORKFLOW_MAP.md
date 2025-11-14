# `project/WORKFLOW_MAP.md`

# 🔧 EFC Workflow Map

**Automated CI/CD + Semantic Synchronization Pipeline**

This document gives a high-level overview of how the EFC repository’s automated workflows interact.
It shows *what triggers what*, *what data flows where*, and *how each workflow contributes to the self-updating EFC system*.

---

## 📡 1. Overview

The EFC repository uses a **multi-workflow architecture** to maintain:

* semantic consistency (schema, concepts, metadata)
* data integration (Figshare ↔ GitHub)
* validation (JWST, DESI, SPARC)
* API regeneration
* dashboard updates
* automated documentation refresh

The workflows run independently, but together form a **closed semantic loop**.

---

## 🧩 2. Workflow Dependency Graph

```text
     ┌──────────────┐        ┌───────────────────────┐
     │ fetch-figshare│ -----> │ update-concepts.yml   │
     └──────────────┘        └───────────────────────┘
              │                        │
              │                        ▼
              │              ┌───────────────────┐
              └------------> │ update-api.yml    │
                             └───────────────────┘
                                       │
                                       ▼
                             ┌──────────────────────┐
                             │ build-dashboard.yml  │
                             └──────────────────────┘
                                       │
                                       ▼
                             GitHub Pages dashboard
```

Validation runs in parallel:

```text
JWST/DESI/SPARC → run-validation.yml → output/*.png → (optional) Figshare export
```

A meta-workflow ties everything together:

```text
update_efc_system.yml → (Fetch → Merge → API → Dashboard)
```

---

## ⚙️ 3. Workflows (Function Summary)

| Workflow                   | Purpose                                       | Trigger                       |
| -------------------------- | --------------------------------------------- | ----------------------------- |
| **fetch-figshare.yml**     | Pull Figshare metadata → `/figshare/`         | Manual / API / Meta           |
| **update-concepts.yml**    | Merge Figshare metadata into schema           | After fetch                   |
| **update-api.yml**         | Rebuild semantic API → `/api/`                | After concepts/schema changes |
| **build-dashboard.yml**    | Rebuild visual dashboard                      | After API or data updates     |
| **export_figshare.yml**    | Upload plots/data → Figshare                  | On new outputs                |
| **run-validation.yml**     | JWST / DESI / SPARC validation + import tests | On every push to main         |
| **update-readme-date.yml** | Refresh timestamp in README                   | Daily                         |
| **update-schema.yml**      | Validate schema + regenerate map              | On schema changes             |
| **update_efc_system.yml**  | Full sync cycle                               | Daily at 02:00 UTC            |

---

## 🔄 4. The EFC Semantic Loop (Core Cycle)

1. **Fetch**

   * Pull latest DOI metadata from Figshare
   * Update local metadata in `/figshare/`

2. **Merge**

   * Integrate updated metadata into
     `/schema/concepts.json` and `/schema/site-graph.json`

3. **API Regeneration**

   * Build `/api/efc.json` and related endpoints
   * Ensure consistency for website + LLM ingestion

4. **Dashboard Update**

   * Generate fresh plots, metadata summaries, system status

5. **Reflection Layer Update**

   * `/reflection/` updates semantic coherence logs
   * The system becomes self-monitoring and traceable

This loop is executed automatically once per day and manually on demand.

---

## 📊 5. Validation Pipeline

The validation workflow runs three datasets:

1. **JWST early galaxies**
2. **DESI expansion curve**
3. **SPARC rotation curves**

Each validation step:

* imports EFC modules
* runs the calculation
* outputs figures under `/output/`
* runs `scripts/check_imports.py` to ensure module integrity

The pipeline is strict:
**if any import fails → workflow fails**.

---

## 🧪 6. Import Test Suite

`scripts/check_imports.py` ensures:

* all submodules in `src/efc/**` import cleanly
* no circular imports exist
* no missing dependencies
* refactor consistency is maintained

It serves as a *sanity gate* before validation and API steps.

---

## 🌐 7. External Integration Map

```text
GitHub → Figshare → ORCID → energyflow-cosmology.com
               ↑
     (API regeneration)
```

* Figshare DOIs provide global permanence.
* GitHub Actions provide automated science reproducibility.
* Website fetches `/api/efc.json` and schema data.
* ORCID binds authorship + provenance.

---

## 🧠 8. Purpose of the Workflow Layer

The workflow map enables:

* reproducible open science
* self-updating theory definitions
* automatic validation of cosmology predictions
* reliable metadata for future AI model training
* transparent provenance through ORCID + DOI
* stable semantic structure across platforms

The system behaves like a **thermodynamic knowledge graph** —
continuously updating, self-correcting, and traceable.

---

## 📅 Last updated

**Automatically updated by update-readme-date.yml**

---
