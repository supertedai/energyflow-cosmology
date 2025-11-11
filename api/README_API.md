---

## 📘 `api/README_API.md`

````markdown
# Energy-Flow Cosmology (EFC) – Open Semantic API

This API provides machine-readable access to the conceptual structure of **Energy-Flow Cosmology (EFC)** — a thermodynamic framework unifying cosmic structure, dynamics, and cognition.

All data follows the [Schema.org/DefinedTermSet](https://schema.org/DefinedTermSet) specification and is automatically updated from `schema/concepts.json` on every commit.

---

## 📂 Structure

| File / Folder | Content | Format |
|----------------|----------|---------|
| `api/v1/concepts.json` | Full EFC concept set (core ontology) | JSON-LD |
| `api/v1/terms.json` | Simplified term list (name, id, url) | JSON |
| `api/v1/concept/` | One file per concept (e.g., `entropy-gradient.json`) | JSON-LD |
| `api/index.json` | Manifest and metadata (optional) | JSON |

---

## 🧠 Examples

```bash
# Fetch all concepts
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concepts.json

# Fetch the simplified term list
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json

# Fetch one specific concept
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concept/entropy-gradient.json
````

---

## 🧩 Usage

The EFC API can be used for:

1. **Semantic indexing**
   – Enables search engines and LLMs to read and interpret structured scientific concepts.

2. **Scientific integration**
   – Allows other research projects to reference or import EFC terms into their own models.

3. **AI & RAG systems**
   – LLMs or local retrieval systems can query definitions, relationships, and structured context.

---

## 🔗 Authorship & Authority

* **Creator:** Morten Magnusson
* **Initiative:** Energy-Flow Cosmology Initiative
* **ORCID:** [0009-0002-4860-5095](https://orcid.org/0009-0002-4860-5095)
* **Main site:** [https://energyflow-cosmology.com](https://energyflow-cosmology.com)
* **Figshare:** [https://figshare.com/authors/Morten_Magnusson/20477774](https://figshare.com/authors/Morten_Magnusson/20477774)

Each term links to verified DOIs hosted on Figshare, providing traceable provenance and citation integrity.

---

## 🧮 Technical background

This API is **fully auto-generated** via GitHub Actions:

* **Source:** `schema/concepts.json`
* **Workflow:** `.github/workflows/update-api.yml`
* **Validation:** `jq` + `jsonlint`
* **Hosting:** Static files, version-controlled on GitHub

No server or database is required — everything is reproducible, cacheable, and open for federation.

---

## 📜 License & Citation

Released under **CC-BY-4.0**.
Please cite as:

> Magnusson, M. (2025). *Energy-Flow Cosmology (EFC) – Open Semantic API.*
> Energy-Flow Cosmology Initiative.
> GitHub: [https://github.com/supertedai/energyflow-cosmology](https://github.com/supertedai/energyflow-cosmology)

---

## 🧭 Planned extensions

* `v2/` with cross-linked structure, dynamics, and cognition layers
* RDF / TTL export for semantic-web interoperability
* SPARQL endpoint for academic querying
* DOI assignment via Zenodo for versioned API releases

---

**In short:**
This repository serves as the **official, verifiable semantic source** for the Energy-Flow Cosmology framework — accessible to both humans and machines.

```

---

### ✅ How to add it

1. In your GitHub repo, create a file:  
   `api/README_API.md`
2. Paste the text above  
3. Commit with message:  
```
