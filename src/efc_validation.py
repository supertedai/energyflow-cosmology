"""
efc_validation.py
Ekte EFC-basert validering mot rotasjonskurver.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from .efc_core import EFCModel


def rotation_curve_efc(model: EFCModel, r_max: float = 30.0, n: int = 200):
    """
    EFC rotasjonskurve:
    v(r) = sqrt(|Ef(r)| * r)
    """
    r = np.linspace(0.1, r_max, n)
    v = model.rotation_velocity(r)
    return r, v


def validate_rotation_curve(model: EFCModel, outdir: Path):
    """
    Lag figurer + JSON-data for rotasjonskurven.
    """
    outdir.mkdir(parents=True, exist_ok=True)

    r, v = rotation_curve_efc(model)

    # Plot
    fig, ax = plt.subplots()
    ax.plot(r, v, label="EFC rotation", linewidth=2)
    ax.set_xlabel("r (kpc)")
    ax.set_ylabel("v(r) (km/s)")
    ax.set_title("EFC Rotation Curve")
    ax.legend()
    fig.savefig(outdir / "rotation_curve.png", dpi=200)
    plt.close(fig)

    # JSON-data
    data = {
        "r": r.tolist(),
        "v_efc": v.tolist(),
    }

    return data
