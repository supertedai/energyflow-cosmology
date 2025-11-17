import os
import shutil
import re
from pathlib import Path

ROOTS = [
    "docs/articles",
    "meta",
    "theory/formal",
    "methodology"
]

EXT_PRIMARY = {".md", ".jsonld", ".tex", ".pdf", ".html", ".docx"}
EXT_MEDIA = {".png", ".jpg", ".jpeg", ".svg"}

def slugify(name):
    return re.sub(r"[^a-zA-Z0-9\-]+", "-", name).strip("-")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def move_file(src, dst):
    ensure_dir(os.path.dirname(dst))
    shutil.move(src, dst)
    print(f"Moved: {src} -> {dst}")

def migrate_folder(base):
    files = list(Path(base).glob("*"))

    for f in files:
        if f.is_dir():
            # Skip already migrated structure
            if (f / "index.md").exists() or (f / "index.jsonld").exists():
                continue
            continue

        # Original filename slug
        stem = f.stem
        slug = slugify(stem)

        # Target folder
        target = Path(base) / slug
        ensure_dir(target)

        # Determine type of file
        ext = f.suffix.lower()

        if ext in EXT_PRIMARY:
            dst = target / f"index{ext}"
            move_file(str(f), str(dst))

        elif ext in EXT_MEDIA:
            media_dir = target / "media"
            ensure_dir(media_dir)
            dst = media_dir / f.name
            move_file(str(f), str(dst))

        else:
            # Unknown extension → treat as auxiliary
            aux_dir = target / "aux"
            ensure_dir(aux_dir)
            dst = aux_dir / f.name
            move_file(str(f), str(dst))

def cleanup_empty(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            full = os.path.join(root, d)
            if not os.listdir(full):
                os.rmdir(full)
                print(f"Removed empty folder: {full}")

def main():
    print("=== Full Structure Migration ===")
    for root in ROOTS:
        if os.path.exists(root):
            print(f"-- Migrating: {root}")
            migrate_folder(root)
            cleanup_empty(root)

    print("=== DONE ===")

if __name__ == "__main__":
    main()
