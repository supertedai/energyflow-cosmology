# 🎯 Production Readiness Checklist

**Status:** 6. desember 2025  
**System:** Symbiose (Qdrant + Neo4j + GNN Hybrid Graph-RAG)

---

## ✅ Hva fungerer (produksjonsklar infrastruktur)

| Komponent | Status | Detaljer |
|-----------|--------|----------|
| **GNN System** | ✅ | 10,183 noder, 64-dim embeddings, modell trent |
| **Unified API** | ✅ | 8 endepunkter, hybrid scoring implementert |
| **Graph-RAG** | ✅ | Neo4j + Qdrant + GNN integrasjon |
| **MCP Server** | ✅ | LM Studio-kobling aktiv |
| **Hybrid Scoring** | ✅ | α-vekting fungerer (semantic + structural) |

---

## ⚠️ Hva som må fikses (datakvalitet)

### 1. **Test-dokumenter i produksjon**
**Problem:**
```json
{
  "source": "test/gnn-bridge-demo.md",
  "score": 0.765  ← Vinner over ekte innhold
}
```

**Løsning:**
```bash
# Fjern test-dokumenter fra Qdrant
# (Krever QDRANT_URL/API_KEY fra .env)
python tools/quality_control.py
```

---

### 2. **Manglende node_id bridge**
**Problem:**
```json
{
  "gnn_status": "no_node_id_mapping",
  "structural_score": null
}
```

**Løsning:**
```bash
# Re-ingest med Neo4j-kobling
NEO4J_URI="..." \
NEO4J_PASSWORD="..." \
  python tools/rag_ingest_repo.py
```

**Hva skjer:**
- Slår opp Neo4j node for hver fil
- Lagrer `node_id` i Qdrant payload
- Hybrid scoring aktiveres automatisk

---

### 3. **Neo4j returnerer tomt**
**Problem:**
```json
{
  "neo4j": []  ← Ingen treff
}
```

**Årsak:**
- Søket matcher på `Concept`-noder med text-felter
- Hvis dataene har annen struktur → ingen treff

**Løsning:**
```cypher
-- Sjekk hva som faktisk finnes i Neo4j:
MATCH (n) 
RETURN labels(n) AS labels, count(*) AS count 
ORDER BY count DESC 
LIMIT 10
```

Oppdater `graph_rag_client.py` til å matche faktisk node-struktur.

---

## 🎯 Én Ren Test (uten støy)

### Steg-for-steg:

#### 1. **Rens Qdrant** (fjern test-dokumenter)
```bash
# Via API (krever env vars):
python tools/quality_control.py

# Eller manuelt via Qdrant UI/API
```

#### 2. **Re-ingest med node_id**
```bash
source .venv/bin/activate

# Sett env vars (fra .env eller eksporter):
export NEO4J_URI="bolt+s://..."
export NEO4J_PASSWORD="..."
export QDRANT_URL="https://..."
export QDRANT_API_KEY="..."

# Kjør ingest:
python tools/rag_ingest_repo.py
```

**Forventet output:**
```
[rag-ingest-repo] ✅ Neo4j-kobling aktivert
[rag-ingest-repo] Ingest: theory/formal/README.md
[rag-ingest-repo]   ✅ Neo4j node_id: 4:0510400c-...
[rag-ingest-repo]   Lagret 5 chunks.
```

#### 3. **Test hybrid søk**
```bash
curl -s "http://localhost:8000/graph-rag/search?query=energy+flow&use_gnn=true&alpha=0.7" \
  | python -m json.tool
```

**Forventet output (MED bridge):**
```json
{
  "results": [
    {
      "score": 0.604,
      "structural_score": 0.850,  ✅
      "hybrid_score": 0.698,      ✅
      "node_id": "4:...",
      "gnn_neighbors": [...]
    }
  ]
}
```

#### 4. **Verifiser kvalitet**
```bash
python tools/test_gnn_bridge.py
```

**Suksess-kriterier:**
- ✅ `structural_score` vises (ikke `null`)
- ✅ `gnn_status` != `"no_node_id_mapping"`
- ✅ Hybrid score endrer seg med alpha
- ✅ Strukturelt relevante dokumenter boostes

---

## 📊 Før/Etter Forventet Resultat

### FØR (nå)
```json
{
  "query": "energy flow cosmology",
  "results": [
    {
      "source": "test/gnn-bridge-demo.md",  ← test vinner
      "score": 0.765,
      "structural_score": null,
      "gnn_status": "no_node_id_mapping"
    }
  ]
}
```

### ETTER (etter cleanup + re-ingest)
```json
{
  "query": "energy flow cosmology",
  "results": [
    {
      "source": "theory/formal/efc-v2.md",  ← ekte teori
      "score": 0.680,
      "structural_score": 0.920,            ← GNN-boost
      "hybrid_score": 0.752,                ← α×0.68 + (1-α)×0.92
      "layer": "theory",
      "doi": "10.6084/...",
      "gnn_neighbors": [...]
    }
  ]
}
```

---

## 🚀 Neste Mål

Når node_id-broen er aktiv:

1. **Vekting etter layer**
   ```python
   layer_weights = {
       "theory": 1.0,
       "paper": 0.9,
       "meta": 0.7,
       "test": 0.1
   }
   ```

2. **Deduplication**
   - Samme dokument chunkes ikke flere ganger
   - Deterministiske IDs basert på (source + chunk_index)

3. **Metadata-fullhet**
   - Alle ingestede dokumenter får `layer`, `doi`, `title`
   - Provenance sporbar helt tilbake

---

## 💡 Konklusjon

**Teknisk:**  
✅ Systemet er produksjonsklart (arkitektur + kode)

**Datakvalitet:**  
⚠️ Krever cleanup + re-ingest med node_id

**Potensial:**  
🚀 Når broen er koblet → strukturell forsterkning aktiveres

---

**Status: Klar for én rolig kvalitetsfiks** 🎯
