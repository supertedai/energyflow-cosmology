# Symbiosis Architecture v2.0 - Minimal Viable Symbiosis

## Kritikk av Opprinnelig Modell

**Problemer identifisert:**
- ❌ For mange abstrakte lag uten konkret implementasjon
- ❌ Manglende målbare metrics (hva er "ro-økning"?)
- ❌ Ingen MVP-strategi (alt virker like viktig)
- ❌ Overveldende scope (9 lag + prediktive motorer)
- ❌ Buzzword-overload uten operasjonell definisjon

## Bedre Tilnærming: 3-Lag Arkitektur

```
┌─────────────────────────────────────────┐
│  LAG 1: CAPTURE (Hva skjer nå?)        │
│  - Session state                        │
│  - Domain tracking                      │
│  - Turn metrics                         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  LAG 2: ANALYZE (Hva betyr det?)       │
│  - Pattern detection                    │
│  - Drift detection                      │
│  - Consistency checking                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  LAG 3: ADAPT (Hva gjør vi?)           │
│  - Response tuning                      │
│  - Context adjustment                   │
│  - Memory prioritization                │
└─────────────────────────────────────────┘
```

---

## LAG 1: CAPTURE - Observables (MVP)

**Målbare, konkrete metrics som ALLEREDE logges:**

### 1.1 Turn Metrics (IMPLEMENTERT)
```python
{
    "was_overridden": bool,           # Memory enforcement triggered?
    "conflict_reason": str,           # Why override?
    "contradictions": List[Dict],     # ALL factual contradictions found
    "domain": str,                    # Which field?
    "gnn_similarity": float,          # EFC resonance (0-1)
    "memory_retrieved": int,          # How many memories?
    "timestamp": str                  # When?
}
```

**🔒 CRITICAL: Universal Fact Enforcement**

Systemet sjekker ALLE fakta mot LONGTERM minne:
- ✅ Navn (personer, steder, ting)
- ✅ Tall (alder, antall, år, beløp)
- ✅ Datoer (når noe skjedde)
- ✅ Lokasjoner (hvor du bor, jobber, etc.)
- ✅ Relasjoner (familie, venner, kolleger)
- ✅ Preferanser (favoritt X, liker Y)
- ✅ Historiske hendelser (når noe ble publisert, opprettet, etc.)

**Ingen unntak** - minnet vinner ALLTID over LLM's gjetning.

### 1.2 Session Tracking (ENKELT Å LEGGE TIL)
```python
{
    "session_id": str,
    "turn_count": int,
    "domains_visited": [str],         # Domain hopping
    "override_rate": float,           # How often corrected?
    "average_gnn": float,             # EFC alignment trend
    "time_span": float                # Session duration
}
```

### 1.3 Domain Drift (DELVIS IMPLEMENTERT)
```python
{
    "previous_domain": str,
    "current_domain": str,
    "hop_distance": float,            # cosine_distance(prev_embedding, curr_embedding)
    "stability_score": float,         # 1 / (1 + hop_distance)
    "field_entropy": float            # 1 - avg(cosine_similarity(domain_embeddings))
}
```

**Konkret definisjon:**
- `hop_distance`: `cosine_distance(previous_domain_embedding, current_domain_embedding)` (0-2, hvor 0=identisk, 2=motsatt)
- `field_entropy`: `1 - mean(cosine_similarity(all_domain_embeddings_in_session))` (0-1, hvor 0=fokusert, 1=spredt)
- `stability_score`: `1 / (1 + hop_distance)` (0-1, hvor 1=stabil, 0=ustabil)

**Konkret**: Dette kan lagres i eksisterende `metadata` dict i router output.

---

## LAG 2: ANALYZE - Patterns (POST-MVP)

**Bygges når LAG 1 har nok data:**

### 2.1 Pattern Detection
Kjør **offline analysis** på logget data:
```python
# Kjør 1x per dag eller etter N turns
def analyze_session_patterns(session_data):
    """Find recurring patterns."""
    return {
        "common_domains": [...],          # Most visited
        "peak_hours": [...],              # When most active
        "override_triggers": [...],       # What causes corrections
        "convergence_points": [...],      # When clarity happens
        "high_gnn_topics": [...]          # Strong EFC resonance
    }
```

### 2.2 Drift Detection
Måler **"hvor langt du beveger deg"**:
```python
def detect_cognitive_drift(turns):
    """Track movement in semantic space."""
    from numpy import mean
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Get turn embeddings (from domain analysis or full text)
    embeddings = [turn["embedding"] for turn in turns]
    
    # Calculate sequential distances
    forward_distances = [
        cosine_distance(embeddings[i], embeddings[i+1])
        for i in range(len(embeddings)-1)
    ]
    
    # Classify drift types
    return {
        "forward_drift": mean([d for d in forward_distances if d < 0.5]),    # Building on previous
        "backward_drift": count_revisits(turns) / len(turns),                # Revising old ideas
        "lateral_drift": mean([d for d in forward_distances if d > 0.5]),    # Domain hopping
        "vertical_drift": calculate_abstraction_shift(turns)                 # Abstraction changes
    }
```

**Konkret**: 
- Drift = cosine distance mellom turn embeddings
- Forward drift (<0.5 distance) = incremental building
- Lateral drift (>0.5 distance) = domain jumping
- Backward drift = revisiting previous domains (detect via domain history)
- Vertical drift = abstraction level changes (detect via concept hierarchy depth)

