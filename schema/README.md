# 🧩 **EFC Schema Layer**

**Semantic Structure • JSON-LD Graph • Machine-Readable Ontology**

The `schema/` directory defines the **semantic backbone** of the Energy-Flow Cosmology (EFC) system.
It contains the machine-readable representations of:

* concepts
* methodology indexes
* documentation structure
* site graph
* schema map
* author metadata
* page/post navigation
* Figshare-synced entities

This layer allows EFC to function as a **structured knowledge graph** rather than a simple document repository.

---

# 📁 **Directory Structure**

```
schema/
├── author.jsonld               # Author identity + ORCID metadata
├── concepts.json               # Core EFC concepts (auto-synced)
├── docs-index.json             # Structure of documentation pages
├── methodology-index.json      # Semantic map of methodology layer
├── pages-structure.json        # Website page skeleton (WordPress)
├── posts-structure.json        # Blog/updates structure
├── schema-map.json             # Global schema map of all data sources
├── site-graph.json             # Full concept → page → file graph
├── sitemap-links.json          # Sitemap links for crawlers & SEO
├── update-schema.sh            # Script to regenerate schema assets
└── README.md                   # This document
```

---

# 🧠 **Purpose of the Schema Layer**

The schema layer turns the EFC repository into a:

* **knowledge graph**
* **machine-readable scientific model**
* **semantic index**
* **cross-linked conceptual system**

It ensures that:

* search engines
* knowledge engines
* AI models
* documentation tools
* dashboards

can understand and navigate the EFC system *algorithmically*.

---

# 🧩 **Key Files Explained**

### **`concepts.json`**

Defines all major EFC concepts.
Auto-generated from Figshare + internal definitions.

Contains:

* names
* definitions
* categories
* relationships
* DOIs
* metadata links

This is the *core ontology*.

---

### **`schema-map.json`**

Global semantic wiring diagram:

* how concepts relate
* where each concept lives (docs, theory, meta, notebooks)
* which files define which concepts
* crosslinks to API v1 and Figshare

Used by dashboards, search tools, and LLM interfaces.

---

### **`site-graph.json`**

A complete graph representation of:

* pages
* posts
* concepts
* datasets
* code modules
* meta-layer elements

This is the **semantic topology** of the entire project.

---

### **`docs-index.json`**

Defines the structure of `docs/`:

* master documents
* articles
* sections
* figures
* linking to concepts

Used for:

* automatic TOC building
* search interfaces
* tree-view browsers

---

### **`methodology-index.json`**

Semantic structure of the methodological layer:

* epistemology
* open-method
* reproducibility
* process models
* reflective nodes

Integrates with `/meta/` and `/api/v1`.

---

### **`pages-structure.json` & `posts-structure.json`**

Maps the WordPress site layout:

* verifies pages exist
* supports automatic JSON-LD injection
* enables hierarchy-aware crawlers
* feeds into sitemap-generation workflows

---

### **`sitemap-links.json`**

JSON representation of external sitemap entries.
Updated automatically by GitHub Actions.

---

### **`author.jsonld`**

Author metadata for JSON-LD:

* ORCID
* affiliation
* author provenance
* linked DOIs
* semantic identity graph

Used for SEO and citation metadata.

---

### **`update-schema.sh`**

CLI script that regenerates all schema files.
Used by:

* local builds
* GitHub Actions
* metadata dashboards

---

# 🔄 **Automatic Schema Synchronization**

Many files are updated via GitHub Actions:

* `figshare-sync`
* `schema-sync`
* `update api`
* `sitemap auto-refresh`

Sources:

* Figshare DOIs
* docs articles
* meta layer
* theory sections
* site map
* semantic crosslinking

The result is a **self-maintaining semantic graph**.

---

# 📬 **How This Layer Connects to the System**

| Layer              | Relationship                                           |
| ------------------ | ------------------------------------------------------ |
| **api/v1**         | Uses schema as input → public API                      |
| **meta/**          | Meta architecture appears in site-graph and schema-map |
| **theory/formal/** | Linked via concepts.json and schema-map                |
| **docs/**          | Connected through docs-index and site-graph            |
| **figshare/**      | Source of concept metadata                             |
| **app/dashboard/** | Visualizes schema and concept graph                    |

Schema = **the central nervous system** of EFC.

---

# 🧩 **Summary**

The `schema/` directory defines the **semantic structure** of Energy-Flow Cosmology:

* concepts
* relationships
* documentation indexing
* cross-layer linking
* metadata provenance
* automated updates

It transforms the EFC repository into a **living, machine-navigable knowledge graph**.

---
