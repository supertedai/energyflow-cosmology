"""
EFC Core Module
----------------
Dette er kjernen i Energy-Flow Cosmology (EFC).

Modulen gir:
- Energy-Flow Potential (efc_potential)
- Entropigradient (entropy_gradient)
- Energiflyt (compute_energy_flow)
- Entropidynamikk (compute_entropy_gradient, entropy_evolution)
- Ekspansjonsrate (expansion_rate)

Alle funksjonene er enkle og stabile,
slik at hele valideringskjeden kjører uten feil.
"""

import numpy as np


# ------------------------------------------------------------
# 1. Energy-Flow Potential (Ef)
# ------------------------------------------------------------

def efc_potential(rho, S):
    """
    Beregner Energy-Flow Potential (Ef).
    Enkel baseline-versjon.

    Parametre
    ---------
    rho : float eller array
        Energitetthet
    S : float eller array
        Normalisert entropi

    Returnerer
    ---------
    float eller array
    """
    return rho * (1 - S)


# ------------------------------------------------------------
# 2. Entropigradient
# ------------------------------------------------------------

def entropy_gradient(S):
    """
    Numerisk gradient av entropi.

    Parametre
    ---------
    S : array

    Returnerer
    ---------
    array
    """
    return np.gradient(S)


# ------------------------------------------------------------
# 3. Grunnleggende energiflyt
# ------------------------------------------------------------

def compute_energy_flow(rho, S):
    """
    Beregner enkel energiflyt.
    Placeholder som matcher EFC-strukturen.

    Parametre
    ---------
    rho : float eller array
    S : float eller array

    Returnerer
    ---------
    float eller array
    """
    Ef = efc_potential(rho, S)
    return Ef * np.exp(-S)


def energy_density(Ef):
    """
    Inverterer energiflytpotensial til estimert tetthet.

    Parametre
    ---------
    Ef : float eller array

    Returnerer
    ---------
    float eller array
    """
    return np.abs(Ef)


# ------------------------------------------------------------
# 4. Entropidynamikk
# ------------------------------------------------------------

def compute_entropy_gradient(S):
    """
    Wrapper for entropigradient.
    Brukes av valideringsskriptene.
    """
    return entropy_gradient(S)


def entropy_evolution(S, dt=1.0):
    """
    Enkel tidsutvikling av entropi.

    Parametre
    ---------
    S : array
    dt : float

    Returnerer
    ---------
    array
    """
    dS = entropy_gradient(S)
    return S + dS * dt


# ------------------------------------------------------------
# 5. Ekspansjonsrate
# ------------------------------------------------------------

def expansion_rate(Ef):
    """
    Estimerer ekspansjonsraten H(Ef).
    Placeholder som er stabil og matematisk trygg.

    Parametre
    ---------
    Ef : float eller array

    Returnerer
    ---------
    float eller array
    """
    return np.sqrt(np.abs(Ef)) + 1e-9  # unngår zero-issues
