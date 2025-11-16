# ⚙️ **EFC Source Code — Computational Engine**

The `src/` directory contains the full **computational implementation** of
**Energy-Flow Cosmology (EFC)**.

This is the engine that powers:

* entropy calculations
* energy-flow dynamics
* expansion rate evolution
* structure formation models
* validation routines
* co-field simulation (Fase 4)

It mirrors the mathematical formalism defined in `/theory/formal/`.

---

# 📁 **Directory Structure**

```
src/
├── __init__.py
├── efc_light.py            # Light/entropy boundary dynamics
│
├── efc/                    # Main EFC package
│   ├── core/               # Core model logic
│   │   └── efc_core.py
│   │
│   ├── entropy/            # Entropy-field dynamics
│   │   └── efc_entropy.py
│   │
│   ├── potential/          # Energy-flow potential model
│   │   └── efc_potential.py
│   │
│   ├── validation/         # Validation utilities
│   │   ├── efc_validation.py
│   │   └── sparc_io.py
│   │
│   └── meta/               # Meta-simulation layer
│       ├── __init__.py
│       └── cofield_simulator.py
```

---

# 🧠 **1. Core Module (`core/`)**

### **`efc_core.py`**

Contains the fundamental engine of EFC:

* entropy → energy-flow → expansion chain
* core equations
* numerical integration
* shared utility functions
* analytic + numerical hybrids

This is the central “physics engine” of the model.

---

# 🔥 **2. Entropy Module (`entropy/`)**

### **`efc_entropy.py`**

Implements the entropy-field evolution:

* entropy (S(r,t))
* gradients ( \nabla S )
* entropy–capacity mapping
* boundary behavior near (S=0) and (S=1)

This module feeds directly into:

```
entropy → potential → expansion → structure
```

---

# ⚡ **3. Potential Module (`potential/`)**

### **`efc_potential.py`**

Implements the energy-flow potential:

* ( E_f = \rho (1 - S) )
* gradient of energy flow
* energy-flow lensing
* structure-driving components

This is the EFC-D subsystem.

---

# 🧩 **4. Validation Module (`validation/`)**

### **`efc_validation.py`**

Runs validation routines:

* SPARC rotation-curve comparisons
* entropy–radius profiles
* potential reconstruction

### **`sparc_io.py`**

Handles:

* SPARC dataset parsing
* formatting
* normalization
* error-handling

These support all validation scripts in `/scripts/`.

---

# 🌀 **5. Meta Simulation Layer (`meta/`)**

### **`cofield_simulator.py`**

Implements the **Co-Field Simulator (Fase 4)**:

* models interactions between energy flow and cognitive/reflective fields
* probes coupling between entropy fields and co-information
* simulates dual-field evolution under reflective feedback

This module connects:

* **meta-layer reasoning**
* **entropy dynamics**
* **energy-flow potential**
* **reflective feedback loops**

This is the most advanced experimental subsystem.

---

# 💡 **6. Light Boundary Module (`efc_light.py`)**

Standalone module for:

* light-speed boundary conditions
* entropy–light coupling
* C₀ dynamics
* early-time constraints

Serves the EFC-C₀ subsystem.

---

# 🛠️ **Development Notes**

### Imports

All modules are structured for:

```python
from src.efc.core import EFCModel
from src.efc.entropy import entropy_field
from src.efc.potential import compute_Ef
```

### Stability

Modules are kept:

* deterministic
* dependency-clean
* semantically aligned with `/schema/`
* traceable to `/theory/formal/`

---

# 🧪 **Running the Engine**

Example:

```python
from src.efc.core.efc_core import EFCModel

model = EFCModel()
results = model.run_entropy_evolution()
```

Or run the full validation pipeline:

```bash
python scripts/validate_efc.py
```

---

# 🧭 **Role of the Source Layer**

| Layer        | Function                                   |
| ------------ | ------------------------------------------ |
| **theory/**  | Mathematical definitions                   |
| **src/**     | Computation + simulation                   |
| **scripts/** | Automation, validation, plots              |
| **schema/**  | Machine-readable semantic structure        |
| **meta/**    | Reflective, cognitive, and co-field models |

`src/` is the **computational heart** of EFC.

---

# 🧩 **Summary**

The `/src/` directory contains:

* the full computational model
* entropy and energy-flow engines
* expansion dynamics
* structure evolution tools
* validation and dataset handlers
* co-field simulation
* boundary and light-speed modules

It transforms the EFC theory into a **working, testable, reproducible physical model**.

---
