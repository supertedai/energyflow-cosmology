#!/usr/bin/env python3
"""
run_sparc_validation.py
Kjør EFC–SPARC validering basert på SPARC Table1 (galakse-nivå).

Bruker:
- data/processed/sparc_table1.csv
- output/parameters.json
- src.efc_core.EFCModel / EFCParameters

Output:
- output/validation/sparc_comparison.json
- output/validation/sparc_vflat_scatter.png
- output/validation/sparc_NGC2403_comparison.png
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, UTC

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.efc_core import EFCModel, EFCParameters
from src.efc_validation import load_parameters



# -------------------------------------------------------------------
# PATH SETUP
# -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = ROOT / "output" / "parameters.json"
SPARC_CSV = ROOT / "data" / "processed" / "sparc_table1.csv"
OUT_DIR = ROOT / "output" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = OUT_DIR / "sparc_comparison.json"


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
        ).decode().strip()
    except Exception:
        return "unknown"


def compute_efc_vflat_for_galaxy(model: EFCModel, row: pd.Series) -> dict:
    """
    Beregn enkel EFC-basert "V_flat" for én galakse.

    Trinn:
    - bestem maks-radius r_max fra SPARC-data:
         R_max = RHI hvis tilgjengelig,
               = 5 * Rdisk,
               = 20 kpc (fallback)
    - sample r mellom 0.1 og R_max
    - beregn Ef(r) fra modellen
    - v_EFC(r) = sqrt(|Ef(r)|)
    - Vflat_model = snitt av de 10 ytterste punktene
    """

    rdisk = row.get("Rdisk", np.nan)
    rhi = row.get("RHI", np.nan)

    if not np.isnan(rhi) and rhi > 0:
        r_max = float(rhi)
    elif not np.isnan(rdisk) and rdisk > 0:
        r_max = float(5.0 * rdisk)
    else:
        r_max = 20.0

    r_max = max(2.0, min(r_max, 200.0))

    r = np.linspace(0.1, r_max, 100)
    x = np.stack([r, np.zeros_like(r), np.zeros_like(r)], axis=-1)

    state = model.compute_state(x)
    ef = np.array(state["Ef"])

    v_model = np.sqrt(np.abs(ef))
    vflat_model = float(np.mean(v_model[-10:]))

    return {
        "r_kpc": r.tolist(),
        "v_model": v_model.tolist(),
        "vflat_model": vflat_model,
    }


# -------------------------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------------------------

def main():
    if not SPARC_CSV.exists():
        raise FileNotFoundError(f"Fant ikke SPARC CSV: {SPARC_CSV}")

    print("[EFC-SPARC] Leser parametere...")
    params = load_parameters(PARAMS_PATH)
    model = EFCModel(params)

    print("[EFC-SPARC] Leser SPARC-tabell...")
    df = pd.read_csv(SPARC_CSV)

    for col in ["Galaxy", "Vflat", "Rdisk", "RHI"]:
        if col not in df.columns:
            print(f"[ADVARSEL] Kolonne mangler: {col}")

    records = []
    v_obs_list = []
    v_mod_list = []

    print("[EFC-SPARC] Beregner EFC V_flat for alle galakser...")

    for _, row in df.iterrows():
        galaxy = str(row.get("Galaxy", "")).strip()
        vflat_obs = row.get("Vflat", np.nan)

        if np.isnan(vflat_obs):
            continue

        try:
            efc_res = compute_efc_vflat_for_galaxy(model, row)
        except Exception as e:
            print(f"[EFC-SPARC] Feil for {galaxy}: {e}")
            continue

        v_model = efc_res["vflat_model"]

        v_obs_list.append(float(vflat_obs))
        v_mod_list.append(float(v_model))

        records.append({
            "Galaxy": galaxy,
            "Vflat_obs": float(vflat_obs),
            "Vflat_model": float(v_model),
            "Rdisk": float(row.get("Rdisk", np.nan)) if not np.isnan(row.get("Rdisk", np.nan)) else None,
            "RHI": float(row.get("RHI", np.nan)) if not np.isnan(row.get("RHI", np.nan)) else None,
            "Q": int(row.get("Q")) if not np.isnan(row.get("Q", np.nan)) else None,
        })

    # -------------------------------------------------------------------
    # GLOBAL STATS
    # -------------------------------------------------------------------
    v_obs = np.array(v_obs_list)
    v_mod = np.array(v_mod_list)

    if len(v_obs) > 0:
        residuals = v_mod - v_obs
        rmse = float(np.sqrt(np.mean(residuals**2)))
        bias = float(np.mean(residuals))
        corr = float(np.corrcoef(v_obs, v_mod)[0, 1]) if len(v_obs) > 1 else None
    else:
        rmse = bias = corr = None

    # -------------------------------------------------------------------
    # SCATTER PLOT
    # -------------------------------------------------------------------
    if len(v_obs) > 0:
        fig, ax = plt.subplots()
        ax.scatter(v_obs, v_mod, alpha=0.6)
        vmin = float(min(v_obs.min(), v_mod.min()))
        vmax = float(max(v_obs.max(), v_mod.max()))
        ax.plot([vmin, vmax], [vmin, vmax], "k--")

        ax.set_xlabel("V_flat (observasjon) [km/s]")
        ax.set_ylabel("V_flat (modell)")
        ax.set_title("EFC vs SPARC – V_flat")

        scatter_path = OUT_DIR / "sparc_vflat_scatter.png"
        fig.savefig(scatter_path, dpi=200)
        plt.close(fig)
        print(f"[EFC-SPARC] Scatter: {scatter_path}")

    # -------------------------------------------------------------------
    # EXAMPLE PLOT: NGC2403
    # -------------------------------------------------------------------
    example_name = "NGC2403"
    ex = df[df["Galaxy"].astype(str).str.strip() == example_name]

    if not ex.empty:
        row = ex.iloc[0]
        efc_res = compute_efc_vflat_for_galaxy(model, row)

        r = np.array(efc_res["r_kpc"])
        v_model = np.array(efc_res["v_model"])
        vflat_obs = float(row["Vflat"])

        fig, ax = plt.subplots()
        ax.plot(r, v_model)
        ax.axhline(vflat_obs, color="r", linestyle="--")

        ax.set_xlabel("r [kpc]")
        ax.set_ylabel("v(r)")
        ax.set_title(f"EFC vs SPARC – {example_name}")

        comp_path = OUT_DIR / f"sparc_{example_name}_comparison.png"
        fig.savefig(comp_path, dpi=200)
        plt.close(fig)

        print(f"[EFC-SPARC] Eksempelplot: {comp_path}")

    # -------------------------------------------------------------------
    # JSON OUTPUT
    # -------------------------------------------------------------------
    meta = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": get_git_commit(),
        "n_galaxies": len(records),
        "paths": {
            "sparc_csv": str(SPARC_CSV),
            "params": str(PARAMS_PATH),
            "output_dir": str(OUT_DIR),
        },
        "metrics": {
            "rmse": rmse,
            "bias": bias,
            "corr": corr,
        },
    }

    out_obj = {"meta": meta, "data": records}

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(out_obj, f, indent=2)

    print("[EFC-SPARC] Ferdig.")
    print(f"- JSON: {OUT_JSON}")
    print(f"- Galakser brukt: {len(records)}")
    if rmse is not None:
        print(f"- RMSE: {rmse:.3f}, bias: {bias:.3f}, corr: {corr:.3f}")


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":
    main()
