# **EFC Source Code — Computational Engine**

The `src/` directory contains the full computational implementation of Energy-Flow Cosmology (EFC).
This is the engine that computes:

* entropy fields
* energy-flow potential
* expansion-rate behaviour
* structure-driving gradients
* validation metrics
* light-boundary dynamics

It is the executable translation of the mathematics defined in:

```
theory/formal/efc_formal_spec.tex
```

---

# **Directory Structure**

```
src/
├── __init__.py
│
├── efc_light.py                # s₀–s₁ light / entropy boundary module
│
├── efc/                        # Main EFC Python package
│   ├── core/                   # Core model logic
│   │   └── efc_core.py
│   │
│   ├── entropy/                # Entropy-field dynamics
│   │   └── efc_entropy.py
│   │
│   ├── potential/              # Energy-flow potential
│   │   └── efc_potential.py
│   │
│   ├── validation/             # Validation utilities
│   │   └── efc_validation.py
│   │
│   └── meta/                   # Meta-simulation layer (co-field abstractions)
│       └── __init__.py
```

*(Note: you removed `cofield_simulator.py`. Repo is clean.)*

---

# **1. Core Module — `core/efc_core.py`**

This is the central numerical engine.

Implements:

* entropy → energy-flow → expansion pipeline
* base equations from EFC-S and EFC-D
* numerical integration
* shared computation utilities
* analytic–numerical hybrid routines

The model exposed here is what scripts and notebooks call.

---

# **2. Entropy Module — `entropy/efc_entropy.py`**

Implements the entropy-field evolution:

* ( S(r) )
* ( \nabla S )
* entropy-capacity mapping
* behaviour near low-S and high-S
* structural entropy profiles for halos

Feeds directly into:

```
entropy → potential → expansion → structure
```

---

# **3. Potential Module — `potential/efc_potential.py`**

Implements the EFC energy-flow potential:

[
E_f = \rho(1 - S)
]

Includes:

* Ef computation
* Ef gradients
* flow-driven curvature
* structure-supporting behaviour
* EFC-D relations

This module is used by validation, notebooks, and plots.

---

# **4. Validation Module — `validation/efc_validation.py`**

Utilities for comparing EFC predictions to data.

Used by:

```
scripts/run_sparc_validation.py
scripts/validate_efc.py
notebooks/EFC_vs_LCDM.ipynb
```

Implements:

* SPARC rotation curve comparison
* entropy-radius profile checks
* Ef-based velocity reconstruction
* local/global curve extraction

All plots stored under:

```
output/validation/
```

---

# **5. Meta Simulation Layer — `src/efc/meta/`**

Currently contains:

```
src/efc/meta/__init__.py
```

This provides the namespace for future:

* co-field simulations
* reflective-feedback models
* entropy-information coupling models

It ties into:

```
meta/meta-process/
meta/symbiosis/
meta/cognition/
```

but has no active simulation code yet — repo is clean and consistent.

---

# **6. Light Boundary Module — `efc_light.py`**

Implements:

* s₀–s₁ light boundary
* light-speed regulation inside EFC
* entropy–light coupling
* early-time dynamics (EFC-C₀ subsystem)

Used by:

* entropy constraints
* expansion-rate constraints
* light-speed thermodynamic boundary models
* notebooks

---

# **Development Notes**

## **Imports**

Modules follow clean import structure:

```python
from src.efc.core.efc_core import EFCModel
from src.efc.entropy.efc_entropy import entropy_field
from src.efc.potential.efc_potential import compute_Ef
```

Everything is:

* deterministic
* dependency-minimal
* semantically aligned with `/schema/`
* traceable to definitions in `/theory/formal/`

---

# **Running the Engine**

### Full validation:

```
python scripts/validate_efc.py
```

### Baseline model:

```
python scripts/run_efc_baseline.py
```

### Python direct use:

```python
from src.efc.core.efc_core import EFCModel

model = EFCModel()
results = model.run()
```

---

# **Role of the Source Layer**

| Layer        | Function                                |
| ------------ | --------------------------------------- |
| **theory/**  | mathematical definitions                |
| **src/**     | computation and simulation              |
| **scripts/** | validation, automation, reproducibility |
| **schema/**  | semantic mapping                        |
| **meta/**    | reflective and cognitive process        |

`src/` is the operational core — the part that *produces predictions*.

---

# **Summary**

The `src/` directory provides:

* entropy field computation
* energy-flow potential
* expansion-rate behaviour
* structure-affecting gradients
* validation utilities
* light-boundary dynamics

It converts the EFC theory into a working, testable numerical model.

System-aligned. Repo-correct. Zero inconsistens.

---
