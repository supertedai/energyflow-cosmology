import os
import json

def build_node_index():
    nodes = []

    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".jsonld"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as infile:
                        data = json.load(infile)
                        nodes.append({
                            "id": data.get("@id"),
                            "name": data.get("name"),
                            "type": data.get("@type"),
                            "path": path
                        })
                except:
                    pass

    with open("node-index.json", "w") as out:
        json.dump(nodes, out, indent=2)

    print("✔ node-index.json updated")

if __name__ == "__main__":
    build_node_index()
