import os
import json

def extract_links(data):
    links = []
    for key, value in data.items():
        if key in ("relatedTo", "partOf", "hasPart", "references"):
            if isinstance(value, list):
                links.extend(value)
            else:
                links.append(value)
    return links

def build_semantic_graph():
    graph = []

    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".jsonld"):
                full = os.path.join(root, f)
                try:
                    with open(full, "r", encoding="utf-8") as infile:
                        data = json.load(infile)
                    source = data.get("@id")
                    if not source:
                        continue

                    for target in extract_links(data):
                        graph.append({
                            "source": source,
                            "target": target,
                            "file": full
                        })
                except:
                    pass

    with open("semantic-graph.json", "w") as out:
        json.dump(graph, out, indent=2)

    print("✔ semantic-graph.json updated")

if __name__ == "__main__":
    build_semantic_graph()
