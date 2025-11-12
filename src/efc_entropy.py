"""
efc_entropy.py
--------------
Håndterer entropirelaterte beregninger i EFC, inkludert gradienter
og utvikling av entropi over tid og rom.
"""

import numpy as np

def compute_entropy_gradient(E, V):
    """
    Beregner lokal entropigradient ∇S ≈ ∂E/∂x / V
    """
    return np.gradient(E) / V

def entropy_evolution(S0, Ef, dt):
    """
    Enkel modell for entropiutvikling:
    dS/dt ∝ Ef  => S(t+1) = S(t) + α * Ef * dt
    """
    alpha = 1e-3
    return S0 + alpha * Ef * dt
