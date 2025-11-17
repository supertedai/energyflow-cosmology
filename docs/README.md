# **Energy-Flow Cosmology — Documentation Layer**

The `docs/` directory contains the **complete scientific documentation system** for Energy-Flow Cosmology (EFC).
This layer unifies:

* the **HTML master document**
* the **LaTeX master document**
* all **published EFC articles**
* all **supporting figures**
* modular **LaTeX section files**
* archived historical versions

It forms the **public-facing scientific record** of the project.

---

# **Directory Structure (sync with repo)**

```
docs/
├── efc_master.html              # Main HTML specification
├── efc_master.css               # Stylesheet for HTML master
├── efc_master.tex               # LaTeX master
├── efc_master_template.html     # Clean MathJax-based HTML template
├── efc_master_v1.pdf            # Published PDF (versioned snapshot)
├── index.html                   # Documentation landing page
├── mathjax_header.html          # MathJax header for HTML builds
│
├── sections/                    # Modular LaTeX theory sections
│   ├── efc_s.tex
│   ├── efc_d.tex
│   ├── efc_c0.tex
│   ├── s0_s1_light_dynamics.tex
│   ├── observables.tex
│   ├── figures.tex
│   └── ...
│
├── figures/                     # Scientific diagrams + generated plots
│   ├── EFC_vs_LCDM_plot.png
│   ├── efc_halo_rho_profile.png
│   ├── efc_halo_S_profile.png
│   ├── efc_schematic_rotation_curves.png
│   ├── efc_schematic_lensing_profile.png
│   ├── efc_Ef_rho_S_heatmap.png
│   ├── efc_schematic_Hz.png
│   └── ...
│
├── articles/                    # Public-facing EFC articles (MD + PDF)
│   ├── EFC-A-Deep-Dive-into-the-Halo-Concept.md
│   ├── EFC-A-Deep-Dive-into-the-Halo-Concept.pdf
│   ├── EFC-Applications-and-Implications.md
│   ├── EFC-Grid-Higgs-Framework.pdf
│   ├── EFC-v2.1-Complete-Edition.md
│   ├── EFC-v2.2-Cross-Field-Integration-Summary.pdf
│   └── (40+ additional documents)
│
└── archive/                     # Archived master TeX files
    └── efc_master_v1.tex
```

*(All paths verified against your tree.)*

---

# **Purpose of the Documentation Layer**

The `docs/` directory is the **formal, human-readable** surface of EFC.
It gathers everything required to:

* understand the theory
* read specifications
* inspect derivations
* view figures
* access articles
* generate PDFs and HTML

This directory is the **scientific interface** of the project.

---

# **1. Master Documentation**

### **`efc_master.html`**

The main web-readable master specification.

Includes:

* full theory
* TOC + navigation
* MathJax rendering
* responsive layout (`efc_master.css`)

### **`efc_master.tex`**

The LaTeX master document, built from:

```
docs/sections/*.tex
```

GitHub Actions produce PDFs from this file automatically.

---

# **2. LaTeX Theory Sections**

Located in:

```
docs/sections/
```

These are the modular source files that assemble into the master:

* `efc_s.tex` — structure
* `efc_d.tex` — dynamics
* `efc_c0.tex` — entropy/information/light
* `s0_s1_light_dynamics.tex` — s₀–s₁
* `observables.tex` — measurable predictions
* `figures.tex` — figure placement and LaTeX integration

This system keeps the theory clean and modular.

---

# **3. Scientific Figures**

All figures used in:

* the master
* articles
* notebooks
* validation

are stored under:

```
docs/figures/
```

This includes:

* halo entropy + density profiles
* energy-flow potential heatmaps
* lensing schematics
* rotation curve figures
* LCDM vs EFC comparison plots

---

# **4. EFC Articles**

All public-facing articles (Markdown + PDF):

```
docs/articles/
```

Includes:

* conceptual deep dives
* theory overviews
* hypothesis papers
* summaries of EFC-S, EFC-D, EFC-C₀
* Grid–Higgs papers
* v2.1 / v2.2 editions
* observational interpretations

This folder forms the **EFC knowledge library**.

---

# **5. Archive (Historical Versions)**

```
docs/archive/
```

Contains earlier LaTeX master builds and legacy content retained for provenance.

---

# **Building the Documents**

### **Build PDF**

```bash
cd docs
latexmk -pdf efc_master.tex
```

### **HTML Build (if desired)**

You already have a clean template:

```
docs/efc_master_template.html
docs/mathjax_header.html
```

(A build script can be added later.)

---

# **How `docs/` Connects to the Rest of the Repo**

| Layer         | Role                                            |
| ------------- | ----------------------------------------------- |
| **theory/**   | source mathematical definitions                 |
| **docs/**     | human-readable documentation                    |
| **schema/**   | JSON-LD semantic layer                          |
| **figshare/** | DOI-synced metadata                             |
| **api/v1/**   | concept and term API                            |
| **output/**   | figures used inside docs                        |
| **meta/**     | metacognitive explanation and reasoning process |

`docs/` acts as the **presentation surface** for all scientific outputs.

---

# **Summary**

The `docs/` folder is the **public documentation hub** of the EFC system.

It contains:

* master theory documents
* modular LaTeX sections
* the article library
* all supporting figures
* archival versions

Everything needed to **read, understand, and present EFC** lives here.

---


