import os
import re
import json

def update_links(root="."):
    for root, dirs, files in os.walk(root):
        for f in files:
            if f.endswith((".md", ".html")):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as infile:
                    text = infile.read()

                # Update links to new structure
                text = re.sub(
                    r"docs/articles/([A-Za-z0-9_\-]+)\.(md|html)",
                    r"docs/articles/\1/index.\2",
                    text
                )

                # media links
                text = re.sub(
                    r"(docs/articles/[A-Za-z0-9_\-]+)/([A-Za-z0-9_\-]+\.(png|jpg|svg))",
                    r"\1/media/\2",
                    text
                )

                with open(path, "w", encoding="utf-8") as outfile:
                    outfile.write(text)

                print(f"[OK] Updated links in: {path}")

if __name__ == "__main__":
    update_links(".")
