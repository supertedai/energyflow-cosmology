"""
Energy-Flow Cosmology (EFC) Core Package
----------------------------------------

Dette er kjernemodulen for EFC – et termodynamisk rammeverk
som beskriver universets struktur, dynamikk og bevissthet
gjennom energiflyt (Ef) og entropigradient (∇S).

Modulen gir:
- Grunnleggende beregningsfunksjoner (efc_core)
- Energiflytpotensial og feltrelasjoner (efc_potential)
- Entropigradient og systemdynamikk (efc_entropy)
- Grensesnitt mot validerings- og visualiseringsverktøy

Eksempel:
    from src import efc_core

    rho = 1e-26  # energitetthet (kg/m³)
    S = 0.4      # normalisert entropi
    Ef = efc_core.efc_potential(rho, S)
    print(Ef)
"""

__version__ = "1.0.0"
__author__ = "Morten Magnusson"
__license__ = "CC-BY-4.0"

# Importér kjernemoduler
from .efc_core import efc_potential, entropy_gradient, expansion_rate
from .efc_potential import compute_energy_flow, energy_density
from .efc_entropy import compute_entropy_gradient, entropy_evolution

# Tilgjengelige symboler ved import *
__all__ = [
    "efc_potential",
    "entropy_gradient",
    "expansion_rate",
    "compute_energy_flow",
    "energy_density",
    "compute_entropy_gradient",
    "entropy_evolution",
]
