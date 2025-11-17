import os
import shutil
from pathlib import Path

EXT_PRIMARY = {".md", ".jsonld", ".tex", ".pdf", ".html", ".docx"}
EXT_MEDIA = {".png", ".jpg", ".jpeg", ".svg"}

ROOTS = [
    "docs/articles",
    "docs/sections",
    "meta",
    "theory/formal",
    "methodology"
]

def is_indexed_dir(path: Path):
    return (path / "index.md").exists() or (path / "index.tex").exists()

def migrate_file(f: Path, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = f.suffix.lower()
    if ext in EXT_PRIMARY:
        # primary -> index.ext
        dst = target_dir / f"index{ext}"
    elif ext in EXT_MEDIA:
        # images -> media/
        media_dir = target_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        dst = media_dir / f.name
    else:
        # unknown -> aux/
        aux_dir = target_dir / "aux"
        aux_dir.mkdir(parents=True, exist_ok=True)
        dst = aux_dir / f.name

    shutil.move(str(f), str(dst))
    print(f"Moved: {f} -> {dst}")

def process_path(base: Path):
    for f in base.glob("*"):
        # skip already structured dirs
        if f.is_dir():
            if is_indexed_dir(f):
                continue
            process_path(f)
            continue

        # file belongs to its own folder
        slug = f.stem
        target_dir = base / slug
        migrate_file(f, target_dir)

def cleanup_empty(path: Path):
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            full = Path(root) / d
            try:
                if not any(full.iterdir()):
                    full.rmdir()
                    print(f"Removed empty: {full}")
            except:
                pass

def main():
    print("=== FULL STRUCTURE MIGRATION ===")
    for root in ROOTS:
        base = Path(root)
        if base.exists():
            process_path(base)
            cleanup_empty(base)
    print("=== DONE ===")

if __name__ == "__main__":
    main()
