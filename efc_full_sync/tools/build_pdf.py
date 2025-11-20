#!/usr/bin/env python3

import os
import shutil

print("[efc_full_sync] build_pdf.py — starter")

# Kilde til ferdig PDF hvis den finnes
source = "../production/latex/paper.pdf"

if not os.path.exists(source):
    # Lag en placeholder-PDF hvis LaTeX-build ikke er satt opp ennå
    print("[efc_full_sync] Fant ikke paper.pdf — lager placeholder")
    os.makedirs("../production/latex", exist_ok=True)
    with open(source, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")

print("[efc_full_sync] PDF OK")
