"""
efc_validation.py
Ekte EFC-basert validering mot rotasjonskurver.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from ..core.efc_core import EFCModel


def rotation_curve_efc(model: EFCModel, r_max: float = 30.0, n: int = 200):
    """
    EFC rotasjonskurve:
    v(r) = sqrt(|Ef(r)| * r)
    """
def load_parameters(path):
    """
    Leser output/parameters.json og returnerer et EFCParameters-objekt.
    """
    import json
    from ..core.efc_core import EFCParameters

    with open(path, "r") as f:
        cfg = json.load(f)

    # Forventer format:
    # { "efc_parameters": { ... } }
    return EFCParameters(**cfg["efc_parameters"])



def rotation_curve_efc(model: EFCModel, r_max: float = 30.0, n: int = 200):
    r = np.linspace(0.1, r_max, n)
    v = model.rotation_velocity(r)
    return r, v


def validate_rotation_curve(model: EFCModel, outdir: Path):
    """
    Lag figurer + JSON-data for rotasjonskurven.
    """
    outdir.mkdir(parents=True, exist_ok=True)

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
    from .sparc_io import load_rotation_curve
import json

def compare_with_sparc(model: EFCModel, sparc_root: Path, galaxy: str, outdir: Path):
    """
    Laster én SPARC-galakse og lager sammenlikning EFC vs. Vobs.
    Forventer filer under data/sparc/<GAL>/.../*.txt (standard SPARC ZIP-struktur).
    """
    gal_dir = sparc_root / galaxy
    if not gal_dir.exists():
        raise FileNotFoundError(f"Fant ikke katalog for '{galaxy}' under {sparc_root}")

    # Heuristikk: finn en fil som inneholder 'rotmod' eller 'rot' og slutter på .txt
    candidates = sorted(list(gal_dir.rglob("*.txt")))
    if not candidates:
        raise FileNotFoundError(f"Ingen .txt i {gal_dir}")
    rc_file = None
    for p in candidates:
        name = p.name.lower()
        if "rotmod" in name or "rot" in name:
            rc_file = p
            break
    if rc_file is None:
        rc_file = candidates[0]

    R, Vobs, eV = load_rotation_curve(rc_file)

    # Modellprediksjon på samme radii
    v_efc = model.rotation_velocity(R)

    # Plot
    outdir.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.errorbar(R, Vobs, yerr=eV, fmt="o", ms=3, alpha=0.8, label=f"SPARC: {galaxy}")
    ax.plot(R, v_efc, lw=2, label="EFC")
    ax.set_xlabel("R (kpc)")
    ax.set_ylabel("V (km/s)")
    ax.set_title(f"EFC vs SPARC – {galaxy}")
    ax.legend()
    fig.savefig(outdir / f"sparc_{galaxy}_comparison.png", dpi=200)
    plt.close(fig)

    # JSON
    data = {
        "galaxy": galaxy,
        "rc_file": str(rc_file),
        "R_kpc": R.tolist(),
        "Vobs_kms": Vobs.tolist(),
        "eV_kms": eV.tolist(),
        "Vefc_kms": v_efc.tolist()
    }
    (outdir / f"sparc_{galaxy}_comparison.json").write_text(json.dumps(data, indent=2))
    return data

    return {"r": r.tolist(), "v_efc": v.tolist()}
