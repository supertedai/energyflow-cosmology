import os
import json
import pandas as pd
from datetime import datetime

RAW_PATH = "data/external/sparc/sparc_table1.mrt"
OUT_CSV = "data/processed/sparc_table1.csv"
OUT_JSON = "data/processed/sparc_table1.json"


# -------------------------------------------------------------
# 1. Load MRT file (raw SPARC table)
# -------------------------------------------------------------
def load_mrt_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Finner ikke SPARC MRT fil: {path}")

    with open(path, "r", encoding="utf-8") as f:
        text = f.readlines()

    # fjern metadata header, behold kun data-linjer
    data_lines = [ln.rstrip("\n") for ln in text if ln[:5].strip() not in ["Byte", "-----", "Note", "====", "----"]]
    data_lines = [ln for ln in data_lines if len(ln.strip()) > 0 and ln[0] != "="]

    return data_lines


# -------------------------------------------------------------
# 2. Parse fixed-width SPARC table using known column widths
#    (fra byte-tabellen i SPARC dokumentasjonen)
# -------------------------------------------------------------
COLS = [
    ("Galaxy", (0, 11)),
    ("T", (11, 13)),
    ("D", (13, 19)),
    ("e_D", (19, 24)),
    ("f_D", (24, 26)),
    ("Inc", (26, 30)),
    ("e_Inc", (30, 34)),
    ("L36", (34, 41)),
    ("e_L36", (41, 48)),
    ("Reff", (48, 53)),
    ("SBeff", (53, 61)),
    ("Rdisk", (61, 66)),
    ("SBdisk", (66, 74)),
    ("MHI", (74, 81)),
    ("RHI", (81, 86)),
    ("Vflat", (86, 91)),
    ("e_Vflat", (91, 96)),
    ("Q", (96, 99)),
    ("Ref", (99, 113)),
]


def parse_sparc_lines(lines):
    rows = []
    for ln in lines:
        if len(ln) < 20:
            continue

        entry = {}
        for col, (a, b) in COLS:
            raw = ln[a:b].strip()
            entry[col] = raw

        rows.append(entry)

    return pd.DataFrame(rows)


# -------------------------------------------------------------
# 3. Convert numeric columns
# -------------------------------------------------------------
def convert_numeric(df):
    numeric_cols = [
        "T", "D", "e_D", "f_D", "Inc", "e_Inc", "L36", "e_L36",
        "Reff", "SBeff", "Rdisk", "SBdisk", "MHI", "RHI",
        "Vflat", "e_Vflat", "Q"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# -------------------------------------------------------------
# 4. Save output
# -------------------------------------------------------------
def save_outputs(df):
    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(OUT_CSV, index=False)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "source": "SPARC Table1.mrt",
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "n_galaxies": len(df)
            },
            "data": df.to_dict(orient="records")
        }, f, indent=2)

    print(f"[OK] Lagret CSV → {OUT_CSV}")
    print(f"[OK] Lagret JSON → {OUT_JSON}")


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    print("[SPARC] Leser rådata...")
    lines = load_mrt_file(RAW_PATH)

    print("[SPARC] Parser tabell...")
    df = parse_sparc_lines(lines)

    print("[SPARC] Konverterer numeriske felt...")
    df = convert_numeric(df)

    print("[SPARC] Lagre filer...")
    save_outputs(df)

    print(f"[SPARC] Ferdig. Galakser: {len(df)}")
