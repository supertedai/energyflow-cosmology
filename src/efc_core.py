"""
efc_core.py
Kjernemodeller for Energy-Flow Cosmology.
"""

from dataclasses import dataclass
import numpy as np
from pathlib import Path
import json


@dataclass
class EFCParameters:
    entropy_scale: float
    length_scale: float
    flow_constant: float
    velocity_scale: float
    seed: int = 42
    grid_resolution: int = 32
    time_steps: int = 10


class EFCModel:
    def __init__(self, params: EFCParameters):
        self.params = params
        np.random.seed(params.seed)

    def compute_state(self, x):
        """
        Returnerer:
        {
            "Ef": Ef(r),
            "gradS": ∇S(r)
        }
        """
        Ef = self._compute_Ef(x)
        gradS = self._compute_entropy_gradient(x)
        return {
            "Ef": Ef,
            "gradS": gradS,
        }

    def _compute_Ef(self, x):
        from .efc_potential import compute_energy_flow

        rho = 1e-24 * np.ones(x.shape[0])
        S = 0.5 * np.ones(x.shape[0])

        return compute_energy_flow(rho, S)

    def _compute_entropy_gradient(self, x):
        from .efc_entropy import entropy_gradient
        return entropy_gradient(x, self.params)


def load_parameters(path: Path) -> EFCParameters:
    """
    Leser output/parameters.json og returnerer EFCParameters.
    """
    with open(path, "r") as f:
        cfg = json.load(f)
    return EFCParameters(**cfg["efc_parameters"])
