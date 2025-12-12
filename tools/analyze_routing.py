#!/usr/bin/env python3
"""
analyze_routing.py - Router Decision Log Analysis
=================================================

Analyzes logs/router_decisions.jsonl to understand:
- Layer activation patterns
- Performance bottlenecks
- Override frequency
- Domain distribution
- Cognitive mode patterns
"""

import json
import os
from typing import List, Dict, Any
from collections import Counter, defaultdict
from datetime import datetime

def load_routing_logs(log_file: str = "logs/router_decisions.jsonl") -> List[Dict]:
    """Load all routing log entries."""
    if not os.path.exists(log_file):
        print(f"⚠️  Log file not found: {log_file}")
        return []
    
    logs = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    
    return logs


def analyze_layer_activation(logs: List[Dict]):
    """Analyze which layers are activated most frequently."""
    print("\n" + "=" * 60)
    print("🔧 LAYER ACTIVATION ANALYSIS")
    print("=" * 60)
    
    layer_counts = Counter()
    for log in logs:
        for layer in log.get("activated_layers", []):
            layer_counts[layer] += 1
    
    print(f"\nTotal routing decisions: {len(logs)}")
    print(f"\nLayer activation frequency:")
    for layer, count in layer_counts.most_common():
        pct = (count / len(logs)) * 100
        print(f"  {layer:20s}: {count:4d} ({pct:5.1f}%)")


