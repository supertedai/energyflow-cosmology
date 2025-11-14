import numpy as np
from src.efc_light import c_of_S

profiles = {
    "linear": np.linspace(0.0, 1.0, 10),
    "dip": np.array([0.0, 0.2, 0.5, 0.2, 0.0]),
    "double_peak": np.array([0.0, 0.8, 0.2, 0.8, 0.0])
}

for name, S in profiles.items():
    c_vals = c_of_S(S)
    print("\n---", name, "---")
    for s, c in zip(S, c_vals):
        print(f"S={s:.3f} -> c={c:.3e}")
