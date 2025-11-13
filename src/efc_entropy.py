"""
efc_entropy.py
<<<<<<< HEAD
Ekte EFC-S: Entropy field S(r) og gradient ∇S(r)
=======
EFC-S: Entropy field S(r) og gradient ∇S(r)
>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
"""

import numpy as np
from .efc_core import EFCParameters


def entropy_field(x, params: EFCParameters) -> np.ndarray:
    """
    EFC-S: S(r) = S0 * (1 - exp(-r/Ls))
    """
    r = np.linalg.norm(x, axis=-1)
    S0 = params.entropy_scale
    Ls = params.length_scale

    return S0 * (1.0 - np.exp(-r / Ls))


def entropy_gradient(x, params: EFCParameters) -> np.ndarray:
    """
<<<<<<< HEAD
    ∇S(r) = (S0/Ls) * exp(-r/Ls)
    Retur: gradient langs radial retning.
=======
    ∇S(r) = (S0/Ls) * exp(-r/Ls) * (r̂)
>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
    """
    r = np.linalg.norm(x, axis=-1)
    S0 = params.entropy_scale
    Ls = params.length_scale

    dSdr = (S0 / Ls) * np.exp(-r / Ls)

<<<<<<< HEAD
    # enhetvektor
=======
    # enhetvektor i radial retning
>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
    direction = np.zeros_like(x)
    mask = r > 0
    direction[mask] = x[mask] / r[mask][:, None]

    return dSdr[:, None] * direction
<<<<<<< HEAD
=======

>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
