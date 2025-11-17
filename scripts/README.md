# **EFC Scripts — Computational, Semantic & Validation Tools**

The `scripts/` directory contains all executable tools that support
**data processing**, **validation**, **semantic generation**,
and **automation** within Energy-Flow Cosmology (EFC).

This layer turns the repository into a **living computational system**.

Scripts fall into five categories:

1. **Data fetching & preprocessing**
2. **Validation & simulation**
3. **Plotting & figure generation**
4. **Schema & API generation**
5. **Utility and diagnostic tools**

---

# **Directory Overview**

```
scripts/
├── fetch_figshare_auto.py
├── fetch_sparc_rc.py
├── parse_sparc_table1.py
│
├── run_efc_baseline.py
├── run_sparc_validation.py
├── validate_efc.py
├── validate_all.py
│
├── generate_efc_vs_lcdm_plot.py
├── plot_c_of_S.py
├── plot_results.py
│
├── generate_methodology_api.py
├── update_concepts.py
├── update_efc_api.py
├── generate_repo_map.py
│
├── import_methodology_to_neo4j.py
├── check_imports.py
└── test_* (test_c_entropy.py, test_gradients.py)
```

---

# **1. Data Fetching & Preprocessing**

### **`fetch_figshare_auto.py`**

Automatically retrieves Figshare metadata and updates:

* `figshare-index.json`
* `figshare-links.json`
* `/api/v1/meta.json`

Part of the self-updating metadata layer.

### **`fetch_sparc_rc.py`**

Downloads SPARC rotation curve datasets.
Used for validation of EFC rotation predictions.

### **`parse_sparc_table1.py`**

Parses SPARC "Table 1" (galaxy parameters) into machine-friendly format.

---

# **2. Validation & Simulation**

### **`run_efc_baseline.py`**

Runs the baseline EFC simulation:

* entropy → expansion
* energy-flow potential
* predicted structure profiles

### **`run_sparc_validation.py`**

Runs full SPARC validation:

* rotation curves
* halo profiles
* entropy-radius relationships

### **`validate_efc.py`**

End-to-end validation script:

* SPARC
* DESI
* JWST
* theoretical consistency checks

### **`validate_all.py`**

Meta-wrapper that runs all validation subsystems in one command.

---

# **3. Plotting & Figure Generation**

These scripts generate the plots stored under `/docs/figures/`.

### **`generate_efc_vs_lcdm_plot.py`**

Plots EFC vs ΛCDM expansion dynamics.

### **`plot_c_of_S.py`**

Plots the information-capacity function ( c(S) ).

### **`plot_results.py`**

General plotting utility for validation output.

---

# **4. Schema & API Generation**

These scripts maintain the EFC semantic and API layers.

### **`generate_methodology_api.py`**

Turns `/methodology/` documents into machine-readable API entries.

### **`update_concepts.py`**

Synchronizes high-level concepts across:

* schema
* API
* Figshare metadata

### **`update_efc_api.py`**

Regenerates the entire API v1:

* concepts
* methodology
* meta
* terms
* index files

### **`generate_repo_map.py`**

Produces a machine-readable and human-readable map of the repository layout.

---

# **5. Utility & Diagnostics**

### **`import_methodology_to_neo4j.py`**

Loads methodology + meta-process into Neo4j
(used for introspective graph dashboards).

### **`check_imports.py`**

Ensures all Python modules in `/src/efc/` import cleanly
(used by GitHub Actions).

### **`test_c_entropy.py` & `test_gradients.py`**

Unit tests for:

* entropy functions
* gradients
* energy-flow consistency

---

# **Usage**

Run any script with Python:

```bash
python scripts/run_efc_baseline.py
python scripts/validate_efc.py
python scripts/generate_efc_vs_lcdm_plot.py
```

Scripts assume:

* the repo root is the working directory
* dependencies listed in `requirements.txt` are installed

---

# **Role of the Script Layer**

The `scripts/` directory acts as the automation engine of EFC:

| Domain            | Contribution                                       |
| ----------------- | -------------------------------------------------- |
| **Data**          | Fetches and formats scientific datasets            |
| **Validation**    | Runs numerical checks and observational tests      |
| **Documentation** | Generates figures and documentation assets         |
| **Semantic**      | Regenerates schema and API layers                  |
| **Meta**          | Integrates process-level insight into Neo4j graphs |

Everything outside of core theory passes through this layer.

---

# **Summary**

The `scripts/` folder provides:

* dataset ingestion
* full EFC validation
* plotting
* semantic graph generation
* API updates
* Neo4j imports
* diagnostic tests

It is the **computational and automation backbone** of the EFC project.

---
