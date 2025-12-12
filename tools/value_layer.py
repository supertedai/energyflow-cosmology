#!/usr/bin/env python3
"""
value_layer.py - Value Layer for Cognitive Symbiosis
=====================================================

WHAT IS IMPORTANT? (not just what user wants)

Value Layer provides:
1. Value Hierarchy - Importance classification (CRITICAL/HIGH/MEDIUM/LOW)
2. Harm Detection - Corruption/degradation/instability detection
3. Value-based Decisions - Intent + Value → Final priority

PRINSIPP: Etisk grunnlag
System skal vite FORSKJELL mellom:
- Kritisk info (identitet, helse, sikkerhet) vs trivial data
- Sannhet vs korrupsjon
- Stabilitet vs kaos
- Brukerens beste vs skade

ARKITEKTUR:
┌─────────────────────────────────────────────────────────┐
│ VALUE LAYER                                             │
│                                                         │
│  Intent Signal (what user wants)                       │
│         ↓                                               │
│  Value Hierarchy (what is important)                   │
│         ↓                                               │
│  Harm Detection (detect damage)                        │
│         ↓                                               │
│  Value Decision (intent + value → priority)            │
└─────────────────────────────────────────────────────────┘

INTEGRATION:
- Meta-Supervisor: Gets value signal for weighting
- Identity Protection: Gets value hierarchy for protection levels
- Priority Gate: Gets value weights for boosting
- Self-Healing: Gets harm signal for conflict priority

PHASE 5 COMPLETION: ~400 lines
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ValueLevel(Enum):
    """Importance level hierarchy"""
    CRITICAL = "critical"    # Identity, health, safety - highest protection
    HIGH = "high"            # Truth consistency, system stability
    MEDIUM = "medium"        # Learning efficiency, user preference
    LOW = "low"              # Trivia, ephemeral data


class HarmType(Enum):
    """Types of system harm"""
    IDENTITY_CORRUPTION = "identity_corruption"    # Morpheus → Morten type errors
    TRUTH_DEGRADATION = "truth_degradation"        # Canonical → low-trust downgrades
    SYSTEM_INSTABILITY = "system_instability"      # Oscillation, drift beyond thresholds
    USER_HARM = "user_harm"                        # Harmful content, manipulation


@dataclass
class ValueSignal:
    """Value signal for a fact/chunk/decision"""
    signal_id: str
    value_level: ValueLevel
    domains: List[str]           # Which domains this applies to
    reasoning: str               # Why this value level
    override_intent: bool = False  # Should value override intent?
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "value_level": self.value_level.value,
            "domains": self.domains,
            "reasoning": self.reasoning,
            "override_intent": self.override_intent,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class HarmSignal:
    """Harm detection signal"""
    signal_id: str
    harm_type: HarmType
    severity: float              # 0.0-1.0 (0=no harm, 1=critical harm)
    affected_domains: List[str]
    evidence: List[str]          # What triggered detection
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "harm_type": self.harm_type.value,
            "severity": self.severity,
            "affected_domains": self.affected_domains,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ValueDecision:
    """Final priority decision combining intent + value"""
    decision_id: str
    intent_mode: str             # From IntentSignal
    value_level: ValueLevel
    final_priority: float        # 0.0-1.0 (final weight)
    reasoning: str
    harm_detected: bool = False
    harm_signals: List[HarmSignal] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id,
            "intent_mode": self.intent_mode,
            "value_level": self.value_level.value,
            "final_priority": self.final_priority,
            "reasoning": self.reasoning,
            "harm_detected": self.harm_detected,
            "harm_signals": [h.to_dict() for h in self.harm_signals],
            "timestamp": self.timestamp.isoformat()
        }


class ValueHierarchy:
    """
    VALUE HIERARCHY
    
    Klassifiserer viktighet av domener, keys, facts.
    
    CRITICAL: Identitet, helse, sikkerhet
    HIGH: Sannhet, stabilitet
    MEDIUM: Effektivitet, preferanser
    LOW: Trivia, ephemeral data
    """
    
    def __init__(self):
        # Domain → Value Level mapping
        self.domain_values = {
            "identity": ValueLevel.CRITICAL,
            "health": ValueLevel.CRITICAL,
            "safety": ValueLevel.CRITICAL,
            "system_name": ValueLevel.CRITICAL,
            
            "efc_theory": ValueLevel.HIGH,
            "canonical_memory": ValueLevel.HIGH,
            "system_stability": ValueLevel.HIGH,
            
            "user_preference": ValueLevel.MEDIUM,
            "learning_efficiency": ValueLevel.MEDIUM,
            "system_config": ValueLevel.MEDIUM,
            
            "trivia": ValueLevel.LOW,
            "temporary": ValueLevel.LOW,
            "experimental": ValueLevel.LOW
        }
        
        # Key patterns → Value Level
        self.key_patterns = {
            ValueLevel.CRITICAL: [
                "user.name", "system.name", "identity",
                "health", "safety", "security"
            ],
            ValueLevel.HIGH: [
                "canonical", "truth", "theory", "stability",
                "core_concept", "foundation"
            ],
            ValueLevel.MEDIUM: [
                "preference", "setting", "config",
                "efficiency", "performance"
            ],
            ValueLevel.LOW: [
                "temp", "test", "experiment", "draft",
                "trivial", "ephemeral"
            ]
        }
    
    def classify_value(
        self,
        key: Optional[str] = None,
        domain: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ValueSignal:
        """
        Classify value level for a fact/chunk.
        
        Args:
            key: Fact key (e.g., "user.name")
            domain: Domain (e.g., "identity")
            content: Content text
            metadata: Additional metadata
        
        Returns:
            ValueSignal with classification
        """
        value_level = ValueLevel.LOW  # Default
        reasoning_parts = []
        domains = []
        
        # Check domain
        if domain:
            domains.append(domain)
            if domain in self.domain_values:
                value_level = self.domain_values[domain]
                reasoning_parts.append(f"domain={domain}")
        
        # Check key patterns
        if key:
            for level, patterns in self.key_patterns.items():
                if any(p in key.lower() for p in patterns):
                    # Take highest level
                    if level.value == "critical" or (level.value == "high" and value_level != ValueLevel.CRITICAL):
                        value_level = level
                        reasoning_parts.append(f"key_pattern={key}")
                        break
        
        # Check content keywords
        if content:
            content_lower = content.lower()
            if any(kw in content_lower for kw in ["identity", "name", "who am i", "critical"]):
                if value_level not in [ValueLevel.CRITICAL]:
                    value_level = ValueLevel.CRITICAL
                    reasoning_parts.append("content=identity_keywords")
        
        # Check metadata
        if metadata:
            if metadata.get("trust_score", 0) >= 0.95:
                reasoning_parts.append("high_trust")
            if metadata.get("is_canonical"):
                if value_level not in [ValueLevel.CRITICAL, ValueLevel.HIGH]:
                    value_level = ValueLevel.HIGH
                    reasoning_parts.append("canonical")
        
        # Override detection
        override_intent = value_level == ValueLevel.CRITICAL
        
        reasoning = " + ".join(reasoning_parts) if reasoning_parts else "default_low"
        
        return ValueSignal(
            signal_id=f"value_{datetime.now().timestamp()}",
            value_level=value_level,
            domains=domains if domains else ["general"],
            reasoning=reasoning,
            override_intent=override_intent
        )


class HarmDetector:
    """
    HARM DETECTION
    
    Oppdager skade på system:
    - Identity corruption (Morpheus → Morten feil)
    - Truth degradation (canonical → low-trust)
    - System instability (oscillation, drift)
    - User harm (harmful content)
    """
    
    def __init__(self):
        self.harm_history: List[HarmSignal] = []
        
        # Blocked patterns (identity corruption)
        self.blocked_identity_patterns = [
            "morpheus", "test", "cli_test", "unknown", "undefined"
        ]
        
        # Harmful content patterns
        self.harmful_patterns = [
            "manipulate", "deceive", "corrupt", "destroy"
        ]
        
        # EFC truth protection - korrekte definisjoner
        self.efc_canonical_truths = {
            "efc.acronym": "Energy-Flow Cosmology",
            "efc.definition": "Energy-Flow Cosmology",
            "efc.name": "Energy-Flow Cosmology",
            "efc.full_name": "Energy-Flow Cosmology"
        }
        
        # Feil EFC-definisjoner som skal blokkeres
        self.blocked_efc_patterns = [
            "enhanced functionality",
            "efficient function",
            "electric flow",
            "electromagnetic field control"
        ]
    
    def detect_identity_corruption(
        self,
        key: str,
        proposed_value: str,
        canonical_value: Optional[str],
        trust_score: float
    ) -> Optional[HarmSignal]:
        """
        Detect identity corruption attempts.
        
        Example: user.name = "Morpheus" when canonical is "Morten"
        """
        # Check blocked patterns
        if any(pattern in proposed_value.lower() for pattern in self.blocked_identity_patterns):
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.IDENTITY_CORRUPTION,
                severity=1.0,  # Critical
                affected_domains=["identity"],
                evidence=[
                    f"Blocked pattern detected: {proposed_value}",
                    f"Key: {key}"
                ],
                recommended_action="BLOCK_UPDATE"
            )
        
        # Check trust score
        if key in ["user.name", "system.name"] and trust_score < 0.95:
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.IDENTITY_CORRUPTION,
                severity=0.8,
                affected_domains=["identity"],
                evidence=[
                    f"Low trust score: {trust_score} < 0.95",
                    f"Key: {key}, Value: {proposed_value}"
                ],
                recommended_action="REQUIRE_VALIDATION"
            )
        
        # Check canonical mismatch
        if canonical_value and canonical_value != proposed_value and trust_score < 0.9:
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.IDENTITY_CORRUPTION,
                severity=0.7,
                affected_domains=["identity"],
                evidence=[
                    f"Canonical mismatch: {canonical_value} != {proposed_value}",
                    f"Trust: {trust_score}"
                ],
                recommended_action="USE_CANONICAL"
            )
        
        return None
    
    def detect_efc_truth_corruption(
        self,
        key: str,
        proposed_value: str
    ) -> Optional[HarmSignal]:
        """
        Detect EFC truth corruption attempts.
        
        Blocks wrong definitions like "Enhanced Functionality Computing"
        when EFC must be "Energy-Flow Cosmology".
        """
        proposed_lower = proposed_value.lower()
        
        # Check if this is an EFC-related key
        if any(efc_key in key.lower() for efc_key in ["efc", "energy-flow", "energyflow"]):
            
            # Check for blocked EFC patterns (wrong definitions)
            for blocked in self.blocked_efc_patterns:
                if blocked in proposed_lower:
                    return HarmSignal(
                        signal_id=f"harm_{datetime.now().timestamp()}",
                        harm_type=HarmType.TRUTH_DEGRADATION,
                        severity=1.0,  # Critical - this is wrong EFC definition
                        affected_domains=["efc_theory", "canonical_memory"],
                        evidence=[
                            f"Wrong EFC definition attempted: '{proposed_value}'",
                            f"Blocked pattern: '{blocked}'",
                            "EFC must be 'Energy-Flow Cosmology'"
                        ],
                        recommended_action="BLOCK_UPDATE"
                    )
            
            # Check if canonical EFC key exists and is being changed
            if key in self.efc_canonical_truths:
                canonical = self.efc_canonical_truths[key]
                if canonical.lower() not in proposed_lower:
                    return HarmSignal(
                        signal_id=f"harm_{datetime.now().timestamp()}",
                        harm_type=HarmType.TRUTH_DEGRADATION,
                        severity=0.9,
                        affected_domains=["efc_theory", "canonical_memory"],
                        evidence=[
                            f"EFC canonical violation: key={key}",
                            f"Expected: '{canonical}'",
                            f"Got: '{proposed_value}'"
                        ],
                        recommended_action="USE_CANONICAL"
                    )
        
        return None

    def detect_truth_degradation(
        self,
        fact_key: str,
        old_trust: float,
        new_trust: float,
        is_canonical: bool
    ) -> Optional[HarmSignal]:
        """
        Detect truth degradation (canonical → low-trust downgrade).
        """
        # Canonical being downgraded
        if is_canonical and new_trust < old_trust:
            severity = (old_trust - new_trust)  # 0.0-1.0
            
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.TRUTH_DEGRADATION,
                severity=severity,
                affected_domains=["canonical_memory"],
                evidence=[
                    f"Canonical fact downgrade: {fact_key}",
                    f"Trust: {old_trust} → {new_trust}"
                ],
                recommended_action="PRESERVE_CANONICAL"
            )
        
        # Significant trust drop
        if old_trust - new_trust > 0.3:
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.TRUTH_DEGRADATION,
                severity=0.6,
                affected_domains=["memory"],
                evidence=[
                    f"Significant trust drop: {old_trust} → {new_trust}",
                    f"Key: {fact_key}"
                ],
                recommended_action="INVESTIGATE_CAUSE"
            )
        
        return None
    
    def detect_system_instability(
        self,
        oscillation_rate: float,
        drift_score: float,
        stability_level: str
    ) -> Optional[HarmSignal]:
        """
        Detect system instability (oscillation, drift).
        """
        evidence = []
        severity = 0.0
        
        # High oscillation
        if oscillation_rate > 5.0:
            evidence.append(f"High oscillation: {oscillation_rate:.1f} changes/hour")
            severity = max(severity, 0.7)
        
        # Significant drift
        if drift_score > 0.3:
            evidence.append(f"Drift detected: {drift_score:.1%}")
            severity = max(severity, 0.6)
        
        # Critical stability
        if stability_level == "critical":
            evidence.append("System stability: CRITICAL")
            severity = 1.0
        
        if evidence:
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.SYSTEM_INSTABILITY,
                severity=severity,
                affected_domains=["system_stability"],
                evidence=evidence,
                recommended_action="STABILIZE_SYSTEM"
            )
        
        return None
    
    def detect_user_harm(
        self,
        content: str,
        intent_mode: str
    ) -> Optional[HarmSignal]:
        """
        Detect harmful content or manipulation attempts.
        """
        content_lower = content.lower()
        
        # Check harmful patterns
        harmful_detected = [
            pattern for pattern in self.harmful_patterns
            if pattern in content_lower
        ]
        
        if harmful_detected:
            return HarmSignal(
                signal_id=f"harm_{datetime.now().timestamp()}",
                harm_type=HarmType.USER_HARM,
                severity=0.8,
                affected_domains=["user_interaction"],
                evidence=[
                    f"Harmful patterns: {harmful_detected}",
                    f"Content preview: {content[:100]}"
                ],
                recommended_action="FILTER_CONTENT"
            )
        
        return None


class ValueDecisionMaker:
    """
    VALUE DECISION MAKER
    
    Kombinerer intent + value → final priority.
    
    Rules:
    - CRITICAL value → Always high priority (override intent)
    - HIGH value + PROTECTION intent → Maximum priority
    - LOW value + LEARNING intent → Normal priority
    - Harm detected → Override to protection mode
    """
    
    def __init__(self):
        self.decisions: List[ValueDecision] = []
        
        # Value level → base priority mapping
        self.value_priorities = {
            ValueLevel.CRITICAL: 1.0,
            ValueLevel.HIGH: 0.75,
            ValueLevel.MEDIUM: 0.5,
            ValueLevel.LOW: 0.25
        }
        
        # Intent mode → priority modifier
        self.intent_modifiers = {
            "protection": 1.2,    # Boost protection
            "learning": 1.0,      # Normal
            "consolidation": 0.9,
            "retrieval": 0.8,
            "exploration": 0.7
        }
    
    def make_decision(
        self,
        intent_signal: Dict[str, Any],
        value_signal: ValueSignal,
        harm_signals: List[HarmSignal]
    ) -> ValueDecision:
        """
        Make final priority decision.
        
        Args:
            intent_signal: From IntentEngine (what user wants)
            value_signal: From ValueHierarchy (what is important)
            harm_signals: From HarmDetector (what is damaged)
        
        Returns:
            ValueDecision with final priority
        """
        intent_mode = intent_signal.get("mode", "retrieval")
        
        # Base priority from value level
        base_priority = self.value_priorities[value_signal.value_level]
        
        # Modify by intent
        intent_modifier = self.intent_modifiers.get(intent_mode, 1.0)
        final_priority = base_priority * intent_modifier
        
        # Cap at 1.0
        final_priority = min(final_priority, 1.0)
        
        reasoning_parts = [
            f"value={value_signal.value_level.value}",
            f"intent={intent_mode}",
            f"base={base_priority:.2f}",
            f"modifier={intent_modifier:.2f}"
        ]
        
        # Check for harm
        harm_detected = len(harm_signals) > 0
        
        if harm_detected:
            # Critical harm → maximum priority
            max_harm_severity = max(h.severity for h in harm_signals)
            if max_harm_severity >= 0.8:
                final_priority = 1.0
                reasoning_parts.append("CRITICAL_HARM_OVERRIDE")
            else:
                final_priority = max(final_priority, 0.8)
                reasoning_parts.append("harm_detected")
        
        # Critical value override
        if value_signal.override_intent:
            final_priority = 1.0
            reasoning_parts.append("CRITICAL_VALUE_OVERRIDE")
        
        reasoning = " → ".join(reasoning_parts)
        
        decision = ValueDecision(
            decision_id=f"decision_{datetime.now().timestamp()}",
            intent_mode=intent_mode,
            value_level=value_signal.value_level,
            final_priority=final_priority,
            reasoning=reasoning,
            harm_detected=harm_detected,
            harm_signals=harm_signals
        )
        
        self.decisions.append(decision)
        
        return decision


class ValueLayer:
    """
    VALUE LAYER - Full integration
    
    Provides WHAT IS IMPORTANT (not just what user wants).
    
    Components:
    1. ValueHierarchy - Classify importance
    2. HarmDetector - Detect damage
    3. ValueDecisionMaker - Intent + Value → Priority
    
    USAGE:
        value_layer = ValueLayer()
        
        # Classify a fact's value
        value_signal = value_layer.classify_value(
            key="user.name",
            domain="identity",
            content="Morten"
        )
        
        # Detect harm
        harm = value_layer.detect_harm(
            key="user.name",
            proposed_value="Morpheus",
            canonical_value="Morten",
            trust_score=0.5
        )
        
        # Make final decision
        decision = value_layer.make_decision(
            intent_signal={"mode": "protection"},
            key="user.name",
            domain="identity",
            content="Morten"
        )
        
        print(f"Final priority: {decision.final_priority}")
        print(f"Reasoning: {decision.reasoning}")
    """
    
    def __init__(self):
        self.hierarchy = ValueHierarchy()
        self.harm_detector = HarmDetector()
        self.decision_maker = ValueDecisionMaker()
    
    def classify_value(
        self,
        key: Optional[str] = None,
        domain: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ValueSignal:
        """Classify value level"""
        return self.hierarchy.classify_value(key, domain, content, metadata)
    
    def detect_harm(
        self,
        key: str,
        proposed_value: str,
        canonical_value: Optional[str] = None,
        trust_score: float = 0.5,
        old_trust: Optional[float] = None,
        is_canonical: bool = False,
        content: Optional[str] = None,
        intent_mode: str = "retrieval",
        oscillation_rate: float = 0.0,
        drift_score: float = 0.0,
        stability_level: str = "stable"
    ) -> List[HarmSignal]:
        """Detect all types of harm"""
        harm_signals = []
        
        # Identity corruption
        identity_harm = self.harm_detector.detect_identity_corruption(
            key, proposed_value, canonical_value, trust_score
        )
        if identity_harm:
            harm_signals.append(identity_harm)
        
        # EFC truth corruption - blokkerer feil EFC-definisjoner
        efc_harm = self.harm_detector.detect_efc_truth_corruption(
            key, proposed_value
        )
        if efc_harm:
            harm_signals.append(efc_harm)
        
        # Also check content for wrong EFC definitions
        if content:
            efc_content_harm = self.harm_detector.detect_efc_truth_corruption(
                "efc.content", content
            )
            if efc_content_harm:
                harm_signals.append(efc_content_harm)
        
        # Truth degradation
        if old_trust is not None:
            truth_harm = self.harm_detector.detect_truth_degradation(
                key, old_trust, trust_score, is_canonical
            )
            if truth_harm:
                harm_signals.append(truth_harm)
        
        # System instability
        stability_harm = self.harm_detector.detect_system_instability(
            oscillation_rate, drift_score, stability_level
        )
        if stability_harm:
            harm_signals.append(stability_harm)
        
        # User harm
        if content:
            user_harm = self.harm_detector.detect_user_harm(content, intent_mode)
            if user_harm:
                harm_signals.append(user_harm)
        
        return harm_signals
    
    def make_decision(
        self,
        intent_signal: Dict[str, Any],
        key: Optional[str] = None,
        domain: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        harm_context: Optional[Dict] = None
    ) -> ValueDecision:
        """
        Make final priority decision combining intent + value.
        
        Args:
            intent_signal: From IntentEngine
            key: Fact key
            domain: Domain
            content: Content
            metadata: Additional metadata
            harm_context: Context for harm detection
        
        Returns:
            ValueDecision with final priority
        """
        # Classify value
        value_signal = self.classify_value(key, domain, content, metadata)
        
        # Detect harm if context provided
        harm_signals = []
        if harm_context:
            harm_signals = self.detect_harm(**harm_context)
        
        # Make decision
        decision = self.decision_maker.make_decision(
            intent_signal,
            value_signal,
            harm_signals
        )
        
        return decision
    
    def get_stats(self) -> Dict:
        """Get value layer statistics"""
        return {
            "total_decisions": len(self.decision_maker.decisions),
            "total_harms_detected": len(self.harm_detector.harm_history),
            "harm_by_type": {
                harm_type.value: sum(
                    1 for h in self.harm_detector.harm_history
                    if h.harm_type == harm_type
                )
                for harm_type in HarmType
            }
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Value Layer")
    print("=" * 60)
    
    value_layer = ValueLayer()
    
    # Test 1: Critical value (identity)
    print("\n1️⃣ Test: Critical value classification")
    value_signal = value_layer.classify_value(
        key="user.name",
        domain="identity",
        content="Morten",
        metadata={"trust_score": 0.95}
    )
    print(f"Key: user.name")
    print(f"Value level: {value_signal.value_level.value}")
    print(f"Reasoning: {value_signal.reasoning}")
    print(f"Override intent: {value_signal.override_intent}")
    
    # Test 2: Harm detection (identity corruption)
    print("\n2️⃣ Test: Identity corruption detection")
    harm_signals = value_layer.detect_harm(
        key="user.name",
        proposed_value="Morpheus",
        canonical_value="Morten",
        trust_score=0.5
    )
    print(f"Harms detected: {len(harm_signals)}")
    for harm in harm_signals:
        print(f"  Type: {harm.harm_type.value}")
        print(f"  Severity: {harm.severity}")
        print(f"  Action: {harm.recommended_action}")
    
    # Test 3: Value decision (protection + critical)
    print("\n3️⃣ Test: Value decision (PROTECTION + CRITICAL)")
    decision = value_layer.make_decision(
        intent_signal={"mode": "protection"},
        key="user.name",
        domain="identity",
        content="Morten",
        metadata={"trust_score": 0.95},
        harm_context={
            "key": "user.name",
            "proposed_value": "Morten",
            "canonical_value": "Morten",
            "trust_score": 0.95
        }
    )
    print(f"Intent: {decision.intent_mode}")
    print(f"Value: {decision.value_level.value}")
    print(f"Final priority: {decision.final_priority:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Harm detected: {decision.harm_detected}")
    
    # Test 4: Value decision (learning + low)
    print("\n4️⃣ Test: Value decision (LEARNING + LOW)")
    decision = value_layer.make_decision(
        intent_signal={"mode": "learning"},
        key="temp.note",
        domain="temporary",
        content="Just testing"
    )
    print(f"Intent: {decision.intent_mode}")
    print(f"Value: {decision.value_level.value}")
    print(f"Final priority: {decision.final_priority:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Test 5: Stats
    print("\n5️⃣ Value Layer stats")
    import json
    stats = value_layer.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Value Layer test complete")
