![Auto Update Sitemap Schema](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)

Energy-Flow Cosmology (EFC) Initiative

This repository hosts the full public schema and documentation for the EFC framework — a unified thermodynamic model connecting cosmic structure, dynamics and cognition.

• Schema Definitions: /schema/concepts.json — machine-readable vocabulary of all major EFC concepts and models.
• Documentation Set: /schema/docs-index.json plus companion files in /docs/ — full list of publications, technical papers and preprints with DOIs.
• Auto-Synced Workflow: Changes are managed via GitHub and pushed automatically into the WordPress site at energyflow-cosmology.com.

Key Links

ORCID: https://orcid.org/0009-0002-4860-5095

# Energy-Flow Cosmology (EFC)

**Author:** Morten Magnusson  
**Affiliation:** Energy-Flow Cosmology Initiative  
**Website:** [https://energyflow-cosmology.com](https://energyflow-cosmology.com)  
**ORCID:** [0009-0002-4860-5095](https://orcid.org/0009-0002-4860-5095)  
**Figshare Profile:** [https://figshare.com/authors/Morten_Magnusson/20477774](https://figshare.com/authors/Morten_Magnusson/20477774)

---

## Overview

Energy-Flow Cosmology (EFC) is a **unified thermodynamic framework** describing the universe as a continuous flow of energy guided by entropy gradients.  
It provides an alternative to the ΛCDM model by replacing dark matter and dark energy with measurable thermodynamic dynamics.

The theory is structured into three domains:

| Domain | Description |
|--------|--------------|
| **EFC-S (Structure)** | Explains how entropy gradients generate geometry and the cosmic web. |
| **EFC-D (Dynamics)** | Describes expansion, gravity, and time as emergent properties of energy flow. |
| **EFC-C (Cognition)** | Extends the same thermodynamic logic to awareness and information systems. |

---

## Repository Structure

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

## Current Focus

1. Integrate all published Figshare works (DOI-linked) into `/docs`.  
2. Expand `/schema` to include complete schema.org markup for each concept.  
3. Automate synchronization between website and GitHub for version control.  
4. Prepare future machine-readable knowledge graph (Neo4j, JSON-LD export).

---

## Citation

If referencing this repository or associated works:

> Magnusson, M. (2025). *Energy-Flow Cosmology (EFC): Unified Thermodynamic Framework*.  
> Energy-Flow Cosmology Initiative. [https://energyflow-cosmology.com](https://energyflow-cosmology.com)

---

## License
All textual and visual materials © Morten Magnusson, 2025.  
Distributed for academic and educational use under Creative Commons CC-BY-NC-SA 4.0.

---

## 🧩 Semantic Integration Guide

This repository is directly connected to the live WordPress site via a **child theme function** that dynamically loads and injects the JSON-LD schema from GitHub into every page.

### Architecture Overview

| Layer | Function | Location |
|-------|-----------|-----------|
| **GitHub (source)** | Authoritative JSON-LD schema files (`site-graph.json`, `posts-structure.json`) | `main` branch |
| **WordPress (frontend)** | Public presentation layer for the Energy-Flow Cosmology website | [https://energyflow-cosmology.com](https://energyflow-cosmology.com) |
| **PHP Bridge** | Fetches JSON-LD data and inserts it into `<head>` | Child theme `functions.php` |
| **Search / LLM Layer** | Google, Bing, Copilot, Perplexity, etc. read structured data for knowledge graph mapping | Automatic |

## ⚙️ Automation

### Auto Update Sitemap Schema
![Auto Update Sitemap Schema](https://github.com/supertedai/energyflow-cosmology/actions/workflows/update-schema.yml/badge.svg)

This automated workflow keeps the project’s sitemap and Schema.org definitions up-to-date.

**Triggers**
- 🕒 Runs automatically every night at 03:00 UTC  
- 🧩 Can be started manually from the **Actions** tab  
- 🔄 Executes on every commit to `main`

**Process**
1. Checks out the repository  
2. Fetches the latest `sitemap.xml` and JSON-LD schema from the website  
3. Commits and pushes any detected changes back to the repository  

**Configuration**
File: `.github/workflows/update-schema.yml`  
Script: `schema/update-schema.sh`

This ensures that search engines, LLMs, and data indexers always reference the most recent semantic structure of *Energy-Flow Cosmology*.

### Active Function

The WordPress child theme includes the following PHP function:

```php
function efc_load_schema_from_github() {
  $url = 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/site-graph.json';
  $response = wp_remote_get($url);
  if (is_array($response) && !is_wp_error($response)) {
    echo '<script type="application/ld+json">' . $response['body'] . '</script>';
  }
}
add_action('wp_head', 'efc_load_schema_from_github');
