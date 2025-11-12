# Energy-Flow Cosmology (EFC) Initiative  
![Auto Update Sitemap Schema](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)

This repository hosts the full public schema and documentation for the **Energy-Flow Cosmology (EFC)** framework — a unified thermodynamic model connecting cosmic structure, dynamics, and cognition.

- [Concept Schema](https://github.com/supertedai/energyflow-cosmology/blob/main/schema/concepts.json) — machine-readable vocabulary of all major EFC concepts and models.  
- [Documentation Index](https://github.com/supertedai/energyflow-cosmology/blob/main/schema/docs-index.json) — complete index of publications, technical papers, and Figshare-linked DOIs.  
- Auto-synced workflow: Changes are managed via GitHub and pushed automatically into the WordPress site at [energyflow-cosmology.com](https://energyflow-cosmology.com).

---

## 🔗 Key Links

**Author:** Morten Magnusson  
**Affiliation:** Energy-Flow Cosmology Initiative  
**Website:** [https://energyflow-cosmology.com](https://energyflow-cosmology.com)  
**ORCID:** [0009-0002-4860-5095](https://orcid.org/0009-0002-4860-5095)  
**Figshare Profile:** [Morten Magnusson on Figshare](https://figshare.com/authors/Morten_Magnusson/20477774)

---

## 🧠 Overview

**Energy-Flow Cosmology (EFC)** is a unified thermodynamic framework describing the universe as a continuous flow of energy guided by entropy gradients.  
It provides an alternative to the ΛCDM model by replacing dark matter and dark energy with measurable thermodynamic dynamics.

### Conceptual Structure

| Domain | Description |
|--------|--------------|
| **EFC-S (Structure)** | Explains how entropy gradients generate geometry and the cosmic web. |
| **EFC-D (Dynamics)** | Describes expansion, gravity, and time as emergent properties of energy flow. |
| **EFC-C (Cognition)** | Extends the same thermodynamic logic to awareness and information systems. |

---

## 📁 Repository Structure

| Folder | Purpose |
|--------|----------|
| `/schema` | JSON-LD and structured data for schema.org integration. |
| `/docs` | Articles and theoretical modules (Markdown or HTML). |
| `/figshare` | DOI mappings, preprints, and metadata exports. |
| `/website` | Web-ready HTML templates from energyflow-cosmology.com. |
| `/images` | Diagrams, figures, and conceptual graphics. |
| `/data` | Observational and validation datasets (e.g. DESI, JWST). |
| `/scripts` | Utility scripts for automation and content generation. |

---

## 🎯 Current Focus

1. Integrate all published Figshare works (DOI-linked) into `/docs`.  
2. Expand `/schema` to include full schema.org markup for each concept.  
3. Automate synchronization between website and GitHub for version control.  
4. Prepare a machine-readable knowledge graph (Neo4j + JSON-LD export).  

---

## 📚 Citation

If referencing this repository or associated works:

> Magnusson, M. (2025). *Energy-Flow Cosmology (EFC): Unified Thermodynamic Framework.*  
> Energy-Flow Cosmology Initiative. [https://energyflow-cosmology.com](https://energyflow-cosmology.com)

---

## ⚖️ License

All textual and visual materials © Morten Magnusson, 2025.  
Distributed for academic and educational use under **Creative Commons CC-BY-NC-SA 4.0**.  
See: [https://creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## 🧩 Semantic Integration Guide

This repository is directly connected to the live WordPress site via a **child theme function** that dynamically loads and injects the JSON-LD schema from GitHub into every page.

### Architecture Overview

| Layer | Function | Location |
|-------|-----------|-----------|
| **GitHub (source)** | Authoritative JSON-LD schema files (`site-graph.json`, `concepts.json`, `docs-index.json`) | `main` branch |
| **WordPress (frontend)** | Public presentation layer for Energy-Flow Cosmology | [energyflow-cosmology.com](https://energyflow-cosmology.com) |
| **PHP Bridge** | Fetches JSON-LD data and inserts it into `<head>` | `functions.php` in the child theme |
| **Search / LLM Layer** | Google, Bing, Copilot, Perplexity, etc. read structured data for knowledge graph mapping | Automatic |

**Configuration**  
File: `.github/workflows/update-schema.yml`  
Script: `schema/update-schema.sh`

This ensures that search engines, LLMs, and data indexers always reference the **most recent semantic structure** of *Energy-Flow Cosmology*.

---

### 🔧 Active PHP Function (WordPress Integration)

```php
function efc_load_schema_from_github() {
  $url = 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/site-graph.json';
  $response = wp_remote_get($url);
  if (is_array($response) && !is_wp_error($response)) {
    echo '<script type="application/ld+json">' . $response['body'] . '</script>';
  }
}
add_action('wp_head', 'efc_load_schema_from_github');
```

---

## 🔭 Latest Validation Dashboard

Automated validation plots generated by the EFC model (JWST, DESI, SPARC):

![EFC Validation Dashboard](https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/output/EFC_Validation_Dashboard.png)

---

**Workflow Status:**  
![EFC Auto Validation](https://github.com/supertedai/energyflow-cosmology/actions/workflows/run-validation.yml/badge.svg)  
*Last automatic update triggers new validation plots and dashboard regeneration.*
