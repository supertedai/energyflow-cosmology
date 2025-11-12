"""
efc_core.py
-----------
Grunnmodul for EFC. Inneholder de sentrale ligningene og 
relasjonene mellom energitetthet (ρ), entropi (S) og energiflyt (Ef).
"""

import numpy as np

# Fysiske konstanter
c = 3.0e8             # lyshastighet (m/s)
kB = 1.380649e-23     # Boltzmanns konstant (J/K)
G = 6.67430e-11       # gravitasjonskonstant (m³/kg/s²)

def efc_potential(rho, S):
    """Energiflytpotensial: Ef = ρ * (1 - S)"""
    return rho * (1 - S)

def entropy_gradient(E, V):
    """Entropigradient ∇S = ∂S/∂x ~ ∂E/∂x / V"""
    return np.gradient(E) / V

def expansion_rate(Ef, S):
    """Ekspansjonsrate ~ H, basert på energiflyt og entropi."""
    return np.sqrt(np.abs(Ef) / (1 - S + 1e-9))

if __name__ == "__main__":
    rho = np.linspace(1e-27, 1e-24, 100)
    S = np.linspace(0.1, 0.9, 100)
    Ef = efc_potential(rho, S)
    H = expansion_rate(Ef, S)
    print("EFC baseline H:", np.mean(H))
