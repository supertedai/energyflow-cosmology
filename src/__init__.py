"""
Energy-Flow Cosmology (EFC) Core Package
----------------------------------------

Dette er kjernemodulen for EFC – et termodynamisk rammeverk
som beskriver universets struktur, dynamikk og kognisjon
gjennom energiflyt (Ef) og entropigradient (∇S).
"""

__version__ = "1.0.0"
__author__ = "Morten Magnusson"
__license__ = "CC-BY-4.0"

# Importer alt direkte fra efc_core
from .efc_core import (
    efc_potential,
    entropy_gradient,
    expansion_rate,
    compute_energy_flow,
    energy_density,
    compute_entropy_gradient,
    entropy_evolution,
)

__all__ = [
    "efc_potential",
    "entropy_gradient",
    "expansion_rate",
    "compute_energy_flow",
    "energy_density",
    "compute_entropy_gradient",
    "entropy_evolution",
]
