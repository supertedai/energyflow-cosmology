#!/usr/bin/env python3
"""
Henter og pakker ut SPARC Rotmod_LTG.zip til data/sparc/.
Kilde: http://astroweb.cwru.edu/SPARC/ (Lelli+2016, AJ 152, 157)
"""
import io, zipfile, os, sys
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "sparc"
URL = "http://astroweb.cwru.edu/SPARC/Rotmod_LTG.zip"

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print(f"[SPARC] Laster ned: {URL}")
    with urllib.request.urlopen(URL) as resp:
        data = resp.read()
    print("[SPARC] Pakker ut...")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(OUTDIR)
    # Lag enkel manifest av galaksenavn (mappenavn)
    gals = sorted({p.parts[-2] for p in OUTDIR.rglob("*.txt")})
    (OUTDIR / "manifest.txt").write_text("\n".join(gals) + "\n")
    print(f"[SPARC] OK. Filer i: {OUTDIR}")
    print(f"[SPARC] Antall galakser: {len(gals)}")
    print(f"[SPARC] manifest: {OUTDIR/'manifest.txt'}")

if __name__ == "__main__":
    sys.exit(main())
