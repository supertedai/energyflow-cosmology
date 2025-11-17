import os
import shutil

def remove_empty_dirs(path):
    for root, dirs, files in os.walk(path, topdown=False):
        if not dirs and not files:
            os.rmdir(root)

def cleanup():
    TARGETS = [
        "docs/articles",
        "docs/sections",
        "meta",
        "theory",
        "theory/formal",
    ]

    for folder in TARGETS:
        for root, dirs, files in os.walk(folder):
            for f in files:
                # Remove temporary/duplicate formats
                if f.endswith((".bak", ".tmp", ".old")):
                    os.remove(os.path.join(root, f))
                if f.startswith("copy_of_"):
                    os.remove(os.path.join(root, f))

    # Remove empty folders
    for folder in TARGETS:
        remove_empty_dirs(folder)

    print("🧹 Cleanup done")

if __name__ == "__main__":
    cleanup()
