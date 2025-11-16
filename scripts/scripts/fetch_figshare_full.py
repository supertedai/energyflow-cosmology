import json
import os
import requests

TOKEN = os.environ["FIGSHARE_TOKEN"]
ARTICLE_ID = os.environ["FIGSHARE_ARTICLE_ID"]

HEADERS = {"Authorization": f"token {TOKEN}"}


def fetch_figshare_metadata(article_id):
    url = f"https://api.figshare.com/v2/articles/{article_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_concepts(concepts_path, metadata):
    """Merge Figshare abstract + keywords into schema/concepts.json"""
    try:
        with open(concepts_path, "r", encoding="utf-8") as f:
            concepts = json.load(f)
    except FileNotFoundError:
        concepts = {}

    concepts["figshare"] = {
        "doi": metadata.get("doi"),
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "categories": metadata.get("categories"),
        "keywords": metadata.get("tags"),
        "published_date": metadata.get("published_date"),
        "modified_date": metadata.get("modified_date"),
        "url": metadata.get("url"),
    }

    save_json(concepts_path, concepts)


def build_schema_map(metadata):
    """Machine-readable linkage format"""
    return {
        "figshare": {
            "id": metadata.get("id"),
            "title": metadata.get("title"),
            "doi": metadata.get("doi"),
            "url": metadata.get("url"),
            "categories": metadata.get("categories"),
            "keywords": metadata.get("tags"),
            "files": metadata.get("files"),
        }
    }


def main():
    metadata = fetch_figshare_metadata(ARTICLE_ID)

    os.makedirs("figshare", exist_ok=True)

    # Full metadata
    save_json("figshare/figshare-index.json", metadata)

    # Links only
    links = {
        "url": metadata.get("url"),
        "doi": metadata.get("doi"),
        "figshare_html": f"https://figshare.com/articles/{ARTICLE_ID}",
    }
    save_json("figshare/figshare-links.json", links)

    # Concepts merge
    update_concepts("schema/concepts.json", metadata)

    # Schema map
    schema_map = build_schema_map(metadata)
    save_json("schema/schema-map.json", schema_map)

    # API meta
    save_json("api/v1/meta.json", schema_map)

    # Docs index
    save_json("docs/docs-index.json", {"figshare": schema_map})


if __name__ == "__main__":
    main()
