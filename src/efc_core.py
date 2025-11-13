"""
efc_core.py – Hovedmodell med ekte EFC-ligninger.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class EFCParameters:
    entropy_scale: float      # S0
    length_scale: float       # Ls
    flow_constant: float      # k
    seed: int = 42


class EFCModel:
    def __init__(self, params: EFCParameters):
        self.params = params
        np.random.seed(params.seed)

    def compute_state(self, x):
        from .efc_entropy import entropy_field, entropy_gradient
        from .efc_potential import energy_flow_potential

        S = entropy_field(x, self.params)
        gradS = entropy_gradient(x, self.params)
        Ef = energy_flow_potential(x, self.params)

        return {"S": S, "gradS": gradS, "Ef": Ef}

    def rotation_velocity(self, r):
        """
        EFC-D rotasjon: v(r) = sqrt(|Ef(r)| * r)
        """
        x = np.stack([r, np.zeros_like(r), np.zeros_like(r)], axis=-1)
        Ef = self.compute_state(x)["Ef"]
        return np.sqrt(np.abs(Ef) * r)
