#!/usr/bin/env python3
"""
Pattern Analyzer - LAG 2: ANALYZE
==================================

Analyzes patterns in logged session data.

Functions:
- analyze_session_patterns(session_id) → Recurring patterns
- detect_cognitive_drift(session_id) → Movement types
- check_identity_consistency(session_id) → AI consistency
- generate_session_report(session_id) → Full analysis
"""

import os
import sys
from typing import Dict, Any, List
from collections import Counter
from datetime import datetime
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.session_tracker import get_session_turns, get_session_state


def analyze_session_patterns(session_id: str) -> Dict[str, Any]:
    """
    Find recurring patterns in session data.
    
    Returns:
        {
            "common_domains": [(domain, count)],
            "peak_hours": [hour],
            "override_triggers": [(reason, count)],
            "convergence_points": [turn_number],
            "high_gnn_topics": [(domain, avg_gnn)]
        }
    """
    turns = get_session_turns(session_id)
    
    if not turns:
        return {
            "common_domains": [],
            "peak_hours": [],
            "override_triggers": [],
            "convergence_points": [],
            "high_gnn_topics": []
        }
    
    # Common domains
    domains = [t.get("domain") for t in turns if t.get("domain")]
    domain_counts = Counter(domains).most_common(5)
    
    # Peak hours
    hours = []
    for turn in turns:
        ts = turn.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hours.append(dt.hour)
            except:
                pass
    peak_hours = [h for h, _ in Counter(hours).most_common(3)]
    
    # Override triggers
    override_reasons = [
        t.get("conflict_reason") 
        for t in turns 
        if t.get("was_overridden") and t.get("conflict_reason")
    ]
    override_triggers = Counter(override_reasons).most_common(5)
    
    # Convergence points (where field_entropy drops significantly)
    convergence_points = []
    for i in range(1, len(turns)):
        prev_entropy = turns[i-1].get("field_entropy", 0)
        curr_entropy = turns[i].get("field_entropy", 0)
        
        if prev_entropy - curr_entropy > 0.2:  # Significant drop
            convergence_points.append(i + 1)
    
    # High GNN topics
    domain_gnn = {}
    for turn in turns:
        domain = turn.get("domain")
        gnn = turn.get("gnn_similarity")
        
        if domain and gnn is not None:
            if domain not in domain_gnn:
                domain_gnn[domain] = []
            domain_gnn[domain].append(gnn)
    
    high_gnn_topics = [
        (domain, np.mean(scores))
        for domain, scores in domain_gnn.items()
        if np.mean(scores) > 0.5
    ]
    high_gnn_topics.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "common_domains": domain_counts,
        "peak_hours": peak_hours,
        "override_triggers": override_triggers,
        "convergence_points": convergence_points,
        "high_gnn_topics": high_gnn_topics[:5]
    }


def detect_cognitive_drift(session_id: str) -> Dict[str, float]:
    """
    Track movement in semantic space.
    
    Returns:
        {
            "forward_drift": float,    # Building on previous (<0.5 distance)
            "backward_drift": float,   # Revisiting old topics
            "lateral_drift": float,    # Domain hopping (>0.5 distance)
            "vertical_drift": float    # Abstraction changes
        }
    """
    turns = get_session_turns(session_id)
    
    if len(turns) < 2:
        return {
            "forward_drift": 0.0,
            "backward_drift": 0.0,
            "lateral_drift": 0.0,
            "vertical_drift": 0.0
        }
    
    # Get hop distances
    hop_distances = [
        t.get("hop_distance", 0.0)
        for t in turns
        if t.get("hop_distance") is not None
    ]
    
    if not hop_distances:
        return {
            "forward_drift": 0.0,
            "backward_drift": 0.0,
            "lateral_drift": 0.0,
            "vertical_drift": 0.0
        }
    
    # Forward drift: small hops (<0.5) = incremental building
    forward_hops = [d for d in hop_distances if d < 0.5]
    forward_drift = np.mean(forward_hops) if forward_hops else 0.0
    
    # Lateral drift: large hops (>0.5) = domain jumping
    lateral_hops = [d for d in hop_distances if d > 0.5]
    lateral_drift = np.mean(lateral_hops) if lateral_hops else 0.0
    
    # Backward drift: revisiting previous domains
    domains = [t.get("domain") for t in turns if t.get("domain")]
    domain_revisits = len(domains) - len(set(domains))
    backward_drift = domain_revisits / len(domains) if domains else 0.0
    
    # Vertical drift: abstraction level changes
    # Simplified: use field_entropy as proxy
    entropies = [
        t.get("field_entropy", 0.0)
        for t in turns
        if t.get("field_entropy") is not None
    ]
    
    if len(entropies) > 1:
        entropy_changes = [abs(entropies[i] - entropies[i-1]) for i in range(1, len(entropies))]
        vertical_drift = np.mean(entropy_changes)
    else:
        vertical_drift = 0.0
    
    return {
        "forward_drift": float(forward_drift),
        "backward_drift": float(backward_drift),
        "lateral_drift": float(lateral_drift),
        "vertical_drift": float(vertical_drift)
    }


