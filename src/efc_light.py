import numpy as np

def c_of_S(S, c0=3.0e8, S0=0.0, S1=1.0, a_edge=0.6):
    """
    Symmetric endpoint model for effective speed of light as a function of entropy S.

    Behaviour:
        - c is lowest around the midpoint between S0 and S1
        - c increases smoothly towards both endpoints: s0 (S=S0) and s1 (S=S1)
        - No divergences, no discontinuities

    Parameters
    ----------
    S : float or array-like
        Entropy coordinate.
    c0 : float
        Baseline speed (approx measured speed of light in mid-range).
    S0 : float
        Low-entropy endpoint (s0).
    S1 : float
        High-entropy endpoint (s1).
    a_edge : float
        Strength of c-increase near the endpoints. a_edge > 0.

    Returns
    -------
    c_eff : float or np.ndarray
        Effective propagation speed of light.
    """
    S = np.asarray(S, dtype=float)

    # Midpoint between endpoints (lowest c)
    Smid = 0.5 * (S0 + S1)
    half_width = 0.5 * (S1 - S0) if S1 != S0 else 1.0

    # Normalized coordinate: -1 at S0, 0 at midpoint, +1 at S1
    x = (S - Smid) / half_width

    # Minimum at the middle, higher at both edges
    factor = 1.0 + a_edge * (x ** 2)

    return c0 * factor

