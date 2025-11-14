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

flowchart TD

    %% === Theory Layer ===
    T1[theory/<br>EFC-S / EFC-D / EFC-C / IMX] 
    T2[theory/architecture.md<br>Model Architecture]

    T1 --> T2

    %% === Source Code Layer ===
    subgraph SRC[ src/efc/ ]
        C1[core/efc_core.py<br>EFCModel, EFCParameters]
        C2[potential/efc_potential.py<br>compute_energy_flow]
        C3[entropy/efc_entropy.py<br>entropy_field, entropy_gradient]
        C4[validation/efc_validation.py<br>rotation curves, SPARC tools]
    end

    T2 --> SRC

    %% === Scripts Layer ===
    subgraph SCRIPTS[ scripts/ ]
        S1[run_efc_baseline.py<br>Numerical baseline run]
        S2[validate_efc.py<br>JWST / DESI / SPARC validation]
        S3[check_imports.py<br>Module integrity checks]
        S4[update_efc_api.py<br>Generate api/v1/]
    end

    SRC --> S1
    SRC --> S2
    SRC --> S3
    SRC --> S4

    %% === Data / Validation Layer ===
    subgraph DATA[data/ + external datasets]
        D1[JWST catalog]
        D2[DESI / BAO data]
        D3[SPARC rotation curves]
    end

    D1 --> S2
    D2 --> S2
    D3 --> S2

    S2 --> OUT1[output/validation/<br>figures + metrics]
    S1 --> OUT2[output/baseline/]

    %% === Semantic Layer ===
    subgraph SEM[Semantic Layer]
        SC1[schema/concepts.json<br>Concept Graph]
        SC2[schema/site-graph.json<br>AuthNode]
        SC3[figshare/figshare-index.json]
        SC4[methodology/<br>Open Method & Symbiosis]
    end

    SC1 --> S4
    S4 --> API[api/v1/<br>JSON-LD Endpoints]

    %% === Open Science / External ===
    OUT1 --> FS[Figshare Upload<br>(GitHub Action)]
    OUT2 --> FS

    SC1 --> FS
    SC3 --> FS

    FS --> DOI[Figshare DOIs<br>CC-BY-4.0]

    %% === Reflection Layer ===
    API --> REF[reflection/<br>symbiosis + meta-analysis]

    T1 --> REF
    SC2 --> REF
    FS --> REF


---

## 📅 Last updated

**Automatically updated by update-readme-date.yml**

---
