import os
import shutil
import re
import json

ROOT = "docs/articles"

def slugify(name):
    name = name.lower()
    name = name.replace(" ", "-")
    name = re.sub(r"[^a-z0-9\-]", "", name)
    return name

def migrate_article(path):
    basename = os.path.basename(path)
    name, ext = os.path.splitext(basename)

    slug = slugify(name)
    folder = os.path.join(ROOT, slug)

    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "media"), exist_ok=True)

    # move main file → index.<ext>
    new_main = os.path.join(folder, f"index{ext}")
    shutil.move(path, new_main)

    # move images to media/
    parent = os.path.dirname(path)
    for f in os.listdir(parent):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
            shutil.move(os.path.join(parent, f), os.path.join(folder, "media", f))

    print(f"[OK] Migrert: {basename} → {folder}/")

def scan_and_migrate():
    for f in os.listdir(ROOT):
        path = os.path.join(ROOT, f)
        if os.path.isfile(path):
            if f.endswith((".md", ".html", ".jsonld", ".tex", ".pdf")):
                migrate_article(path)

if __name__ == "__main__":
    scan_and_migrate()
    print("🔄 Migrering fullført.")
