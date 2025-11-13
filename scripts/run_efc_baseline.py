"""
run_efc_baseline.py – kjør ekte EFC-baseline.
"""

import json
from pathlib import Path
from datetime import datetime
import subprocess

from src.efc_core import EFCModel, EFCParameters
from src.efc_validation import validate_rotation_curve


ROOT = Path(__file__).resolve().parents[1]
PARAMS_PATH = ROOT / "output" / "parameters.json"
FIG_DIR = ROOT / "output" / "figures"
VAL_DIR = ROOT / "output" / "validation"
META_PATH = ROOT / "output" / "run_metadata.json"


def load_parameters():
    with PARAMS_PATH.open() as f:
        cfg = json.load(f)
    return EFCParameters(**cfg["efc_parameters"])


def get_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def main():
    params = load_parameters()
    model = EFCModel(params)

    # --- Validation ---
    rot_data = validate_rotation_curve(model, VAL_DIR)
    (VAL_DIR / "rotation_curve.json").write_text(
        json.dumps(rot_data, indent=2)
    )

    # --- Metadata ---
    meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_commit": get_git_commit(),
        "parameters_file": str(PARAMS_PATH),
        "validation_dir": str(VAL_DIR),
        "figures_dir": str(FIG_DIR),
    }

    META_PATH.write_text(json.dumps(meta, indent=2))

    print("EFC baseline validation complete.")
    print(f"- rotation curve: {VAL_DIR/'rotation_curve.json'}")
    print(f"- metadata: {META_PATH}")


if __name__ == "__main__":
    main()
