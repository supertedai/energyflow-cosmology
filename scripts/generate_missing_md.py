import os
import re
import json

def ensure_md(folder):
    index_md = os.path.join(folder, "index.md")
    index_html = os.path.join(folder, "index.html")
    index_json = os.path.join(folder, "index.jsonld")

    if os.path.exists(index_md):
        return

    title = folder.split("/")[-1].replace("-", " ").title()

    doi = ""
    if os.path.exists(index_json):
        try:
            with open(index_json, "r") as f:
                data = json.load(f)
            doi = data.get("identifier", "")
        except:
            pass

    md = f"# {title}\n\n"
    if doi:
        md += f"**DOI:** {doi}\n\n"

    md += "Auto-generated Markdown wrapper.\n\n"
    if os.path.exists(index_html):
        md += f"[Open HTML](index.html)\n\n"
    if os.path.exists(index_json):
        md += f"[View JSON-LD](index.jsonld)\n\n"

    with open(index_md, "w") as f:
        f.write(md)

    print(f"[OK] Created index.md in {folder}")

def scan_all():
    for root, dirs, files in os.walk("docs"):
        if "index.html" in files or "index.jsonld" in files:
            ensure_md(root)

    for root, dirs, files in os.walk("meta"):
        if "index.html" in files or "index.jsonld" in files:
            ensure_md(root)

    for root, dirs, files in os.walk("theory"):
        if "index.html" in files or "index.jsonld" in files:
            ensure_md(root)

if __name__ == "__main__":
    scan_all()
