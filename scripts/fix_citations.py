#!/usr/bin/env python3
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent
    papers_root = repo_root / "docs" / "papers" / "efc"

    if not papers_root.exists():
        print("[ERROR] Papers directory not found.")
        return

    for paper_dir in papers_root.iterdir():
        if not paper_dir.is_dir():
            continue

        paper_id = paper_dir.name
        bib_file = paper_dir / "citations.bib"

        # Build BibTex key
        bibkey = paper_id.lower().replace(" ", "-").replace("–", "-").replace("—", "-")

        # Generate content
        bib_content = f"""@article{{{bibkey}_2025,
  title={{{{ {paper_id} }}}},
  author={{Magnusson, Morten}},
  year={{2025}},
  note={{Energy-Flow Cosmology Project}},
  url={{https://github.com/supertedai/energyflow-cosmology}}
}}
"""

        # Write / overwrite
        bib_file.write_text(bib_content, encoding="utf-8")
        print(f"[FIXED] {bib_file}")

    print("\n[DONE] All citations.bib regenerated.")

if __name__ == "__main__":
    main()
