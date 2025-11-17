#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
import json

ROOT = Path(".")

# hvilke mapper vi migrerer
TARGET_DIRS = [
    "docs/articles",
    "docs/sections",
    "docs/figures",
    "docs/preprints",
    "docs/archive",
    "docs",
    "meta",
    "methodology",
    "theory",
]

SKIP_EXT = [".md"]  # md skal IKKE flyttes
SKIP_NAMES = ["index.md", "README.md", "index.jsonld"]


def safe_name(name):
    """Lag en ren mappenavnversjon"""
    return name.lower().replace(" ", "-").replace("_", "-")


def ensure_readme(folder: Path, original_file: Path):
    readme = folder / "README.md"
    if readme.exists():
        return

    content = f"# {folder.name}\n\nAuto-generated container for `{original_file.name}`.\n"
    readme.write_text(content)


def migrate_file(path: Path):
    if not path.is_file():
        return

    if path.suffix.lower() in SKIP_EXT:
        return

    if path.name in SKIP_NAMES:
        return

    parent = path.parent
    name = path.stem
    folder = parent / name

    # Hopp over hvis det allerede ser OK ut
    if folder.is_dir():
        return

    print(f"Migrating: {path}")

    folder.mkdir(exist_ok=True)

    # flytt fil til index.<ext>
    new_path = folder / f"index{path.suffix}"
    shutil.move(str(path), str(new_path))

    # README
    ensure_readme(folder, new_path)

    # jsonld håndtering
    jsonld_path = parent / f"{name}.jsonld"
    if jsonld_path.exists():
        shutil.move(str(jsonld_path), str(folder / "index.jsonld"))


def run():
    for base in TARGET_DIRS:
        base_path = ROOT / base
        if not base_path.exists():
            continue

        for root, dirs, files in os.walk(base_path):
            # ikke gå inn i allerede migrerte mapper
            if "index.md" in files or "index.jsonld" in files:
                continue

            for file in files:
                migrate_file(Path(root) / file)


if __name__ == "__main__":
    run()
    print("✔ Full folder migration complete.")
