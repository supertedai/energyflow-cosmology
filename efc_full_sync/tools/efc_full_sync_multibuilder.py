import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPERS_SRC = ROOT / "papers_src"
OUTPUT_ROOT = ROOT / "docs" / "papers" / "efc"

def run(cmd, cwd=None):
    print(f"[builder] Running: {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

def build_paper(paper_dir):
    meta_path = paper_dir / "metadata.json"
    paper_tex = paper_dir / "paper.tex"

    if not meta_path.exists() or not paper_tex.exists():
        return

    with open(meta_path) as f:
        meta = json.load(f)

    slug = meta["slug"]
    out_dir = OUTPUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build PDF
    run(f"pdflatex -interaction=nonstopmode paper.tex", cwd=paper_dir)

    pdf_src = paper_dir / "paper.pdf"
    pdf_dst = out_dir / f"{slug}.pdf"
    pdf_dst.write_bytes(pdf_src.read_bytes())

    # 2. Copy metadata
    jsonld_path = out_dir / f"{slug}.jsonld"
    jsonld_path.write_text(json.dumps(meta, indent=2))

    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2))

    print(f"[builder] Finished: {slug}")

def scan_and_build():
    print("[builder] Scanning papers_src/")
    for domain in PAPERS_SRC.iterdir():
        if not domain.is_dir():
            continue
        for paper in domain.iterdir():
            if paper.name.startswith("_template"):
                continue
            if (paper / "metadata.json").exists():
                build_paper(paper)

if __name__ == "__main__":
    scan_and_build()
