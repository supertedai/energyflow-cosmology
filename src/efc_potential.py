"""
efc_potential.py
----------------
Definerer energiflytpotensialet (Ef) og relaterte hjelpefunksjoner.
"""

import numpy as np

def compute_energy_flow(rho, S):
    """
    Beregner energiflytpotensialet (Ef).
    Ef = ρ * (1 - S)
    """
    return rho * (1 - S)

def energy_density(mass, volume):
    """Enkel energitetthet (ρ = m/V)."""
    return mass / volume

def energy_flow_rate(Ef, t):
    """Estimert endring i Ef over tid."""
    return np.gradient(Ef, t)
