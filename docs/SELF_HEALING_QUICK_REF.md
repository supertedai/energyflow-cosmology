# Self-Healing Memory - Quick Reference

## One-Liner
**Observation-based truth engine that isolates test data and resolves conflicts automatically via authority-weighted aggregation.**

---

## Quick Test

```bash
cd /Users/morpheus/energyflow-cosmology
python test_self_healing_integration.py
```

**Expected output**:
```
Canonical name: Morten
Expected: Morten (user wins over cli_test) ✅
```

---

## Usage

### Basic (automatic - recommended)

```python
from tools.canonical_memory_core import CanonicalMemoryCore

cmc = CanonicalMemoryCore(enable_self_healing=True)

# Store fact (automatically uses observations)
cmc.store_fact(
    key="user_name",
    value="Morten",
    domain="identity",
    fact_type="name",
    source="user"  # Tagged automatically
)

# Query canonical truth
if cmc.self_healing:
    truth = cmc.self_healing.get_canonical_truth("identity", "user_name")
    print(truth)  # "Morten"
```

### Advanced (direct self-healing layer)

```python
from tools.self_healing_canonical import (
    SelfHealingCanonical,
    SourceType,
    AuthorityLevel
)

shc = SelfHealingCanonical()

# Register observations
shc.register_observation(
    domain="identity",
    key="name",
    value="Morten",
    source=SourceType.CHAT_USER,
    authority=AuthorityLevel.SHORT_TERM
)

# Get canonical truth
truth = shc.get_canonical_truth("identity", "name")

# Detect conflicts
conflicts = shc.detect_conflicts()

# Get stats
stats = shc.get_stats()
```

---

## Authority Levels

| Level | Weight | Usage |
|-------|--------|-------|
| TEST | 0.1 | CLI tests only |
| SHORT_TERM | 1.0 | Single mention |
| MEDIUM_TERM | 2.0 | Multiple mentions |
| STABLE | 5.0 | Verified |
| LONG_TERM | 10.0 | Established truth |

---

## Source Types

| Source | Weight | Auto-tagged from |
|--------|--------|------------------|
| CLI_TEST | 0.1 | `source="cli_test"` |
| CHAT_USER | 1.0 | `source="user"` |
| MEMORY_ENHANCEMENT | 1.5 | `source="memory_enhancement"` |
| INGEST_DOC | 3.0 | `source="ingest"` |
| SYSTEM_DEFAULT | 2.0 | `source="system"` |

---

## Key Features

✅ **Test data isolation** - CLI tests never pollute truth  
✅ **Conflict resolution** - Automatic via weighting  
✅ **Authority hierarchy** - Strong sources win  
✅ **Temporal decay** - Old facts degrade  
✅ **Domain-agnostic** - Works for ALL domains  

---

## Integration Points

1. **CMC** - `enable_self_healing=True` (default)
2. **Router** - Uses CMC → automatic observations
3. **AME** - Generates observations from enhancement
4. **MCA** - Periodic conflict detection

---

## Conflict Resolution Rules

1. Sort by authority (LONG_TERM > STABLE > ... > TEST)
2. Weight by source (INGEST_DOC > CHAT_USER > CLI_TEST)
3. Weight by support count
4. Weight by recency

**Winner** → ACTIVE/STABLE  
**Losers** → DEPRECATED

---

## Common Scenarios

### Scenario 1: Test vs Real Data
```python
# Test data
store_fact(key="name", value="TestUser", source="cli_test")

# Real user data
store_fact(key="name", value="Morten", source="user")

# Result: "Morten" ✅ (user wins)
```

### Scenario 2: Multiple Sources
```python
# User says X
store_fact(key="db", value="Neo4j", source="user")

# Doc says Y
store_fact(key="db", value="Qdrant", source="ingest")

# Result: "Qdrant" ✅ (ingest has higher weight)
```

### Scenario 3: Temporal Decay
```python
# Old fact (90+ days unused)
# Gets demoted: STABLE → ACTIVE → SUSPECT → DEPRECATED

shc.apply_temporal_decay()
```

---

## Debugging

### Check observations
```python
print(f"Total observations: {len(shc.observations)}")
```

### Check facts
```python
print(f"Total facts: {len(shc.facts)}")
for fact in shc.facts.values():
    print(f"{fact.domain}.{fact.key} = {fact.value} [{fact.status.value}]")
```

### Check conflicts
```python
conflicts = shc.detect_conflicts()
for conflict in conflicts:
    print(f"Conflict: {conflict.domain}.{conflict.key}")
    print(f"Values: {conflict.competing_values}")
```

### Get stats
```python
stats = shc.get_stats()
print(json.dumps(stats, indent=2))
```

---

## Files

| File | Purpose |
|------|---------|
| `tools/self_healing_canonical.py` | Core self-healing layer |
| `tools/canonical_memory_core.py` | CMC with self-healing integration |
| `test_self_healing_integration.py` | Integration tests |
| `docs/SELF_HEALING_MEMORY.md` | Full architecture docs |

---

## Status

```
✅ Core implementation: Complete
✅ CMC integration: Complete
✅ Testing: Validated
✅ Documentation: Complete
✅ Production ready: YES
```

---

## Next Steps

1. Deploy to LM Studio
2. Monitor conflict resolution in live chat
3. Validate test data isolation in production
4. Performance optimization if needed

---

**Version**: 1.0  
**Date**: 2025-12-12  
**Status**: ✅ PRODUCTION READY
