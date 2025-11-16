# Energy-Flow Cosmology (EFC)

📘 **Start Here**  
If you are new to the project, begin with:  
👉 **[START-HERE.md](START-HERE.md)**  
This file gives a clear orientation to the entire repository: the theory, the meta-architecture, the cognitive process, the symbiosis layer, the validation pipeline, and the overall structure.

---

**Formal Specification • Semantic Knowledge Graph • Computational Framework**

Energy-Flow Cosmology (EFC) is a thermodynamic cosmology built on energy-flow potential, entropy-gradients, and emergent structure formation.
This repository contains the full scientific theory, semantic schema, computational models, workflows, validation pipelines, and integration tools.

It is designed as a **self-updating scientific system**:

* theory → LaTeX master
* web → HTML master
* ontology → JSON-LD schema
* data sources → Figshare sync
* validation → automated pipelines
* code → notebooks, simulators, and API v1
* dashboards → semantic and scientific visualization

Everything is structured for clarity, reproducibility, and long-term maintainability.

---

# 📌 **Overview**

EFC combines:

* **Formal mathematical theory** (entropy, energy-flow, potentials, dynamics)
* **Semantic mappings** (concepts, definitions, ontology, schema)
* **Computational models** (Python modules, simulators, utilities)
* **Automated scientific workflows** (GitHub Actions)
* **Validation pipelines** (SPARC, DESI, JWST, CMB, etc.)
* **Metadata synchronization** with Figshare DOIs and scientific datasets
* **Dashboards and tools** for interactive exploration

The repository follows a strict separation of *theory, schema, and computation*.

---

# 🧠 **Repository Architecture**

The project is organized into three fundamental layers:

### **1. Theory Layer**

Mathematical foundation of Energy-Flow Cosmology.

* Master LaTeX document (`efc_master.tex`)
* Sectioned structure for modular development
* Figures for theory and publication
* Basis for PDF generation and journal submission

### **2. Semantic Layer**

Machine-readable ontology and metadata graph.

* Concepts, definitions, relationships
* Schema.org JSON-LD integration
* Figshare metadata sync
* Cross-referencing nodes (cognition, reflection, symbiosis)

### **3. Computational Layer**

The implementation of EFC simulations, validation, and tools.

* Python modules under `/src/efc/`
* Notebooks for SPARC, DESI, JWST validation
* API v1 (concepts, methodology, terms, metadata)
* Dashboards for visual exploration
* Automated workflows for continuous integration

---

# 📁 **Repository Structure**

````markdown
📁 Repository Structure (click to expand)

```
/
├── api/
│   └── v1/
│       ├── concepts.json
│       ├── methodology.json
│       ├── terms.json
│       ├── meta.json
│       └── README.md
│
├── app/
│   └── dashboard/
│       ├── index.html
│       ├── style.css
│       └── script.js
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── archive/
│
├── docs/
│   ├── efc_master.html
│   └── figures/
│
├── figshare/
│   ├── figshare-links.json
│   └── metadata.json
│
├── integrations/
│   └── wp/
│       └── efc-schema-loader/
│           ├── efc-schema-loader.php
│           ├── loader-core.php
│           ├── admin/
│           └── includes/
│
├── meta/
│   ├── cognition/
│   ├── reflection/
│   └── symbiosis/
│
├── methodology/
│   └── README.md
│
├── notebooks/
│   ├── EFC_Baseline.ipynb
│   └── SPARC_Validation.ipynb
│
├── schema/
│   ├── concepts.json
│   ├── schema-map.json
│   └── site-graph.json
│
├── scripts/
│   ├── fetch_figshare_full.py
│   ├── update_efc_api.py
│   ├── validate_efc.py
│   ├── check_imports.py
│   └── build_html.py
│
├── src/
│   └── efc/
│       ├── core/
│       ├── models/
│       ├── utils/
│       └── simulators/
│
├── theory/
│   ├── efc_master.tex
│   └── sections/
│
├── .github/workflows/
│   ├── fetch_figshare.yml
│   ├── build_master_clean.yml
│   ├── export_api.yml
│   └── validation.yml
│
├── .gitignore
├── CHANGELOG.md
├── START-HERE.md
├── requirements.txt
└── README.md
```

````

---

# 🔧 **Installation**

Clone the repository:

```bash
git clone https://github.com/supertedai/energyflow-cosmology.git
cd energyflow-cosmology
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

# ⚙️ **Build System**

### **LaTeX Master Build**

```bash
cd theory
latexmk -pdf efc_master.tex
```

### **HTML Master Build**

```bash
python scripts/build_html.py
```

### **API Regeneration**

```bash
python scripts/update_efc_api.py
```

### **Figshare Sync**

Triggered automatically by GitHub Actions or manually:

```bash
python scripts/fetch_figshare_full.py
```

---

# 📊 **Validation Pipelines**

Validation notebooks and scripts include:

* SPARC rotation curves
* DESI growth curves
* JWST galaxy distributions
* CMB entropy mapping

Run validation:

```bash
python scripts/validate_efc.py
```

---

# 🌐 **Dashboards and Visualization**

The repository includes an interactive dashboard under:

```
app/dashboard/
```

Open locally:

```bash
open app/dashboard/index.html
```

A semantic dashboard (`meta_dashboard.py`) supports ontology analysis and graph traversal.

---

# 🧬 **Semantic Integration**

EFC is fully integrated with:

* Figshare DOIs
* Schema.org JSON-LD
* Site graph
* Concept graph
* API v1 ontology

The `schema/` directory defines the full semantic layer.

---

# 📚 **Documentation**

Two master documents serve as the “single source of truth”:

* **Mathematical master:** `theory/efc_master.tex`
* **Web specification:** `docs/efc_master.html`

Both are generated automatically.

---

# **📄 License**

Distributed under **CC-BY-4.0**
© 2025 — *Morten Magnusson* — Energy-Flow Cosmology Initiative

---

# 🤝 **Contributions**

Pull requests are welcome.
For changes to core theory or schema, open an issue first to discuss the direction.

---

# 🎯 **Status**

The repository is actively developed and maintained as part of a larger research program on thermodynamic cosmology, emergent structure formation, and AI-assisted scientific methodology.

---
