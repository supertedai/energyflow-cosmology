import requests, json

# Figshare-ID-er fra dine DOI-er (ta de siste du har)
FIGSHARE_IDS = [
    "30530156",
    "30478916",
    "30468737"
]

concepts = {"@context":"https://schema.org","@type":"DefinedTermSet","hasDefinedTerm":[]}

for fid in FIGSHARE_IDS:
    api = f"https://api.figshare.com/v2/articles/{fid}"
    r = requests.get(api)
    if r.status_code != 200:
        continue
    d = r.json()
    name = d["title"]
    doi = d["doi_url"]
    slug = name.lower().replace(" ","-")
    concept = {
        "@type": "DefinedTerm",
        "name": name,
        "description": d["description"][:600],
        "@id": f"https://energyflow-cosmology.com/concepts/{slug}",
        "identifier": doi,
        "url": doi,
        "creator": {
            "@type":"Person",
            "name":"Morten Magnusson",
            "sameAs":"https://orcid.org/0009-0002-4860-5095"
        }
    }
    concepts["hasDefinedTerm"].append(concept)

with open("schema/concepts.json","w",encoding="utf-8") as f:
    json.dump(concepts,f,indent=2,ensure_ascii=False)
