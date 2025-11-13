"""
EFC Core Functions
------------------
Dette er kjernen av Energy-Flow Cosmology.

Funksjonene her brukes av alle valideringsscript (JWST, DESI, SPARC, CMB).
"""

import numpy as np


def efc_potential(Ef, S):
    """
    Energy-Flow Potential (Ef).
    Placeholder-implementasjon.

    Parametre
    ---------
    Ef : float eller array
    S  : float eller array

    Returnerer
    ---------
    float eller array
    """
    return Ef - S


def entropy_gradient(S):
    """
    Entropy Gradient (∇S).
    Forenklet numerisk gradient.

    Parametre
    ---------
    S : array

    Returnerer
    ---------
    array
    """
    return np.gradient(S)


def expansion_rate(Ef):
    """
    Expansion Rate H(Ef).
    Forenklet placeholder.

    Parametre
    ---------
    Ef : float eller array

    Returnerer
    ---------
    float eller array
    """
    return np.sqrt(np.abs(Ef))
