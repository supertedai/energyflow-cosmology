# Energy-Flow Cosmology (EFC) – Open Semantic API

Dette API-et gjør begreper og strukturer fra Energy-Flow Cosmology (EFC) maskinlesbare og gjenbrukbare for forskning, AI-systemer og kunnskapsdatabaser.

Alle data følger [Schema.org/DefinedTermSet](https://schema.org/DefinedTermSet)-standarden og oppdateres automatisk fra `schema/concepts.json` ved hver commit.

---

## 📂 Struktur

| Fil / Mappe | Innhold | Format |
|--------------|----------|---------|
| `api/v1/concepts.json` | Hele EFC-begrepssettet (strukturert kjerne) | JSON-LD |
| `api/v1/terms.json` | Forenklet liste med navn, ID og URL | JSON |
| `api/v1/concept/` | Én fil per begrep (f.eks. `entropy-gradient.json`) | JSON-LD |
| `api/index.json` | Manifest med metadata og lenker | JSON |

---

## 🧠 Eksempel

```bash
# Hent alle begreper
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concepts.json

# Hent kortliste
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json

# Hent ett begrep
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concept/entropy-gradient.json
