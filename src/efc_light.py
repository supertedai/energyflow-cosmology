"""
EFC Light Propagation Utilities

Provisional implementation of c(S) for exploring s0–s1 endpoint behaviour.
This is NOT a final physical model, but a testing scaffold.
"""

import numpy as np


def c_of_S(S, c0=3.0e8, S0=0.0, S1=1.0, a0=0.4, a1=0.4):
    """
    Toy model for effective speed of light as a function of entropy S.

    Idea:
        - c is approximately c0 in mid-range S
        - c increases near both endpoints S0 (s0) and S1 (s1)
        - no divergences (smooth asymptotic bumps)

    Parameters
    ----------
    S : float or array-like
        Entropy coordinate (normalized between S0 and S1 for now).
    c0 : float
        Baseline speed (approx current measured c in mid-range).
    S0 : float
        Low-entropy endpoint (s0).
    S1 : float
        High-entropy endpoint (s1).
    a0, a1 : float
        Amplitudes of the endpoint enhancements.

    Returns
    -------
    c_eff : float or np.ndarray
        Effective propagation speed.
    """
    S = np.asarray(S, dtype=float)

    # Normalized distance from each endpoint
    d0 = (S - S0)
    d1 = (S - S1)

    # Smooth bump functions near S0 and S1
    bump0 = a0 / (1.0 + d0**2)
    bump1 = a1 / (1.0 + d1**2)

    factor = 1.0 + bump0 + bump1
    return c0 * factor

