# 🧠 Energy-Flow Cosmology — Unified Module Architecture
**Folder:** `/theory/architecture.md`  
**Last updated:** 2025-11-13  

This document provides a complete overview of the internal module system powering the Energy-Flow Cosmology (EFC) codebase.  
The architecture follows a thermodynamic logic:

- Core definitions (parameters & model)
- Entropy field
- Energy-flow potential
- Validation layer

Everything emerges from first-principles relations between **entropy gradients**, **energy flow**, and **observables**.

---

# 🔷 1. Top-Level Structure
src/
└── efc/
├── core/
│ └── efc_core.py
├── entropy/
│ └── efc_entropy.py
├── potential/
│ └── efc_potential.py
├── validation/
│ └── efc_validation.py
└── init.py

Each folder corresponds to one conceptual EFC layer:

| Layer | Purpose | Mathematical role |
|-------|---------|--------------------|
| `core` | Model definition | EFCParameters, state vector, Ef, v(r) |
| `entropy` | Entropy field | ∇S, S(x) |
| `potential` | Energy-flow potential | Ef = ρ (1 − S) |
| `validation` | Observational comparison | SPARC, DESI, JWST |
| `__init__` | Public API | Stable import surface |

---

# 🔷 2. Core Layer

Implements the general EFC model, with:

- `EFCModel`
- `EFCParameters`
- `compute_state`
- `rotation_velocity`

Logical role:  
Combine entropy + energy flow → observable predictions.

---

# 🔷 3. Entropy Layer

Provides:

- `entropy_field(x)`
- `entropy_gradient(x)`

Defines the thermodynamic geometry of the system.

---

# 🔷 4. Potential Layer

Implements:

Ef = ρ (1 − S)

Functions:

- `compute_energy_flow(rho, S)`
- `energy_density(mass, volume)`
- `energy_flow_rate(Ef, t)`

This is the driving energy-flow potential in EFC-D.

---

# 🔷 5. Validation Layer

Tools for benchmarking EFC:

- `rotation_curve_efc`
- `validate_rotation_curve`
- `compare_with_sparc`
- `load_parameters`

Outputs plots + JSON for empirical comparison.

---

# 🔷 6. Public API

`src/__init__.py` exposes a clean import interface:

```python
from src import (
    EFCModel,
    EFCParameters,
    compute_energy_flow,
    entropy_gradient,
    entropy_field,
)

🔷 7. Design Principles

Thermodynamic hierarchy

Clear separation of concerns

Stable API exposure

Validation-first architecture

🔷 8. Planned Modules
Module	Role
efc/cosmology	H(z), E(z), Ef(z)
efc/lensing	Weak lensing predictions
efc/jwst	Early galaxies
efc/synthesis	Unified pipelines
