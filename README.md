Perfekt — du har allerede et imponerende README-grunnlag.
Her er en **oppdatert versjon** som reflekterer alt vi har gjort de siste dagene:
– koblingen mellom **to DOI-er (kode + data)**,
– **automatiserte workflows** (Fetch → Merge → API → Upload),
– og full integrasjon av **Open Science-loop + EFC API**.

---

````markdown
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

**Energy-Flow Cosmology (EFC)** er et termodynamisk rammeverk som kobler  
kosmisk struktur, dynamikk og kognisjon gjennom energiflyt og entropi.  
Prosjektet kombinerer *open-science-metoder*, *semantisk strukturering*  
og *refleksivt samarbeid mellom menneske og AI.*

---

## 🔹 System Architecture

EFC-repoet fungerer som en **selvoppdaterende semantisk graf** som integrerer  
GitHub ↔ Figshare ↔ ORCID ↔ Energyflow-Cosmology.com.

| Node | Formål | Plassering |
|------|---------|------------|
| **AuthNode (Who)** | Forfatterskap og provenance | `/schema/site-graph.json` |
| **ConceptNode (What)** | Vitenskapelig kjerne – energi, entropi, struktur | `/schema/concepts.json` |
| **MethodologyNode (How)** | Refleksiv, åpen vitenskap og AI-resonnering | `/methodology/` |
| **EmpiricalNode (Evidence)** | Valideringsdata og figurer | `/output/` |
| **IntegrationNode** | Automatisk synk mot Figshare og nett-API | `.github/workflows/update_efc_system.yml` |

---

## 🔹 Automated Workflows

| Workflow | Formål | Frekvens |
|-----------|---------|-----------|
| **Fetch Figshare Concepts** | Henter siste DOI-metadata fra Figshare | ved behov |
| **Update Concepts from Figshare** | Fletter Figshare-data med lokale schemaer | etter fetch |
| **Update EFC API** | Regenererer semantisk API for nettsiden | daglig |
| **Export EFC Outputs to Figshare** | Laster opp nye resultater til DOI 30478916 | automatisk |
| **Update EFC System** | Komplett kjede (Fetch → Merge → API) | daglig kl 02:00 UTC |

---

## 🔹 Open-Science Principles

1. **Transparens** – alle modeller og data er offentlige  
2. **Reproduserbarhet** – schema og koder er versjonsstyrt  
3. **Interoperabilitet** – ORCID + Figshare + GitHub + WordPress  
4. **Refleksivitet** – AI-assistert metakognitiv prosess er del av selve metoden  

---

## 🔹 DOI-Network Map

```text
Morten Magnusson (ORCID 0009-0002-4860-5095)
   ├── Figshare Codebase DOI (30604004)
   │      └── isSupplementTo → Validation Dataset (30478916)
   └── Figshare Dataset DOI (30478916)
          └── isBasedOn → GitHub Repository (30604004)
````

---

## 🔹 Repository Layout

```
energyflow-cosmology/
│
├── .github/          # GitHub-workflows, actions og automasjon
├── api/              # Semantiske API-definisjoner og endepunkter
├── data/             # Rå og behandlede datasett
├── docs/             # Manuskripter og referanser
├── figshare/         # DOI-koblinger og metadatafiler
├── methodology/      # Open-science prosess-dokumentasjon
├── output/           # Valideringsgrafer og dashboards
├── schema/           # Semantiske definisjoner (Auth, Concept, Methodology)
├── scripts/          # Python-verktøy for automasjon
└── src/              # Kildekode og eksperimentelle moduler
```

---

## 🔹 License

All files are released under
**[Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/)**

---
---

## 🧠 EFC Reflective Loop

The **EFC Reflective Loop** describes the self-reinforcing cycle connecting human reasoning, AI synthesis, and open-data publication.


*Last updated: 2025-11-12*


### 🔹 Process Breakdown
| Stage | Function | System Layer |
|--------|-----------|---------------|
| **Fetch** | Retrieves new concepts, datasets, and metadata from Figshare | `fetch_figshare.py` |
| **Merge** | Integrates external updates with local semantic structures | `update_concepts.py` |
| **API** | Rebuilds the machine-readable semantic endpoint for EFC | `update_efc_api.py` |
| **Publish** | Exports validation data, schema updates, and graphs to Figshare and website | GitHub Actions / Figshare API |
| **Reflect** | Human–AI evaluation of reasoning accuracy, coherence, and novelty | Methodology layer (`/methodology/`) |
| **Refine** | Adjusts definitions, models, and schema for the next iteration | `/schema/` and `/docs/` |

### 🔹 Purpose
This loop forms the **core of EFC’s meta-scientific design**:
- The system learns and reorganizes itself through reflection.
- Every iteration strengthens the connection between *data integrity*, *theoretical clarity*, and *semantic transparency*.
- Human and AI reasoning are treated as complementary nodes in the same thermodynamic-informational cycle.

---

_Last updated: 2025-11-12_


```

---


```
