import os
import shutil
import re
import json

TARGET_FOLDERS = [
    "docs/articles",
    "docs/sections",
    "docs",
    "theory",
    "theory/formal",
    "meta",
    "meta/reflection",
    "meta/cognition",
    "meta/symbiosis",
]

VALID_EXT = (".md", ".html", ".tex", ".jsonld", ".pdf")

def slugify(name):
    name = name.lower()
    name = name.replace(" ", "-")
    name = name.replace("_", "-")
    name = re.sub(r"[^a-z0-9\-]", "", name)
    return name

def migrate_file(path):
    root = os.path.dirname(path)
    basename = os.path.basename(path)
    name, ext = os.path.splitext(basename)

    # skip internal files you don't want
    if name.startswith("index"):
        return

    slug = slugify(name)
    new_folder = os.path.join(root, slug)

    os.makedirs(new_folder, exist_ok=True)
    os.makedirs(os.path.join(new_folder, "media"), exist_ok=True)

    # move file into index.ext
    new_file = os.path.join(new_folder, f"index{ext}")
    shutil.move(path, new_file)

    # move images
    for f in os.listdir(root):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
            try:
                shutil.move(os.path.join(root, f),
                            os.path.join(new_folder, "media", f))
            except:
                pass

    print(f"[OK] Migrerte: {basename} → {new_folder}/")

def scan_all():
    for folder in TARGET_FOLDERS:
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith(VALID_EXT) and f != "index.md":
                    migrate_file(os.path.join(root, f))

if __name__ == "__main__":
    print("🔄 Starter full migrering...")
    scan_all()
    print("✨ Migrering fullført.")