def check_identity_consistency(session_id: str) -> Dict[str, Any]:
    """
    Track AI self-reference consistency.
    
    Returns:
        {
            "name_consistency": float,
            "role_consistency": float,
            "location_consistency": float,
            "violations": [(turn, issue)]
        }
    """
    turns = get_session_turns(session_id)
    
    if not turns:
        return {
            "name_consistency": 1.0,
            "role_consistency": 1.0,
            "location_consistency": 1.0,
            "violations": []
        }
    
    # Check for identity-related overrides
    identity_keywords = ["navn", "name", "heter", "called", "jeg er", "i am"]
    location_keywords = ["bor", "live", "location", "oslo", "norway"]
    
    name_checks = 0
    name_violations = 0
    location_checks = 0
    location_violations = 0
    violations = []
    
    for i, turn in enumerate(turns):
        user_msg = turn.get("user_message", "").lower()
        was_overridden = turn.get("was_overridden", False)
        conflict_reason = turn.get("conflict_reason", "")
        
        # Check name consistency
        if any(kw in user_msg for kw in identity_keywords):
            name_checks += 1
            if was_overridden and "identity" in conflict_reason.lower():
                name_violations += 1
                violations.append((i + 1, f"Name: {conflict_reason}"))
        
        # Check location consistency
        if any(kw in user_msg for kw in location_keywords):
            location_checks += 1
            if was_overridden and "location" in conflict_reason.lower():
                location_violations += 1
                violations.append((i + 1, f"Location: {conflict_reason}"))
    
    name_consistency = 1.0 - (name_violations / name_checks) if name_checks > 0 else 1.0
    location_consistency = 1.0 - (location_violations / location_checks) if location_checks > 0 else 1.0
    
    # Role consistency (simplified - based on no role-related overrides)
    role_checks = len(turns)
    role_violations = sum(
        1 for t in turns 
        if t.get("was_overridden") and "role" in t.get("conflict_reason", "").lower()
    )
    role_consistency = 1.0 - (role_violations / role_checks) if role_checks > 0 else 1.0
    
    return {
        "name_consistency": float(name_consistency),
        "role_consistency": float(role_consistency),
        "location_consistency": float(location_consistency),
        "violations": violations
    }


def generate_session_report(session_id: str) -> str:
    """
    Generate comprehensive session analysis report.
    
    Returns:
        Formatted text report
    """
    state = get_session_state(session_id)
    patterns = analyze_session_patterns(session_id)
    drift = detect_cognitive_drift(session_id)
    consistency = check_identity_consistency(session_id)
    
    report = []
    report.append("=" * 60)
    report.append(f"SESSION ANALYSIS: {session_id}")
    report.append("=" * 60)
    report.append("")
    
    # Session state
    report.append("📊 SESSION STATE:")
    report.append(f"   Turns: {state['turn_count']}")
    report.append(f"   Time span: {state['time_span']:.1f}s ({state['time_span']/60:.1f}min)")
    report.append(f"   Domains visited: {', '.join(state['domains_visited'][:5])}")
    report.append(f"   Override rate: {state['override_rate']:.1%}")
    report.append(f"   Average GNN: {state['average_gnn']:.3f}")
    report.append(f"   Field entropy: {state['field_entropy']:.3f}")
    report.append("")
    
    # Patterns
    report.append("🔍 PATTERNS:")
    if patterns['common_domains']:
        report.append("   Common domains:")
        for domain, count in patterns['common_domains'][:3]:
            report.append(f"      • {domain}: {count} turns")
    
    if patterns['override_triggers']:
        report.append("   Override triggers:")
        for reason, count in patterns['override_triggers'][:3]:
            report.append(f"      • {reason}: {count}x")
    
    if patterns['high_gnn_topics']:
        report.append("   High EFC resonance:")
        for domain, gnn in patterns['high_gnn_topics'][:3]:
            report.append(f"      • {domain}: {gnn:.3f}")
    
    if patterns['convergence_points']:
        report.append(f"   Convergence points: turns {patterns['convergence_points']}")
    
    report.append("")
    
    # Drift
    report.append("📈 COGNITIVE DRIFT:")
    report.append(f"   Forward drift: {drift['forward_drift']:.3f} (building)")
    report.append(f"   Lateral drift: {drift['lateral_drift']:.3f} (domain hopping)")
    report.append(f"   Backward drift: {drift['backward_drift']:.3f} (revisiting)")
    report.append(f"   Vertical drift: {drift['vertical_drift']:.3f} (abstraction)")
    report.append("")
    
    # Consistency
    report.append("✅ IDENTITY CONSISTENCY:")
    report.append(f"   Name: {consistency['name_consistency']:.1%}")
    report.append(f"   Role: {consistency['role_consistency']:.1%}")
    report.append(f"   Location: {consistency['location_consistency']:.1%}")
    
    if consistency['violations']:
        report.append("   Violations:")
        for turn, issue in consistency['violations'][:5]:
            report.append(f"      • Turn {turn}: {issue}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Pattern Analyzer CLI")
    parser.add_argument("--session-id", required=True, help="Session ID")
    parser.add_argument("--action", 
                       choices=["patterns", "drift", "consistency", "report"], 
                       default="report",
                       help="Analysis to perform")
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.action == "patterns":
        result = analyze_session_patterns(args.session_id)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Common domains:", result["common_domains"])
            print("Override triggers:", result["override_triggers"])
            print("High GNN topics:", result["high_gnn_topics"])
    
    elif args.action == "drift":
        result = detect_cognitive_drift(args.session_id)
        print(json.dumps(result, indent=2))
    
    elif args.action == "consistency":
        result = check_identity_consistency(args.session_id)
        print(json.dumps(result, indent=2))
    
    elif args.action == "report":
        report = generate_session_report(args.session_id)
        print(report)
