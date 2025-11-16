import json
import os
import requests

TOKEN = os.environ.get("FIGSHARE_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def search_latest_efc_article():
    """Søk etter alle Figshare-artikler med DOI som inneholder 'm9.figshare'."""
    url = "https://api.figshare.com/v2/articles/search"
    params = {"search_for": "m9.figshare"}
    r = requests.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    articles = r.json()

    if not articles:
        raise RuntimeError("Ingen Figshare-artikler funnet med DOI 'm9.figshare'.")

    # Sorter etter publiseringsdato (nyeste først)
    articles.sort(key=lambda a: a.get("published_date", ""), reverse=True)
    return articles[0]["id"]


def fetch_article_metadata(article_id):
    url = f"https://api.figshare.com/v2/articles/{article_id}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_concepts(metadata):
    """Oppdater schema/concepts.json med Figshare metadata."""
    path = "schema/concepts.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            concepts = json.load(f)
    else:
        concepts = {}

    concepts["figshare"] = {
        "title": metadata.get("title"),
        "description": metadata.get("description"),
        "doi": metadata.get("doi"),
        "published_date": metadata.get("published_date"),
        "modified_date": metadata.get("modified_date"),
        "url": metadata.get("url"),
        "keywords": metadata.get("tags"),
        "categories": metadata.get("categories")
    }

    save_json(path, concepts)


def main():
    print("🔍 Søker etter siste Figshare-versjon (m9.figshare)…")
    latest_id = search_latest_efc_article()
    print(f"📌 Fant nyeste artikkel-ID: {latest_id}")

    print("🔄 Henter metadata…")
    metadata = fetch_article_metadata(latest_id)

    # Lagre full metadata
    save_json("figshare/figshare-index.json", metadata)

    # Lagre lenker
    save_json("figshare/figshare-links.json", {
        "doi": metadata.get("doi"),
        "url": metadata.get("url"),
        "api": f"https://api.figshare.com/v2/articles/{latest_id}"
    })

    # Oppdatér concepts.json
    update_concepts(metadata)

    # Export schema-map
    schema_map = {
        "figshare": {
            "id": latest_id,
            "doi": metadata.get("doi"),
            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "files": metadata.get("files"),
            "keywords": metadata.get("tags"),
            "categories": metadata.get("categories")
        }
    }

    save_json("schema/schema-map.json", schema_map)
    save_json("api/v1/meta.json", schema_map)
    save_json("docs/docs-index.json", {"figshare": schema_map})

    print("✅ Full Figshare-sync fullført!")


if __name__ == "__main__":
    main()
