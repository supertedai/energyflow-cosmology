#!/usr/bin/env python3

import os
import json
from pathlib import Path
from slugify import slugify
from datetime import datetime

print("[efc_full_sync] generate_paper_package — starter")

meta_path = "../config/paper_metadata.json"
pdf_path = "../production/latex/paper.pdf"

if not os.path.exists(meta_path):
    raise FileNotFoundError(f"Mangler metadata: {meta_path}")

with open(meta_path) as f:
    meta = json.load(f)

title = meta["title"]
desc = meta["description"]
keywords = meta["keywords"]

slug = slugify(title)
out_dir = Path(f"../../docs/papers/efc/{slug}")
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Kopier PDF
pdf_out = out_dir / f"{slug}.pdf"
with open(pdf_path, "rb") as src, open(pdf_out, "wb") as dst:
    dst.write(src.read())

# 2. README.md
readme = out_dir / "README.md"
readme.write_text(f"# {title}\n\n{desc}\n\nPDF: `{slug}.pdf`")

# 3. Paper MD
paper_md = out_dir / f"{slug}.md"
paper_md.write_text(f"# {title}\n\n{desc}\n\n(Automatisk generert placeholder)")

# 4. JSON-LD
jsonld = out_dir / f"{slug}.jsonld"
jsonld.write_text(json.dumps({
    "@context": "https://schema.org",
    "@type": "ScholarlyArticle",
    "name": title,
    "description": desc,
    "keywords": keywords,
    "author": {
        "@type": "Person",
        "name": "Morten Magnusson",
        "identifier": "https://orcid.org/0009-0002-4860-5095"
    },
    "encodingFormat": "application/pdf",
    "dateModified": datetime.utcnow().isoformat() + "Z"
}, indent=2))

# 5. citations.bib
citations = out_dir / "citations.bib"
citations.write_text(f"""@misc{{{slug},
  title = {{{title}}},
  author = {{Magnusson, Morten}},
  year = {{{datetime.utcnow().year}}},
  note = {{Automatisk generert EFC-pakke}}
}}
""")

# 6. metadata.json
meta_json = out_dir / "metadata.json"
meta_json.write_text(json.dumps(meta, indent=2))

print("[efc_full_sync] generate_paper_package — ferdig")