def analyze_layer_timings(logs: List[Dict]):
    """Analyze layer performance."""
    print("\n" + "=" * 60)
    print("⚡ LAYER PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    timings = defaultdict(list)
    
    for log in logs:
        for layer, time_ms in log.get("layer_timings", {}).items():
            timings[layer].append(time_ms)
    
    print(f"\nAverage layer execution times:")
    for layer in sorted(timings.keys()):
        times = timings[layer]
        avg = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        print(f"  {layer:20s}: avg={avg:6.1f}ms, min={min_time:6.1f}ms, max={max_time:6.1f}ms")
    
    # Total times
    total_times = [log.get("total_time_ms", 0) for log in logs]
    if total_times:
        avg_total = sum(total_times) / len(total_times)
        min_total = min(total_times)
        max_total = max(total_times)
        print(f"\n  {'TOTAL':<20s}: avg={avg_total:6.1f}ms, min={min_total:6.1f}ms, max={max_total:6.1f}ms")


def analyze_override_patterns(logs: List[Dict]):
    """Analyze memory override patterns."""
    print("\n" + "=" * 60)
    print("🛡️  MEMORY OVERRIDE ANALYSIS")
    print("=" * 60)
    
    contradiction_count = sum(1 for log in logs if log.get("contradiction_detected"))
    override_count = sum(1 for log in logs if log.get("override_triggered"))
    
    print(f"\nOverride statistics:")
    print(f"  Contradictions detected: {contradiction_count}/{len(logs)} ({(contradiction_count/len(logs)*100):.1f}%)")
    print(f"  Overrides triggered:     {override_count}/{len(logs)} ({(override_count/len(logs)*100):.1f}%)")
    
    # Enforcement decisions
    enforcement_decisions = Counter()
    for log in logs:
        decision = log.get("routing_decisions", {}).get("enforcement")
        if decision:
            enforcement_decisions[decision] += 1
    
    print(f"\nEnforcement decisions:")
    for decision, count in enforcement_decisions.most_common():
        pct = (count / len(logs)) * 100
        print(f"  {decision:20s}: {count:4d} ({pct:5.1f}%)")


def analyze_domain_distribution(logs: List[Dict]):
    """Analyze domain detection patterns."""
    print("\n" + "=" * 60)
    print("🎯 DOMAIN DISTRIBUTION")
    print("=" * 60)
    
    domains = Counter()
    for log in logs:
        domain = log.get("routing_decisions", {}).get("domain_detection")
        if domain:
            domains[domain] += 1
    
    print(f"\nTop domains:")
    for domain, count in domains.most_common(15):
        pct = (count / len(logs)) * 100
        print(f"  {domain:20s}: {count:4d} ({pct:5.1f}%)")


def analyze_memory_retrieval(logs: List[Dict]):
    """Analyze memory retrieval effectiveness."""
    print("\n" + "=" * 60)
    print("🧠 MEMORY RETRIEVAL ANALYSIS")
    print("=" * 60)
    
    canonical_counts = []
    context_counts = []
    
    for log in logs:
        retrieval = log.get("routing_decisions", {}).get("memory_retrieval", {})
        canonical_counts.append(retrieval.get("canonical_facts", 0))
        context_counts.append(retrieval.get("context_chunks", 0))
    
    if canonical_counts:
        avg_canonical = sum(canonical_counts) / len(canonical_counts)
        avg_context = sum(context_counts) / len(context_counts)
        
        print(f"\nAverage facts retrieved per turn:")
        print(f"  Canonical facts: {avg_canonical:.1f}")
        print(f"  Context chunks:  {avg_context:.1f}")
        
        # Distribution
        no_canonical = sum(1 for c in canonical_counts if c == 0)
        no_context = sum(1 for c in context_counts if c == 0)
        
        print(f"\nTurns with no memory:")
        print(f"  No canonical facts: {no_canonical}/{len(logs)} ({(no_canonical/len(logs)*100):.1f}%)")
        print(f"  No context chunks:  {no_context}/{len(logs)} ({(no_context/len(logs)*100):.1f}%)")


def analyze_temporal_patterns(logs: List[Dict]):
    """Analyze temporal patterns."""
    print("\n" + "=" * 60)
    print("📅 TEMPORAL PATTERNS")
    print("=" * 60)
    
    # Group by hour
    hours = defaultdict(int)
    dates = defaultdict(int)
    
    for log in logs:
        timestamp = log.get("timestamp")
        if timestamp:
            dt = datetime.fromisoformat(timestamp)
            hours[dt.hour] += 1
            dates[dt.date().isoformat()] += 1
    
    print(f"\nRouting decisions by hour:")
    for hour in sorted(hours.keys()):
        count = hours[hour]
        bar = "█" * (count // 5 + 1)
        print(f"  {hour:02d}:00-{hour:02d}:59  {count:4d}  {bar}")
    
    print(f"\nRouting decisions by date:")
    for date in sorted(dates.keys())[-7:]:  # Last 7 days
        count = dates[date]
        bar = "█" * (count // 10 + 1)
        print(f"  {date}  {count:4d}  {bar}")


def identify_bottlenecks(logs: List[Dict]):
    """Identify performance bottlenecks."""
    print("\n" + "=" * 60)
    print("🚨 PERFORMANCE BOTTLENECKS")
    print("=" * 60)
    
    # Find slowest turns
    slow_turns = []
    for log in logs:
        total_time = log.get("total_time_ms", 0)
        if total_time > 1000:  # > 1 second
            slow_turns.append((total_time, log))
    
    slow_turns.sort(reverse=True)
    
    print(f"\nSlowest routing decisions (>{1000}ms):")
    for i, (time_ms, log) in enumerate(slow_turns[:10], 1):
        session = log.get("session_id", "unknown")
        turn = log.get("turn_number", "?")
        message = log.get("user_message", "")[:50]
        print(f"\n  {i}. {time_ms:.0f}ms - session:{session}, turn:{turn}")
        print(f"     Message: {message}...")
        
        # Layer breakdown
        timings = log.get("layer_timings", {})
        if timings:
            sorted_timings = sorted(timings.items(), key=lambda x: x[1], reverse=True)
            print(f"     Slowest layers:")
            for layer, layer_time in sorted_timings[:3]:
                pct = (layer_time / time_ms) * 100
                print(f"       - {layer}: {layer_time:.1f}ms ({pct:.1f}%)")
    
    if not slow_turns:
        print("\n  ✅ No slow routing decisions found")


def main():
    """Main analysis workflow."""
    print("📊 Router Decision Log Analysis")
    print("=" * 60)
    
    logs = load_routing_logs()
    
    if not logs:
        print("\n⚠️  No routing logs found. Run some chat turns first.")
        return
    
    print(f"\nLoaded {len(logs)} routing decisions")
    print(f"Time range: {logs[0]['timestamp'][:10]} to {logs[-1]['timestamp'][:10]}")
    
    # Run analyses
    analyze_layer_activation(logs)
    analyze_layer_timings(logs)
    analyze_override_patterns(logs)
    analyze_domain_distribution(logs)
    analyze_memory_retrieval(logs)
    analyze_temporal_patterns(logs)
    identify_bottlenecks(logs)
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print(f"\nLog file: logs/router_decisions.jsonl")
    print(f"Total entries: {len(logs)}")
    print()


if __name__ == "__main__":
    main()
