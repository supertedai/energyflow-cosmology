"""
Quick sanity check for c(S) behaviour.

Run with:
    python3 scripts/test_c_entropy.py
"""

import numpy as np
from src.efc_light import c_of_S


def main():
    # Sample S from slightly before S0 to slightly after S1
    S_vals = np.linspace(-0.2, 1.2, 8)
    c_vals = c_of_S(S_vals)

    print("S\tc(S) [m/s]")
    for S, c in zip(S_vals, c_vals):
        print(f"{S:.2f}\t{c:.3e}")

    # Rough qualitative expectations:
    # - mid-range S ~ 0.5 → c ~ c0
    # - near S0 and S1 → c > c0
    S_mid = 0.5
    c_mid = c_of_S(S_mid)
    print("\nMid-range S=0.5 → c(S) ≈", f"{c_mid:.3e}", "m/s")


if __name__ == "__main__":
    main()
