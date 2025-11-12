"""
plot_results.py
----------------
Samler alle valideringsplott (JWST, DESI, SPARC) i ett felles “dashboard”-bilde.
Kjøres etter at validate_efc.py er brukt for alle tre datasettene.
"""

import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image

def combine_plots(output_dir="output"):
    files = [
        "validation_jwst.png",
        "validation_desi.png",
        "validation_sparc.png"
    ]
    images = []
    for f in files:
        path = Path(output_dir) / f
        if path.exists():
            images.append(Image.open(path))
        else:
            print(f"⚠️ Fant ikke {f} – hoppes over.")

    if not images:
        print("Ingen plott funnet i output/. Kjør validate_efc.py først.")
        return

    # Bestem bredde/høyde basert på første bilde
    widths, heights = zip(*(i.size for i in images))
    total_height = sum(heights)
    max_width = max(widths)

    dashboard = Image.new("RGB", (max_width, total_height), (255, 255, 255))
    y_offset = 0
    for im in images:
        dashboard.paste(im, (0, y_offset))
        y_offset += im.size[1]

    out_path = Path(output_dir) / "EFC_Validation_Dashboard.png"
    dashboard.save(out_path)
    print(f"✅ Dashboard lagret: {out_path}")

if __name__ == "__main__":
    combine_plots()
