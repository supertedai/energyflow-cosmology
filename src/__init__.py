"""
Energy-Flow Cosmology (EFC) Core Package
----------------------------------------

Dette er kjernemodulen for EFC – et termodynamisk rammeverk som beskriver
universets struktur, dynamikk og kognisjon gjennom energiflyt (Ef)
og entropigradient (∇S).

Alle kjernefunksjoner ligger nå i efc_core.py for maksimal stabilitet.
"""

__version__ = "1.0.0"
__author__ = "Morten Magnusson"
__license__ = "CC-BY-4.0"


# Importer alt fra efc_core (ren og stabil struktur)
from .efc_core import (
    efc_potential,
    entropy_gradient,
    expansion_rate,
    compute_energy_flow,
    energy_density,
    compute_entropy_gradient,
    entropy_evolution,
)


# Eksponer symbolene
__all__ = [
    "efc_potential",
    "entropy_gradient",
    "expansion_rate",
    "compute_energy_flow",
    "energy_density",
    "compute_entropy_gradient",
    "entropy_evolution",
]
