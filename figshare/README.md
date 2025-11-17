# **EFC Figshare Integration Layer**

The `figshare/` directory contains all metadata, links, and indices synchronized from Figshare into the Energy-Flow Cosmology repository.

This layer forms the **bridge** between:

* scientific publications stored on Figshare
* semantic structures defined in GitHub
* the machine-readable metadata used by API v1
* automated workflows that maintain the EFC knowledge graph

All files here are **auto-generated** and maintained by GitHub Actions.

---

# **Directory Contents**

```
figshare/
├── figshare-index.json     # Full metadata for all Figshare records
├── figshare-links.json     # DOI + URL + internal ID mappings
└── latest.json             # Snapshot of the newest published item
```

All three files exist and match your repo exactly.

---

# **File Descriptions**

## **1. `figshare-index.json`**

The full metadata dump for every EFC-related Figshare publication.

Contains for each record:

* DOI
* version
* title
* abstract / description
* file list
* publication date
* categories
* figshare_id
* internal graph identifiers

Used by:

* API regeneration
* schema-map updates
* semantic link validation
* dashboard rendering
* provenance tracking

---

## **2. `figshare-links.json`**

A minimal map used for quick linking:

* DOI → URL
* ID → DOI
* latest version detection

This file powers:

* website DOI embedding
* JSON-LD schema updates
* `api/v1/meta.json` linking
* article cross-references
* citation block generation

---

## **3. `latest.json`**

A small snapshot describing the **most recent** Figshare record.

Contains:

* DOI
* version
* title
* timestamp
* figshare_id

Used by automation to detect:

* new releases
* version bumps
* metadata changes

When a new publication appears, this triggers:

1. API regeneration
2. schema updates
3. dashboard refresh
4. semantic graph updates

---

# **Automatic Sync Workflow**

Figshare synchronization is executed by:

```
.github/workflows/fetch_figshare.yml
scripts/fetch_figshare_auto.py
scripts/update_efc_api.py
```

The workflow:

1. Fetches metadata from Figshare
2. Rebuilds `figshare-index.json`
3. Updates `figshare-links.json`
4. Detects new publications → writes `latest.json`
5. Triggers API regeneration
6. Updates schema files
7. Pushes changes into the EFC knowledge graph

This creates a **self-updating metadata ecosystem**.

---

# **Purpose of the Figshare Layer**

The Figshare integration is essential for:

* provenance and traceability
* DOI-based citation stability
* version-controlled research outputs
* semantic linking across platforms
* reproducibility of the scientific process
* machine-readable access to all publications

It ensures all EFC scientific outputs are:

* citable
* discoverable
* archived
* link-consistent
* future-proof
* synchronized

---

# **Examples**

### Full index:

```bash
jq '.' figshare/figshare-index.json
```

### Latest DOI:

```bash
jq '.doi' figshare/latest.json
```

### Extract all URLs:

```bash
jq '.[] | .url' figshare/figshare-links.json
```

---

# **Connected Layers**

Figshare metadata feeds directly into:

### **Semantic Layer**

* `schema-map.json`
* `site-graph.json`
* ontology updates

### **API v1**

* `api/v1/meta.json`
* `concepts.json`
* DOI-linked concept definitions

### **Documentation**

* `docs/efc_master.html`
* cross-links inside the master specification

### **Dashboards**

* `meta_dashboard.py`
* metadata and provenance visualizations

---

# **Summary**

The `figshare/` directory is the **metadata backbone** of Energy-Flow Cosmology.

It:

* connects all official publications
* ensures versioned provenance
* synchronizes metadata automatically
* supports semantic linking
* feeds API and schema layers
* keeps the entire project consistent

This layer guarantees that EFC remains a **clean, open, verifiable scientific system**.

---
