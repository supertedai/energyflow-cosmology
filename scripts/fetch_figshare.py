import json
import requests
from pathlib import Path

# ----------------------------------------------------------
# fetch_figshare.py
# Leser figshare/figshare-index.json, henter metadata
# fra Figshare API, og genererer schema/concepts.json
# ----------------------------------------------------------

FIGSHARE_INDEX = Path("figshare/figshare-index.json")
OUTPUT_FILE = Path("schema/concepts.json")

def load_figshare_ids(index_path: Path):
    """Les DOI/ID-er fra figshare-index.json."""
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids = []
    for item in data.get("dataset", []):
        identifier = item.get("identifier", "")
        # DOI-url → ID (siste tall)
        if identifier.startswith("https://doi.org/10.6084/m9.figshare."):
            ids.append(identifier.split(".")[-1])
    return ids


def fetch_article(fid: str):
    """Hent metadata fra Figshare API for gitt ID."""
    url = f"https://api.figshare.com/v2/articles/{fid}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️  Feil ved henting av {fid}: {e}")
        return None


def main():
    if not FIGSHARE_INDEX.exists():
        print(f"❌ Finner ikke {FIGSHARE_INDEX}")
        return

    figshare_ids = load_figshare_ids(FIGSHARE_INDEX)
    if not figshare_ids:
        print("⚠️  Ingen Figshare-IDer funnet i indeksen.")
        return

    print(f"🔄 Henter metadata for {len(figshare_ids)} artikler ...")

    concepts = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "hasDefinedTerm": []
    }

    for fid in figshare_ids:
        data = fetch_article(fid)
        if not data:
            continue

        name = data.get("title", "Untitled")
        doi = data.get("doi_url", "")
        desc = (data.get("description") or "").strip()
        slug = name.lower().replace(" ", "-")

        concept = {
            "@type": "DefinedTerm",
            "name": name,
            "description": desc[:600],
            "@id": f"https://energyflow-cosmology.com/concepts/{slug}",
            "identifier": doi,
            "url": doi,
            "creator": {
                "@type": "Person",
                "name": "Morten Magnusson",
                "sameAs": "https://orcid.org/0009-0002-4860-5095"
            }
        }

        concepts["hasDefinedTerm"].append(concept)
        print(f"✅  {name}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(concepts, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Lagret {len(concepts['hasDefinedTerm'])} konsepter til {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
