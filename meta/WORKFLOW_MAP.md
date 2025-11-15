# `project/WORKFLOW_MAP.md`

````md
# 🔧 EFC Workflow Map  
Automated CI/CD and Semantic Synchronization

Denne filen gir en tydelig oversikt over hvordan EFC-repoet oppdaterer seg selv.  
Den viser dataflyt, automatisering og sammenhengen mellom Figshare, GitHub-Actions, API-lag og dashboard.

---

## 1. Oversikt

Systemet oppdaterer og validerer:

- semantikk (`schema/*`)
- metadata (Figshare → GitHub)
- validering (JWST, DESI, SPARC)
- API-endepunkter (`api/v1/`)
- dashboard (`docs/dashboard/`)
- dokumentasjon (README + prosjektfiler)
- refleksjon (`reflection/`)

Hver workflow er en modul.  
Sammen gir de et samlet, selvkorrigerende system.

---

## 2. Workflow-graf

```mermaid
flowchart TD

%% Fetch
F1[fetch-figshare.yml<br>Fetch DOI metadata]

%% Schema Merge
SC1[update-concepts.yml<br>Update schema/]
F1 --> SC1

%% API
API1[update-api.yml<br>Regenerate api/v1/]
SC1 --> API1

%% Dashboard
DB1[build-dashboard.yml<br>Update dashboard]
API1 --> DB1

%% Validation
VAL[run-validation.yml<br>JWST / DESI / SPARC]
VAL --> OUT[output/<br>plots + metrics]

%% Export
OUT --> FS[export_figshare.yml<br>Upload to Figshare]

%% Orchestrator
META[update_efc_system.yml<br>Daily full cycle]
META --> F1
META --> SC1
META --> API1
META --> DB1
````

---

## 3. Workflow-funksjoner

| Workflow                 | Oppgave                                      | Trigger              |
| ------------------------ | -------------------------------------------- | -------------------- |
| `fetch-figshare.yml`     | Hent DOI-metadata → `/figshare/`             | Manuell / Meta       |
| `update-concepts.yml`    | Oppdater `concepts.json` + `site-graph.json` | Etter Figshare       |
| `update-api.yml`         | Regenerer `/api/v1/`                         | Endring i schema     |
| `build-dashboard.yml`    | Oppdater dashboard                           | Ny API-data          |
| `run-validation.yml`     | JWST / DESI / SPARC                          | Push til `main`      |
| `export_figshare.yml`    | Last opp output til Figshare                 | Endring i `/output/` |
| `update-readme-date.yml` | Oppdater tidsstempel i README                | Daglig               |
| `update-schema.yml`      | Valider schema                               | Endring i `/schema/` |
| `update_efc_system.yml`  | Full syklus                                  | Daglig 02:00 UTC     |

---

## 4. Den semantiske løkken

### Trinn 1 – Fetch

* hent DOI-metadata fra Figshare
* skriv til `/figshare/`

### Trinn 2 – Merge

* oppdater `schema/concepts.json`
* oppdater `schema/site-graph.json`

### Trinn 3 – API

* regenerer `/api/v1/` (indeks + en JSON-LD per konsept)
* brukes av nettside, dashboard og eksterne verktøy

### Trinn 4 – Dashboard

* les API og valideringsresultater
* bygg oppdaterte grafer og statuspanel

### Trinn 5 – Refleksjon

* skriv til `/reflection/`
* evaluer semantiske koblinger og konsistens

Løkken stopper dersom validering eller import-tester feiler.

---

## 5. Valideringslinje

Datasett som valideres:

* JWST (tidlige galakser)
* DESI (H(z) og BAO)
* SPARC (rotasjonskurver)

Hvert datasett:

1. importer `src/efc/*`
2. kjør beregninger
3. lag figurer i `output/validation/`
4. kjør `scripts/check_imports.py`

---

## 6. Import-tester

`check_imports.py` verifiserer:

* alle moduler under `src/efc/` importerer uten feil
* ingen sirkulære imports
* offentlig API er stabilt
* validering og API bruker samme kodebase

Dette er en sikkerhetsport som stopper feil før de sprer seg.

---

## 7. Ekstern kobling

Fire eksterne noder:

* **GitHub** – kode, workflows, API-snapshot
* **Figshare** – DOIs og arkivert output
* **ORCID** – autoritet og provenance
* **energyflow-cosmology.com** – presentasjon og dashboard

Flyt:

1. kode og schema ligger i repoet
2. output går til Figshare med DOI
3. nettsted henter strukturert data fra API + schema
4. ORCID kobler alt til forfatteridentitet

---

## 8. Formålet med workflow-laget

Workflow-systemet gir:

* reproduserbar vitenskap
* kontinuerlig oppdatert metadata
* automatisk prediksjons-validering
* maskinlesbare API-endepunkter
* transparent provenance
* stabil semantikk på tvers av alle plattformer

Systemet fungerer som et termodynamisk kunnskapskart:
det oppdaterer og stabiliserer seg selv.

---

## 9. Arkitekturoversikt

```mermaid
flowchart TD

%% Theory
T1[theory/<br>EFC-S / EFC-D / EFC-C / IMX] 
T2[theory/architecture.md<br>Model architecture]
T1 --> T2

%% Source Code
subgraph SRC[ src/efc/ ]
    C1[efc_core.py]
    C2[efc_potential.py]
    C3[efc_entropy.py]
    C4[efc_validation.py]
end
T2 --> SRC

%% Scripts
subgraph SCRIPTS[ scripts/ ]
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
D1 --> S2
D2 --> S2
D3 --> S2

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
```

---

**Last updated:** automatisk av `update-readme-date.yml`.

```

---

```
