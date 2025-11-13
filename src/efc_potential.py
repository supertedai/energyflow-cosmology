"""
efc_potential.py
<<<<<<< HEAD
EFC-D: Energy-flow potential fra ∇S.
=======
EFC-D: Energy-flow potential fra entropigradient.
>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
"""

import numpy as np
from .efc_core import EFCParameters
from .efc_entropy import entropy_gradient


def energy_flow_potential(x, params: EFCParameters) -> np.ndarray:
    """
    Ef(r) = -k * |∇S(r)|
    """
    gradS = entropy_gradient(x, params)
<<<<<<< HEAD
    mag = np.linalg.norm(gradS, axis=-1)

    k = params.flow_constant
    return -k * mag
=======
    magnitude = np.linalg.norm(gradS, axis=-1)

    k = params.flow_constant
    return -k * magnitude

>>>>>>> 6fe47b1 (Add complete SPARC validation pipeline + parsers + EFC baseline integration)
