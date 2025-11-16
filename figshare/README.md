# 📦 **EFC Figshare Integration Layer**

The `figshare/` directory contains all metadata, links, and indices synchronized from Figshare into the Energy-Flow Cosmology repository.
This layer acts as the **central bridge** between:

* the scientific publications stored on Figshare
* the semantic structure stored in GitHub
* the machine-readable metadata used by API v1
* automated workflows that maintain the knowledge graph

All files here are **auto-generated** and updated by GitHub Actions.

---

# 📁 **Directory Contents**

```
figshare/
├── figshare-index.json     # Global index of all Figshare records
├── figshare-links.json     # DOI + URL mapping for all EFC publications
└── latest.json             # Snapshot of the newest published record
```

---

# 📄 **File Descriptions**

### **1. `figshare-index.json`**

A complete mapping of *all* EFC-related items published on Figshare.

Includes for each item:

* DOI
* version
* title
* description
* file list
* publication date
* categories / tags
* internal identifiers

This file powers:

* API regeneration
* semantic linking
* reference consistency checks
* automated documentation updates

---

### **2. `figshare-links.json`**

A simplified file containing only the essential links:

* DOI → URL
* internal ID → DOI
* latest version of each entry

Used for:

* embedding DOIs in the website
* updating schema files
* linking API metadata
* generating citation blocks

---

### **3. `latest.json`**

A minimal JSON document describing the **newest published Figshare record**.

Includes:

* DOI
* title
* version
* timestamp
* figshare_id

Used by automation to:

* detect when new scientific content is released
* trigger API regeneration
* update semantic structures
* refresh dashboards

---

# 🔄 **Automatic Sync Workflow**

The Figshare integration runs through:

```
.github/workflows/fetch_figshare.yml
scripts/fetch_figshare_full.py
scripts/update_efc_api.py
```

The workflow:

1. Fetches all metadata from Figshare
2. Generates `figshare-index.json`
3. Updates `figshare-links.json`
4. Identifies new releases → writes into `latest.json`
5. Triggers API regeneration
6. Updates schema files
7. Ensures the EFC knowledge graph is always current

This creates a **self-updating metadata ecosystem**.

---

# 🔍 **Purpose of the Figshare Layer**

The Figshare integration is essential for:

* metadata provenance
* DOI tracking
* long-term archival stability
* linking theory, data, and publications
* enabling semantic search across datasets
* providing authoritative version history
* machine-level reproducibility

It ensures that **all scientific outputs of EFC** remain:

* traceable
* citable
* reference-stable
* synchronized across platforms

---

# 📘 **Examples**

### Access the full index:

```bash
jq '.' figshare/figshare-index.json
```

### Get the latest DOI:

```bash
jq '.doi' figshare/latest.json
```

### Extract all publication URLs:

```bash
jq '.[] | .url' figshare/figshare-links.json
```

---

# 🧲 **Connected Layers**

The Figshare metadata feeds directly into:

### **Semantic Layer**

* `schema-map.json`
* `site-graph.json`
* ontology updates

### **API v1**

* `meta.json`
* `concepts.json`

### **Documentation**

* `docs/efc_master.html`
* formal specification metadata

### **Dashboards**

* EFC Metadata Dashboard
* Meta-layer reflective dashboards

---

# 🧩 **Summary**

The `/figshare/` directory is the **metadata backbone** of EFC:

* connects all official publications
* ensures versioned provenance
* automates synchronization
* supports semantic linking
* feeds the API and schema systems
* keeps the entire project self-consistent

This layer guarantees that EFC remains a **clean, open, verifiable scientific system**.

---
