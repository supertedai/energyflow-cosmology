# **Energy-Flow Cosmology — Documentation Layer**

The `docs/` directory contains the **complete documentation system** for Energy-Flow Cosmology (EFC).
This layer unifies:

* the **HTML master document**
* the **LaTeX master document**
* all **published articles**
* all **supporting figures**
* modular **section files**
* meta-level documents
* archived historical versions

It represents the **public-facing scientific documentation** of EFC.

---

# Directory Structure

```
docs/
├── efc_master.html            # Main HTML specification
├── efc_master.css             # Stylesheet for the HTML master
├── efc_master.tex             # LaTeX master (parallel to HTML)
├── efc_master_template.html   # Clean HTML template (MathJax + layout)
├── efc_master_v1.pdf          # Uploaded master v1 (static copy)
├── index.html                 # Documentation landing page
├── mathjax_header.html        # Script header for MathJax rendering
│
├── sections/                  # LaTeX theory modules
│   ├── efc_s.tex
│   ├── efc_d.tex
│   ├── efc_c0.tex
│   ├── s0_s1_light_dynamics.tex
│   ├── observables.tex
│   ├── figures.tex
│   └── ...
│
├── figures/                   # Scientific figures, plots, diagrams
│   ├── EFC_vs_LCDM_plot.png
│   ├── efc_halo_rho_profile.png
│   ├── efc_halo_S_profile.png
│   ├── efc_schematic_rotation_curves.png
│   ├── efc_schematic_lensing_profile.png
│   ├── efc_Ef_rho_S_heatmap.png
│   ├── efc_schematic_Hz.png
│   └── ...
│
├── articles/                  # Public-facing EFC articles (MD + PDF)
│   ├── EFC-A-Deep-Dive-into-the-Halo-Concept.md
│   ├── EFC-A-Deep-Dive-into-the-Halo-Concept.pdf
│   ├── EFC-CMB-Thermodynamic-Gradient.md
│   ├── EFC-Thermodynamic-Bridge-GR-QFT.pdf
│   ├── EFC-v2.1-Complete-Edition.md
│   ├── EFC-v2.2-Cross-Field-Integration-Summary.pdf
│   └── (40+ additional articles)
│
├── meta/                      # Meta-level docs imported into docs layer
│   ├── CEM-Consciousness-Ego-Mirror.md
│   ├── CEM-Consciousness-Ego-Mirror.pdf
│   └── EFC-Hypothesis-Entropy-and-Energy-Flow.docx
│
└── archive/                   # Archived master LaTeX files
    └── efc_master_v1.tex
```

---

# Purpose of the Documentation Layer

The `docs/` directory is the **central place where all human-readable EFC material lives**.
It integrates:

### **1. Master Documentation**

* `efc_master.html`
* `efc_master.tex`
* CSS, template, and MathJax headers

These form the authoritative **documentation outputs**.

### **2. LaTeX Theory Sections**

Found under `docs/sections/`, aligned with:

* EFC-S (entropy model)
* EFC-D (energy-flow model)
* EFC-C₀ (light/entropy boundary)
* Observables
* Figures
* Cross-section structure

These assemble into the master TeX document.

### **3. Scientific Articles**

All public EFC articles (Markdown + PDF).
This includes:

* deep dives
* hypotheses
* observational interpretations
* theory overviews
* versioned summaries

This is effectively the **EFC knowledge library**.

### **4. Scientific Figures**

All plots and schematic diagrams used in:

* the master documents
* the articles
* external presentations
* validation graphics

Moved here to centralize figure use across multiple workflows.

### **5. Meta Documents (Imported)**

Documents that bridge EFC theory with:

* cognition
* entropy interpretation
* CEM
* reflective layers

These are **not part of the physics theory**, but included for completeness.

### **6. Archive Folder**

Stores historic versions of master TeX documents and earlier builds.

---

# Master Documents

## **`efc_master.html`**

The **primary web-readable** master document.

Includes:

* MathJax equation rendering
* full table of contents
* responsive design
* clean CSS (`efc_master.css`)

## **`efc_master.tex`**

The **primary LaTeX master**.
Built from modular `sections/*.tex`.

Production builds are handled by GitHub Actions.

---

# Building the Master Documents

### **HTML build**

```bash
python scripts/build_html.py
```

### **LaTeX (PDF) build**

```bash
cd docs
latexmk -pdf efc_master.tex
```

---

# 📬 How This Directory Interacts With the Rest of the Repo

| Layer              | Role                                           |
| ------------------ | ---------------------------------------------- |
| **theory/**        | Pure formal math (TeX subsystem)               |
| **docs/**          | Public, human-readable surface                 |
| **schema/**        | Machine-readable structure of concepts         |
| **figshare/**      | DOI-synced metadata feeding docs               |
| **api/v1**         | JSON interface — some fields link back to docs |
| **app/dashboard/** | Visual layer rendering parts of the docs       |

`docs/` is the **presentation layer** for all scientific content.

---

# Summary

The `docs/` directory is the **official documentation hub** for Energy-Flow Cosmology.

It contains:

* master documents
* article library
* modular LaTeX theory
* complete figure set
* meta documents
* archival versions

Everything needed to **read, understand, publish, and present EFC** lives here.

---