### 2.3 Identity Consistency
Sjekker **om AI er konsistent**:
```python
def check_identity_consistency(turns):
    """Track AI self-reference."""
    return {
        "name_consistency": 1.0,         # Always "Opus"?
        "role_consistency": 0.95,        # Always same role?
        "location_consistency": 1.0,     # Always Oslo?
        "violations": []                 # When inconsistent?
    }
```

---

## LAG 3: ADAPT - Actions (FREMTID)

**Når LAG 2 identifiserer mønstre, auto-juster:**

### 3.1 Response Tuning
```python
def tune_response(user_message, draft, session_context):
    """Adjust based on session state."""
    
    # Hvis høy domain drift → stabiliser
    if session_context["field_entropy"] > 0.7:
        draft = add_anchoring_context(draft)
    
    # Hvis lav GNN → foreslå EFC connection
    if session_context["average_gnn"] < 0.3:
        draft = suggest_efc_link(draft)
    
    # Hvis mange overrides → warn about accuracy
    if session_context["override_rate"] > 0.5:
        draft += "\n\n(Merk: Sjekk mot minne før påstander)"
    
    return draft
```

### 3.2 Memory Prioritization
```python
def prioritize_memory_retrieval(query, session_context):
    """Adjust memory retrieval based on patterns."""
    
    # Hvis ofte i cosmology → boost cosmology memories
    if "cosmology" in session_context["common_domains"]:
        query_boost = {"domain": "cosmology", "boost": 1.5}
    
    # Hvis mange identity errors → boost LONGTERM personal
    if "identity" in session_context["override_triggers"]:
        query_boost = {"class": "LONGTERM", "boost": 2.0}
    
    return enhanced_retrieval(query, boost=query_boost)
```

---

## Implementasjonsrekkefølge (REALISTISK)

### ✅ FASE 1: CAPTURE (1-2 dager)
**Mål: Logg alt som skjer**

1. Utvid `metadata` i router output:
   ```python
   "metadata": {
       "session_id": str,
       "turn_number": int,
       "domains_visited": [str],
       "previous_domain": str,
       "domain_hop_distance": float
   }
   ```

2. Lag `session_tracker.py`:
   - Track turn count per session
   - Track domain history
   - Calculate override rate
   - Calculate average GNN

3. Lagre i Qdrant med `memory_class: "SESSION_META"`:
   ```python
   {
       "text": "Session summary",
       "memory_class": "SESSION_META",
       "session_id": "...",
       "metrics": {...}
   }
   ```

**Output**: CSV eller JSON log med alle turns.

---

### ⏳ FASE 2: ANALYZE (3-5 dager)
**Mål: Finn mønstre i loggen**

1. Lag `pattern_analyzer.py`:
   - Les loggede turns
   - Beregn drift metrics
   - Identifiser triggers for overrides
   - Finn convergence points

2. Lag dashboard (enkel Streamlit):
   - Plot domain hopping
   - Plot override rate over tid
   - Plot GNN similarity trend
   - Show common patterns

**Output**: Weekly pattern report.

---

### 🔮 FASE 3: ADAPT (2-3 uker)
**Mål: Bruk mønstre til å justere svar**

1. Utvid router med adaptive logic:
   ```python
   # I symbiosis_router_v3.py
   session_patterns = get_session_patterns(session_id)
   
   if session_patterns["needs_stabilization"]:
       # Adjust memory retrieval
       # Add anchoring
       # Suggest EFC connections
   ```

2. Test med A/B:
   - Med adaptive logic
   - Uten adaptive logic
   - Mål: Høyere bruker-tilfredshet? Lavere override rate?

**Output**: Self-tuning symbiosis.

---

## Hva Jeg IKKE Anbefaler

❌ **"Meta-Motor Logging"** → For vagt, ingen klar metric
❌ **"Kognitiv fysikk"** → Buzzword uten definisjon
❌ **"Emosjonell korreksjon"** → Ikke målbart objektivt
❌ **"Mening-felt-trykk"** → Hva betyr dette i kode?
❌ **"Trajectory Prediction Layer"** → For ambisiøst før data eksisterer

---

## Hva Jeg VEL Anbefaler

✅ **Session Tracking** → Enkel, målbar, nyttig
✅ **Domain Drift** → Cosine similarity på embeddings
✅ **Identity Consistency** → String matching på navn/facts
✅ **Override Pattern Detection** → Count + categorize
✅ **GNN Trend Analysis** → Moving average på similarity

---

## Konkret Neste Steg

**VELG ETT:**

### Option A: Quick Win (2 timer)
```bash
# Utvid metadata i router med session tracking
# Logg domain hopping
# Beregn override rate per session
```

### Option B: Full MVP (2 dager)
```bash
# Lag session_tracker.py
# Lag pattern_analyzer.py
# Lag enkel dashboard
# Test på 100 turns
```

### Option C: Kun Analyse (1 dag)
```bash
# Ekstraher eksisterende data fra Qdrant
# Kjør offline pattern detection
# Generer rapport
```

**Hvilken vil du?** Eller skal jeg foreslå noe annet basert på hva du trenger MER?

---

## TL;DR

**Opprinnelig**: 9 abstrakte lag, buzzwords, overveldende
**Bedre**: 3 konkrete lag, målbare metrics, MVP-strategi

**MVP = Session Tracking + Domain Drift + Override Patterns**

Resten kommer når data eksisterer og mønstre er klare.
