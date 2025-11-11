# Energy-Flow Cosmology (EFC) – Open Semantic API

This API provides machine-readable access to the conceptual structure of **Energy-Flow Cosmology (EFC)** — a thermodynamic framework unifying cosmic structure, dynamics, and cognition.

All data follows the [Schema.org/DefinedTermSet](https://schema.org/DefinedTermSet) specification and is automatically updated from `schema/concepts.json` on every commit.

---

## 📂 Structure

| File / Folder | Content | Format |
|----------------|----------|---------|
| `api/v1/concepts.json` | Full EFC concept set (core ontology) | JSON-LD |
| `api/v1/terms.json` | Simplified term list (name, id, url) | JSON |
| `api/v1/concept/` | One file per concept (e.g., `entropy-gradient.json`) | JSON-LD |
| `api/index.json` | Manifest and metadata (optional) | JSON |

---

## 🧠 Examples

```bash
# Fetch all concepts
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concepts.json

# Fetch the simplified term list
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json

# Fetch one specific concept
curl https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concept/entropy-gradient.json
