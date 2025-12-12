# Self-Optimizing Symbiosis - Quick Reference

**One-liner**: System observes performance → adjusts parameters → anchors improvements or reverts failures.

---

## Quick Start

```python
from tools.canonical_memory_core import CanonicalMemoryCore
from tools.self_optimizing_layer import MetricType

# 1. Initialize CMC with self-optimizing
cmc = CanonicalMemoryCore(enable_self_optimizing=True)

# 2. Record metrics during operation
cmc.record_performance_metric(MetricType.OVERRIDE_RATE, 0.35)

# 3. Run optimization cycle (e.g., hourly cron)
results = cmc.run_self_optimization_cycle()
```

---

## Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `OVERRIDE_RATE` | AME overrides user | >30% |
| `CONFLICT_RATE` | Self-healing conflicts/hour | >5 |
| `ACCURACY` | Truth accuracy | <70% |
| `DOMAIN_QUALITY` | Domain detection quality | <80% |
| `MEMORY_HIT_RATE` | Memory usefulness | <50% |

---

## Parameters

| Parameter | Component | Default | Adjust When |
|-----------|-----------|---------|-------------|
| `PROMOTION_THRESHOLD` | CMC | 3 | High conflict_rate |
| `TEMPORAL_DECAY_DAYS` | Self-Healing | 90 | Low accuracy |
| `AME_OVERRIDE_STRENGTH` | AME | 0.5 | High override_rate |
| `SMM_DECAY_RATE` | SMM | 0.01 | Memory issues |
| `DDE_DOMAIN_WEIGHT` | DDE | 1.0 | Poor domain_quality |

---

## Quick Test

```bash
# Unit test
python tools/self_optimizing_layer.py

# Integration test
python test_self_optimizing_integration.py
```

---

## Common Scenarios

### Scenario 1: AME Too Aggressive

**Symptom**: Users complain about overrides

**Diagnosis**:
```python
stats = cmc.self_optimizing.observer.get_metric_stats(MetricType.OVERRIDE_RATE)
print(f"Override rate: {stats['mean']:.1%}")  # >30%
```

**Solution**: System auto-adjusts (reduces `ame_override_strength`)

---

### Scenario 2: Too Many Conflicts

**Symptom**: High conflict_rate in self-healing

**Diagnosis**:
```python
stats = cmc.self_optimizing.observer.get_metric_stats(MetricType.CONFLICT_RATE)
print(f"Conflict rate: {stats['mean']:.1f}/hour")  # >5
```

**Solution**: System auto-adjusts (increases `promotion_threshold`)

---

### Scenario 3: Stale Facts

**Symptom**: Old incorrect facts persisting

**Diagnosis**:
```python
stats = cmc.self_optimizing.observer.get_metric_stats(MetricType.ACCURACY)
print(f"Accuracy: {stats['mean']:.1%}")  # <70%
```

**Solution**: System auto-adjusts (decreases `temporal_decay_days`)

---

## Manual Override

```python
from tools.self_optimizing_layer import ParameterType

# Get current value
current = cmc.self_optimizing.adapter.get_parameter(
    ParameterType.PROMOTION_THRESHOLD
)

# Manually adjust
adjustment = cmc.self_optimizing.adapter.adjust_parameter(
    ParameterType.PROMOTION_THRESHOLD,
    new_value=5,
    reason="Manual override for testing",
    baseline_metrics={}
)
```

---

## Monitoring

```python
# Get system stats
stats = cmc.self_optimizing.get_stats()
print(f"Total adjustments: {stats['total_adjustments']}")
print(f"Success rate: {stats['success_rate']:.1%}")

# Get current parameters
params = cmc.self_optimizing.get_current_parameters()
for param, value in params.items():
    print(f"{param}: {value}")

# Get successful configs
successful = cmc.self_optimizing.tracker.get_successful_configs()
print(f"Successful configs: {len(successful)}")
```

---

## Debugging

### Check if enabled
```python
if cmc.self_optimizing:
    print("✓ Self-optimizing enabled")
else:
    print("✗ Self-optimizing disabled")
```

### Check recent metrics
```python
recent = cmc.self_optimizing.observer.get_recent_metrics(
    MetricType.OVERRIDE_RATE,
    hours=24
)
print(f"Metrics in last 24h: {len(recent)}")
```

### Check pending adjustments
```python
for adj_id, adj in cmc.self_optimizing.adapter.adjustments.items():
    if adj.result.value == "pending":
        print(f"Pending: {adj.parameter.value}")
```

---

## Cron Job Setup

```bash
# /etc/cron.d/self-optimization
0 * * * * cd /path/to/project && python -c "
from tools.canonical_memory_core import CanonicalMemoryCore
cmc = CanonicalMemoryCore(enable_self_optimizing=True)
results = cmc.run_self_optimization_cycle()
print(f'Adjustments: {len(results[\"adjustments_made\"])}')
" >> /var/log/self-optimization.log 2>&1
```

---

## Architecture Summary

```
SystemObserver → MetaEvaluator → ParameterAdapter → EffectivenessTracker
      ↓               ↓                 ↓                    ↓
  Metrics      Pattern Analysis   Apply Changes      Anchor/Revert
```

---

## Status Checklist

- [x] Core module (730 lines)
- [x] CMC integration
- [x] Unit tests
- [x] Integration tests
- [x] Full documentation
- [x] Quick reference
- [ ] Router integration
- [ ] MCP endpoint
- [ ] Production deployment
- [ ] Monitoring dashboard

---

## Key Commands

```bash
# Test core module
python tools/self_optimizing_layer.py

# Test integration
python test_self_optimizing_integration.py

# Validate syntax
python -m py_compile tools/self_optimizing_layer.py

# Count lines
wc -l tools/self_optimizing_layer.py
```

---

## Evolution

**Phase 1**: MCP Compliance ✅  
**Phase 2**: Self-Healing ✅  
**Phase 3**: Self-Optimizing ✅  
**Phase 4**: Predictive (future)

---

**EVNER, IKKE REGLER** - System learns from experience, not rules.
