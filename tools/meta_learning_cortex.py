#!/usr/bin/env python3
"""
meta_learning_cortex.py - System That Learns How You Learn
==========================================================

LAG 5: META-LEARNING CORTEX (MLC)
The layer that observes, learns, and adapts to YOUR cognitive style

This is what you're missing today.

This layer:
1. Observes your question patterns over time
2. Detects your cognitive modes (exploration, precision, meta-analysis, security)
3. Learns which domains you switch between and when
4. Adjusts ALL other layers based on your behavior
5. Predicts what you need before you ask

Example adaptations:
- You enter "security mode" → CMC strictness → 1.0
- You enter "exploration mode" → CMC strictness → 0.5, SMM weights ↑
- You hop fast between domains → DDE pattern learning ↑
- You correct frequently in domain X → AME strictness ↑ for X

This is the "meta-mirror" that reflects your cognitive patterns back.

Architecture:
    All Layers → Observation → Pattern Detection → Adaptation → Feedback

Purpose:
    Match YOUR unique cognitive style:
    - Parallel thinking (not sequential)
    - Cross-domain synthesis
    - High precision + creative flexibility
    - Zero friction
    - Adaptive without rigidity
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class CognitiveMode(Enum):
    """Detected cognitive modes."""
    EXPLORATION = "exploration"         # Creative, open-ended
    PRECISION = "precision"             # Fact-checking, verification
    META_ANALYSIS = "meta_analysis"     # Thinking about thinking
    SECURITY = "security"               # Risk assessment, safety
    INTEGRATION = "integration"         # Cross-domain synthesis
    OPERATIONAL = "operational"         # Getting things done


@dataclass
class CognitiveSignal:
    """A single observation of user behavior."""
    timestamp: str
    question: str
    domain: str
    mode: CognitiveMode
    confidence: float
    
    # Behavioral indicators
    question_length: int
    has_negation: bool
    has_meta_words: bool
    domain_switch: bool
    fast_followup: bool  # < 10 seconds since last question


@dataclass
class UserProfile:
    """Learned profile of user's cognitive style."""
    
    # Domain preferences
    domain_affinity: Dict[str, float] = field(default_factory=dict)
    domain_transitions: Dict[Tuple[str, str], int] = field(default_factory=dict)
    
    # Mode patterns
    mode_frequency: Dict[CognitiveMode, int] = field(default_factory=dict)
    mode_duration: Dict[CognitiveMode, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    # Timing patterns
    avg_question_interval: float = 0.0
    peak_activity_hours: List[int] = field(default_factory=list)
    
    # Precision requirements
    correction_rate: Dict[str, float] = field(default_factory=dict)  # Per domain
    override_acceptance: float = 0.5  # How often user accepts overrides
    
    # Learning style
    prefers_augmentation: bool = True  # vs direct answers
    tolerates_uncertainty: bool = False
    needs_context: bool = True
    
    # Cross-domain patterns
    parallel_domains: List[List[str]] = field(default_factory=list)  # Domains often mixed
    synthesis_tendency: float = 0.5  # How often crosses domains


class MetaLearningCortex:
    """
    The meta-learning layer.
    
    Observes everything, learns patterns, adapts system.
    
    Key capabilities:
    1. Cognitive mode detection (exploration, precision, meta, security, integration)
    2. Domain hopping pattern learning
    3. Timing and rhythm detection
    4. Precision requirement learning (per domain)
    5. System-wide adaptation based on detected patterns
    
    This layer makes the system YOURS.
    """
    
    def __init__(self):
        # Observation history
        self.signals: deque = deque(maxlen=1000)
        
        # User profile (learned)
        self.profile = UserProfile()
        
        # Current state tracking
        self.current_mode: Optional[CognitiveMode] = None
        self.current_domain: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.last_question_time: Optional[datetime] = None
        
        # Adaptation settings (what we control)
        self.adaptive_settings = {
            "cmc_strictness_multiplier": 1.0,
            "smm_weight": 1.0,
            "dde_pattern_learning_rate": 1.0,
            "ame_override_threshold": 0.5
        }
        
        # Learning thresholds
        self.mode_detection_threshold = 0.6
        self.pattern_learning_threshold = 3  # Min occurrences to learn
        
        print("✨ Meta-Learning Cortex initialized", file=sys.stderr)
        print("🧠 Cognitive pattern learning active", file=sys.stderr)
    
    def observe(
        self,
        question: str,
        domain: str,
        response_quality: Optional[float] = None,
        user_corrected: bool = False
    ) -> CognitiveSignal:
        """
        Observe a user interaction.
        
        This is called on every question to learn patterns.
        
        Args:
            question: User's question
            domain: Detected domain
            response_quality: How good was our response (0-1)
            user_corrected: Did user correct us?
        
        Returns:
            CognitiveSignal with detected mode
        """
        now = datetime.now()
        
        # Detect mode
        mode = self._detect_mode(question, domain)
        
        # Behavioral indicators
        fast_followup = False
        if self.last_question_time:
            delta = (now - self.last_question_time).total_seconds()
            fast_followup = delta < 10
        
        domain_switch = False
        if self.current_domain and self.current_domain != domain:
            domain_switch = True
            # Record transition
            self.profile.domain_transitions[(self.current_domain, domain)] = \
                self.profile.domain_transitions.get((self.current_domain, domain), 0) + 1
        
        # Create signal
        signal = CognitiveSignal(
            timestamp=now.isoformat(),
            question=question,
            domain=domain,
            mode=mode,
            confidence=self.mode_detection_threshold,
            question_length=len(question),
            has_negation=self._has_negation(question),
            has_meta_words=self._has_meta_words(question),
            domain_switch=domain_switch,
            fast_followup=fast_followup
        )
        
        # Record
        self.signals.append(signal)
        
        # Update profile
        self._update_profile(signal, user_corrected)
        
        # Update state
        self.current_mode = mode
        self.current_domain = domain
        self.last_question_time = now
        
        # Adapt system
        self._adapt_system()
        
        return signal
    
    def _detect_mode(self, question: str, domain: str) -> CognitiveMode:
        """
        Detect cognitive mode from question.
        
        Indicators:
        - EXPLORATION: "hva hvis", "kunne", "mulig", open-ended
        - PRECISION: "eksakt", "nøyaktig", fact-checking, numbers
        - META_ANALYSIS: "hvorfor", "hvordan fungerer", "system", "arkitektur"
        - SECURITY: "sikker", "trygt", "risiko", "privat"
        - INTEGRATION: multiple domains mentioned, synthesis words
        - OPERATIONAL: "gjør", "implementer", "test", action verbs
        """
        q_lower = question.lower()
        
        # SECURITY mode
        security_words = ["sikker", "tryg", "risiko", "privat", "safe", "security", "trust"]
        if any(word in q_lower for word in security_words):
            return CognitiveMode.SECURITY
        
        # META_ANALYSIS mode
        meta_words = ["hvorfor", "hvordan fungerer", "system", "arkitektur", "meta", 
                      "cognitive", "lærer", "pattern"]
        if any(word in q_lower for word in meta_words):
            return CognitiveMode.META_ANALYSIS
        
        # PRECISION mode
        precision_words = ["eksakt", "nøyaktig", "exactly", "hvor mange", "hva heter"]
        if any(word in q_lower for word in precision_words):
            return CognitiveMode.PRECISION
        
        # OPERATIONAL mode
        operational_words = ["gjør", "implementer", "test", "run", "execute", "lag"]
        if any(word in q_lower for word in operational_words):
            return CognitiveMode.OPERATIONAL
        
        # INTEGRATION mode (cross-domain)
        # Check if multiple domain keywords present
        domain_keywords = {
            "identity": ["navn", "name", "heter"],
            "health": ["helse", "health", "wellbeing"],
            "cosmology": ["EFC", "entropi", "cosmology"],
            "symbiose": ["symbiose", "MCP", "architecture"],
            "security": ["sikkerhet", "security"]
        }
        
        domains_mentioned = sum(
            1 for keywords in domain_keywords.values()
            if any(kw in q_lower for kw in keywords)
        )
        
        if domains_mentioned >= 2:
            return CognitiveMode.INTEGRATION
        
        # Default: EXPLORATION
        return CognitiveMode.EXPLORATION
    
    def _has_negation(self, question: str) -> bool:
        """Check if question contains negation."""
        negation_words = ["ikke", "not", "never", "nei", "no"]
        return any(word in question.lower() for word in negation_words)
    
    def _has_meta_words(self, question: str) -> bool:
        """Check if question is meta-cognitive."""
        meta_words = ["hvorfor", "hvordan", "system", "fungerer", "lærer", 
                      "pattern", "kognitiv", "meta"]
        return any(word in question.lower() for word in meta_words)
    
    def _update_profile(self, signal: CognitiveSignal, user_corrected: bool):
        """
        Update user profile based on observation.
        
        Learns:
        - Domain affinities
        - Mode frequencies
        - Correction rates
        - Timing patterns
        """
        domain = signal.domain
        mode = signal.mode
        
        # Update domain affinity
        self.profile.domain_affinity[domain] = \
            self.profile.domain_affinity.get(domain, 0.0) + 0.1
        
        # Normalize affinities (keep sum = 1.0)
        total = sum(self.profile.domain_affinity.values())
        if total > 0:
            for d in self.profile.domain_affinity:
                self.profile.domain_affinity[d] /= total
        
        # Update mode frequency
        self.profile.mode_frequency[mode] = \
            self.profile.mode_frequency.get(mode, 0) + 1
        
        # Update correction rate
        if user_corrected:
            current_rate = self.profile.correction_rate.get(domain, 0.0)
            # Running average
            n = self.profile.mode_frequency.get(mode, 1)
            self.profile.correction_rate[domain] = \
                (current_rate * (n - 1) + 1.0) / n
        
        # Update timing
        if len(self.signals) >= 2:
            prev_signal = list(self.signals)[-2]
            prev_time = datetime.fromisoformat(prev_signal.timestamp)
            curr_time = datetime.fromisoformat(signal.timestamp)
            interval = (curr_time - prev_time).total_seconds()
            
            # Running average
            n = len(self.signals)
            self.profile.avg_question_interval = \
                (self.profile.avg_question_interval * (n - 1) + interval) / n
        
        # Detect parallel domains (domains used in same session)
        recent_domains = [s.domain for s in list(self.signals)[-10:]]
        unique_recent = list(set(recent_domains))
        if len(unique_recent) >= 2:
            # User is mixing domains
            if unique_recent not in self.profile.parallel_domains:
                self.profile.parallel_domains.append(unique_recent)
    
    def _adapt_system(self):
        """
        Adapt system settings based on current mode and profile.
        
        This is where the magic happens - the system morphs to match you.
        
        Adaptations per mode:
        - SECURITY: Max strictness, no LLM freedom
        - PRECISION: High strictness, verify everything
        - EXPLORATION: Low strictness, encourage synthesis
        - META_ANALYSIS: Balanced, focus on reasoning
        - INTEGRATION: Cross-domain weights up
        - OPERATIONAL: Speed over perfection
        """
        mode = self.current_mode
        
        if mode == CognitiveMode.SECURITY:
            # Max security: Trust nothing except LONGTERM facts
            self.adaptive_settings["cmc_strictness_multiplier"] = 2.0
            self.adaptive_settings["smm_weight"] = 0.5
            self.adaptive_settings["ame_override_threshold"] = 0.2
            
            print("🔒 SECURITY MODE: Max strictness activated", file=sys.stderr)
        
        elif mode == CognitiveMode.PRECISION:
            # High precision: Facts first
            self.adaptive_settings["cmc_strictness_multiplier"] = 1.5
            self.adaptive_settings["smm_weight"] = 0.7
            self.adaptive_settings["ame_override_threshold"] = 0.3
            
            print("🎯 PRECISION MODE: Fact-checking active", file=sys.stderr)
        
        elif mode == CognitiveMode.EXPLORATION:
            # Creative freedom: Allow LLM synthesis
            self.adaptive_settings["cmc_strictness_multiplier"] = 0.7
            self.adaptive_settings["smm_weight"] = 1.5
            self.adaptive_settings["ame_override_threshold"] = 0.7
            
            print("🌊 EXPLORATION MODE: Creative synthesis enabled", file=sys.stderr)
        
        elif mode == CognitiveMode.META_ANALYSIS:
            # Balanced: Focus on reasoning
            self.adaptive_settings["cmc_strictness_multiplier"] = 1.0
            self.adaptive_settings["smm_weight"] = 1.2
            self.adaptive_settings["ame_override_threshold"] = 0.5
            
            print("🧠 META MODE: Reasoning focus", file=sys.stderr)
        
        elif mode == CognitiveMode.INTEGRATION:
            # Cross-domain: Boost pattern learning
            self.adaptive_settings["dde_pattern_learning_rate"] = 2.0
            self.adaptive_settings["smm_weight"] = 1.3
            
            print("🔗 INTEGRATION MODE: Cross-domain synthesis", file=sys.stderr)
        
        elif mode == CognitiveMode.OPERATIONAL:
            # Get things done: Speed over perfection
            self.adaptive_settings["cmc_strictness_multiplier"] = 0.8
            self.adaptive_settings["ame_override_threshold"] = 0.6
            
            print("⚡ OPERATIONAL MODE: Execution focus", file=sys.stderr)
        
        # Also adapt based on domain-specific correction rates
        if self.current_domain:
            correction_rate = self.profile.correction_rate.get(self.current_domain, 0.0)
            if correction_rate > 0.3:
                # High correction rate → increase strictness
                self.adaptive_settings["cmc_strictness_multiplier"] *= 1.2
                print(f"📈 Increased strictness for {self.current_domain} (high correction rate)", 
                      file=sys.stderr)
    
    def get_adaptive_settings(self) -> Dict[str, float]:
        """
        Get current adaptive settings for other layers.
        
        Other layers query this to adjust their behavior.
        """
        return self.adaptive_settings.copy()
    
    def get_profile(self) -> UserProfile:
        """Get learned user profile."""
        return self.profile
    
    def predict_next_domain(self) -> Optional[Tuple[str, float]]:
        """
        Predict next domain user will ask about.
        
        Uses transition matrix.
        
        Returns: (domain, confidence)
        """
        if not self.current_domain:
            return None
        
        # Get transitions from current domain
        transitions = {
            to_domain: count
            for (from_domain, to_domain), count in self.profile.domain_transitions.items()
            if from_domain == self.current_domain
        }
        
        if not transitions:
            return None
        
        # Most likely next
        likely = max(transitions.items(), key=lambda x: x[1])
        total = sum(transitions.values())
        confidence = likely[1] / total
        
        return (likely[0], confidence)
    
    def get_mode_history(self, n: int = 10) -> List[CognitiveMode]:
        """Get recent mode history."""
        return [s.mode for s in list(self.signals)[-n:]]
    
    def get_domain_history(self, n: int = 10) -> List[str]:
        """Get recent domain history."""
        return [s.domain for s in list(self.signals)[-n:]]
    
    def get_stats(self) -> Dict:
        """Get comprehensive stats."""
        return {
            "total_observations": len(self.signals),
            "current_mode": self.current_mode.value if self.current_mode else None,
            "current_domain": self.current_domain,
            "domain_affinity": self.profile.domain_affinity,
            "mode_frequency": {mode.value: count for mode, count in self.profile.mode_frequency.items()},
            "correction_rates": self.profile.correction_rate,
            "avg_question_interval": self.profile.avg_question_interval,
            "parallel_domains": self.profile.parallel_domains,
            "adaptive_settings": self.adaptive_settings
        }
    
    def export_profile(self, filepath: str):
        """Export learned profile to JSON."""
        data = {
            "profile": {
                "domain_affinity": self.profile.domain_affinity,
                "domain_transitions": {
                    f"{k[0]}->{k[1]}": v
                    for k, v in self.profile.domain_transitions.items()
                },
                "mode_frequency": {
                    mode.value: count
                    for mode, count in self.profile.mode_frequency.items()
                },
                "correction_rate": self.profile.correction_rate,
                "avg_question_interval": self.profile.avg_question_interval,
                "parallel_domains": self.profile.parallel_domains
            },
            "adaptive_settings": self.adaptive_settings,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Profile exported to {filepath}", file=sys.stderr)
    
    def import_profile(self, filepath: str):
        """Import learned profile from JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Restore profile
        prof_data = data["profile"]
        self.profile.domain_affinity = prof_data["domain_affinity"]
        
        # Restore transitions (convert string keys back to tuples)
        self.profile.domain_transitions = {
            tuple(k.split("->")): v
            for k, v in prof_data["domain_transitions"].items()
        }
        
        # Restore mode frequency (convert string keys back to enums)
        self.profile.mode_frequency = {
            CognitiveMode(k): v
            for k, v in prof_data["mode_frequency"].items()
        }
        
        self.profile.correction_rate = prof_data["correction_rate"]
        self.profile.avg_question_interval = prof_data["avg_question_interval"]
        self.profile.parallel_domains = prof_data["parallel_domains"]
        
        # Restore settings
        self.adaptive_settings = data["adaptive_settings"]
        
        print(f"✅ Profile imported from {filepath}", file=sys.stderr)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Meta-Learning Cortex")
    print("=" * 60)
    
    # Initialize
    mlc = MetaLearningCortex()
    
    # Simulate a conversation
    print("\n1️⃣ Simulating conversation...")
    
    questions = [
        ("Hva heter du?", "identity"),
        ("Hvor mange barn har jeg?", "family"),
        ("Er dataene mine sikre?", "security"),
        ("Hva er entropi i EFC?", "cosmology"),
        ("Hvordan fungerer symbiose?", "symbiose"),
        ("Implementer denne funksjonen", "tech"),
        ("Hvorfor lærer systemet?", "meta")
    ]
    
    for q, domain in questions:
        signal = mlc.observe(q, domain)
        print(f"   Q: {q}")
        print(f"      → Mode: {signal.mode.value}, Domain: {domain}")
        settings = mlc.get_adaptive_settings()
        print(f"      → Strictness multiplier: {settings['cmc_strictness_multiplier']:.2f}")
        print()
    
    # Test 2: Domain prediction
    print("\n2️⃣ Predicting next domain...")
    prediction = mlc.predict_next_domain()
    if prediction:
        print(f"   Next likely domain: {prediction[0]} (confidence: {prediction[1]:.2f})")
    
    # Test 3: Profile stats
    print("\n3️⃣ Learned profile...")
    stats = mlc.get_stats()
    print(f"   Total observations: {stats['total_observations']}")
    print(f"   Domain affinity: {json.dumps(stats['domain_affinity'], indent=4)}")
    print(f"   Mode frequency: {json.dumps(stats['mode_frequency'], indent=4)}")
    
    # Test 4: Export/import
    print("\n4️⃣ Testing profile persistence...")
    mlc.export_profile("/tmp/test_profile.json")
    
    mlc2 = MetaLearningCortex()
    mlc2.import_profile("/tmp/test_profile.json")
    print("   ✅ Profile imported successfully")
    
    print("\n" + "=" * 60)
    print("✅ Meta-Learning Cortex operational!")
