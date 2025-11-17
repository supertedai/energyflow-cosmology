import os
import json

def generate_status():
    report = {}

    for root, dirs, files in os.walk("docs/articles"):
        if "index.md" in files:
            report[root] = {
                "md": True,
                "html": "index.html" in files,
                "jsonld": "index.jsonld" in files,
                "pdf": "index.pdf" in files,
                "media": "media" in dirs
            }

    with open("migration_status.json", "w") as f:
        json.dump(report, f, indent=2)

    print("📊 migration_status.json updated.")

if __name__ == "__main__":
    generate_status()
