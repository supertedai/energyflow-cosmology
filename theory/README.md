# **EFC Theory Layer**

This directory contains the full scientific and mathematical foundation of **Energy-Flow Cosmology (EFC)**.
It is split into two levels:

1. **High-level theoretical architecture**
2. **Formal mathematical specification** (in `/formal/`)

Together, these define the complete structure, dynamics, and semantics of the EFC model.

---

# Directory Structure

```
theory/
├── formal/                  # Full mathematical specification (TeX)
│   ├── efc_formal_spec.tex
│   ├── efc_formal_spec.pdf
│   ├── efc_s_model.tex
│   ├── efc_d_model.tex
│   ├── efc_h_model.tex
│   ├── efc_structure_model.tex
│   ├── notation.tex
│   ├── parameters.tex
│   ├── efc_header.tex
│   ├── meta_index.tex
│   ├── meta_architecture_section.tex
│   ├── meta_reflective_section.tex
│   └── efc_flow_diagram.tex
│
├── architecture.md          # Conceptual architecture + design overview
└── README.md                # This file
```

---

# **Purpose of the Theory Layer**

The theory layer provides:

* The mathematical foundation for energy-flow dynamics
* Entropy-based structure formation
* Expansion geometry
* Parameter definitions and notation
* Reflective/meta sections describing reasoning structure
* A unified TeX build for the full formal specification PDF

It represents the **ground truth** for all scientific statements in EFC.

---

# **High-Level Architecture Files**

### **`architecture.md`**

Conceptual overview of how the EFC theory is structured.

Includes:

* Core subsystems (S, D, H, Φ)
* How the equations interact
* How theory → model → validation is separated
* Rationale for the thermodynamic framework

Useful for readers who want insight before diving into TeX.

---

# **Formal Specification (`formal/` directory)**

This folder contains the complete TeX-based formalization of EFC.

### **`efc_formal_spec.tex`**

The master file.
Includes all subsystems and meta-sections.

### Core subsystem files:

* `efc_s_model.tex` — Entropy field & gradient (EFC-S)
* `efc_d_model.tex` — Energy-flow potential (EFC-D)
* `efc_h_model.tex` — Expansion mapping (EFC-H)
* `efc_structure_model.tex` — Structure formation (EFC-Φ)

### Supporting files:

* `notation.tex` — Symbols, units, definitions
* `parameters.tex` — Model parameters
* `efc_header.tex` — Shared definitions/macros
* `efc_flow_diagram.tex` — Flow diagrams
* `meta_index.tex` — Structure of meta-sections
* `meta_architecture_section.tex` — Meta-architecture
* `meta_reflective_section.tex` — Reflective theory section

### Output:

* `efc_formal_spec.pdf` — auto-generated via GitHub Actions

---

# **Building the Formal Specification**

Build locally:

```bash
cd theory/formal
latexmk -pdf efc_formal_spec.tex
```

GitHub Actions automatically builds:

* `efc_formal_spec.pdf`
* stores it in `theory/formal/`

---

# **Design Philosophy**

The theory layer is designed around four principles:

### **1. Mathematical completeness**

All equations and definitions are explicit.

### **2. Structural clarity**

Subsystems (S, D, H, Φ) reflect the actual flow of the cosmological model.

### **3. Separation of concerns**

Theory is independent of:

* code
* validation
* API definitions
* dashboard logic
* semantic annotations

### **4. Reproducibility and transparency**

The full theory is published as an open, inspectable TeX specification.

---

# Summary

The `theory/` directory contains:

* The conceptual architecture of the EFC model
* The full formal mathematical specification
* Meta-level reasoning structures
* Auto-generated PDFs and TeX build support

It defines *how EFC works* at the deepest scientific level.

---
