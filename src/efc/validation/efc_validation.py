import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from ..core.efc_core import EFCModel, EFCParameters


def load_parameters(path):
    """
    Load parameters.json and return EFCParameters object.
    """
    with open(path, "r") as f:
        cfg = json.load(f)
    return EFCParameters(**cfg)


def rotation_curve_efc(model: EFCModel, r_max: float = 30.0, n: int = 200):
    """
    Compute EFC rotation curve: v(r) = sqrt(|Ef(r)| * r)
    """
    r = np.linspace(0.1, r_max, n)
    v = model.rotation_velocity(r)
    return r, v


def validate_rotation_curve(model: EFCModel, outdir: Path):
    """
    Generate figure + JSON for rotation curve.
    """
    outdir.mkdir(parents=True, exist_ok=True)

    r, v = rotation_curve_efc(model)

    # Plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(r, v, label="EFC rotation curve")
    ax.set_xlabel("r (kpc)")
    ax.set_ylabel("v (km/s)")
    ax.legend()

    fig.savefig(outdir / "rotation_curve.png", dpi=200)
    plt.close(fig)

    # JSON output
    data = {"r": r.tolist(), "v_efc": v.tolist()}
    (outdir / "rotation_curve.json").write_text(json.dumps(data, indent=2))
    return data


def compare_with_sparc(model: EFCModel, sparc_root: Path, galaxy: str, outdir: Path):
    """
    Compare EFC rotation curve to SPARC data for a given galaxy.
    """
    outdir.mkdir(parents=True, exist_ok=True)

    # Load SPARC rotation curve
    sparc_file = sparc_root / f"{galaxy}.csv"
    raw = np.genfromtxt(sparc_file, delimiter=",", names=True)
    r_data = raw["R"]
    v_data = raw["V"]

    # EFC prediction
    r_efc, v_efc = rotation_curve_efc(model, r_max=max(r_data) * 1.1)

    # Plot comparison
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(r_data, v_data, s=20, label="SPARC data")
    ax.plot(r_efc, v_efc, label="EFC prediction")
    ax.set_xlabel("r (kpc)")
    ax.set_ylabel("v (km/s)")
    ax.legend()

    fig.savefig(outdir / f"sparc_{galaxy}_comparison.png", dpi=200)
    plt.close(fig)

    # JSON output
    data = {
        "galaxy": galaxy,
        "r_data": r_data.tolist(),
        "v_data": v_data.tolist(),
        "r_efc": r_efc.tolist(),
        "v_efc": v_efc.tolist(),
    }

    (outdir / f"sparc_{galaxy}_comparison.json").write_text(
        json.dumps(data, indent=2)
    )

    return data
