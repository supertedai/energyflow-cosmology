"""
efc_potential.py
EFC-D: Energy-flow potential fra ∇S.
"""

import numpy as np
from .efc_core import EFCParameters
from .efc_entropy import entropy_gradient


def energy_flow_potential(x, params: EFCParameters) -> np.ndarray:
    """
    Ef(r) = -k * |∇S(r)|
    """
    gradS = entropy_gradient(x, params)
    mag = np.linalg.norm(gradS, axis=-1)

    k = params.flow_constant
    return -k * mag
