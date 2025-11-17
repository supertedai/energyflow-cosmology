import os
import json

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def build_schema_map():
    schema = {}

    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".jsonld"):
                full = os.path.join(root, f)
                js = load_json(full)
                if js:
                    schema[f] = {
                        "path": full,
                        "type": js.get("@type"),
                        "id": js.get("@id"),
                        "name": js.get("name"),
                    }

    with open("schema-map.json", "w") as out:
        json.dump(schema, out, indent=2)

    print("✔ schema-map.json updated")

if __name__ == "__main__":
    build_schema_map()
