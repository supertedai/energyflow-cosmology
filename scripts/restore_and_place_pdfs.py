import os
import shutil
import subprocess

# --------------------------------------
# 1. Restore all deleted PDF files
# --------------------------------------

def restore_all_pdfs():
    print("🔄 Restoring all PDFs from history...")
    cmds = [
        "git checkout HEAD~25 -- docs/*.pdf",
        "git checkout HEAD~25 -- docs/**/*.pdf",
        "git checkout HEAD~25 -- theory/**/*.pdf",
        "git checkout HEAD~25 -- methodology/**/*.pdf",
    ]
    for cmd in cmds:
        subprocess.run(cmd, shell=True, check=False)


# --------------------------------------
# Helpers
# --------------------------------------

def ensure(path):
    if not os.path.exists(path):
        os.makedirs(path)

def slugify(name):
    return (
        name.lower()
            .replace("efc-", "")
            .replace("cem-", "")
            .replace(".pdf", "")
            .replace(" ", "-")
            .replace("_", "-")
    )


def detect_slug_from_filename(filename):
    """
    Converts EFC-Grid-Higgs-Framework.pdf -> efc-grid-higgs-framework
    """
    name = filename.lower().replace(".pdf", "")
    name = name.replace(" ", "-").replace("_", "-")
    return name


# --------------------------------------
# 2. Move PDFs into unified structure
# --------------------------------------

def place_pdfs():
    print("\n📦 Moving restored PDFs into final structure...")

    for root, dirs, files in os.walk("docs"):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue

            src = os.path.join(root, f)
            fname = f.lower()

            # MASTER
            if "master" in fname and "efc" in fname:
                dst = "docs/master/index/efc-master.pdf"
                ensure(os.path.dirname(dst))
                shutil.move(src, dst)
                print("→ MASTER:", dst)
                continue

            # FORMAL SPEC
            if "formal" in fname or "spec" in fname:
                dst = "theory/formal/efc-formal-spec/index/efc-formal-spec.pdf"
                ensure(os.path.dirname(dst))
                shutil.move(src, dst)
                print("→ FORMAL SPEC:", dst)
                continue

            # GENERAL ARTICLE
            slug = detect_slug_from_filename(f)
            article_dir = f"docs/articles/{slug}/index"

            if os.path.exists(f"docs/articles/{slug}"):
                dst = f"{article_dir}/{slug}.pdf"
                ensure(os.path.dirname(dst))
                shutil.move(src, dst)
                print("→ ARTICLE:", dst)
                continue

            print("!! Unmatched PDF:", src)

    print("\n✅ PDF restoration completed.")


# --------------------------------------
# MAIN
# --------------------------------------

if __name__ == "__main__":
    restore_all_pdfs()
    place_pdfs()
