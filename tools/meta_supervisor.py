#!/usr/bin/env python3
"""
meta_supervisor.py - Meta-Supervisor Layer
===========================================

Top-down/bottom-up balance controller for cognitive symbiosis.

PRINSIPP: Kognitiv isomorfi
System skal matche brukerens tenkemåte:
- Bottom-up: Data → Pattern (SMM, Observations, Neo4j)
- Top-down: Intent → Frame (Priority, Focus, Filtering)
- Meta-lag: Balance + Stability + Direction

ARKITEKTUR:
1. Intent Engine - "Hva er viktig nå?"
2. Priority Gating - Filtrer irrelevant (se priority_gate.py)
3. Balance Controller - Bottom-up vs top-down vekting
4. Stability Monitor - Drift detection + prevention
5. Identity Protection - Hindrer identitetsskader (se identity_protection.py)
6. Value Layer - "Hva er VIKTIG?" (se value_layer.py)

Dette er den kognitive isomorfien - systemet tenker som deg.

INTEGRASJON:
- Self-Optimizing Layer: Får intent signal for parameter tuning
- Self-Healing: Får prioritetsvekter for conflict resolution
- AME: Får balance signal for override strength
- CMC: Får domain focus for fact promotion
- Router: Får stability signal for routing decisions
- Value Layer: Får intent signal, sender value priority tilbake

PHASE 4.2 ADDITIONS:
- Priority gate available via tools.priority_gate.PriorityGate
- Identity protection available via tools.identity_protection.IdentityProtection
- Real oscillation tracking in StabilityMonitor

PHASE 5 ADDITIONS:
- Value layer available via tools.value_layer.ValueLayer
- Value-based decision making (intent + value → priority)
- Harm detection integration

PHASE 6 ADDITIONS:
- Motivational dynamics available via tools.motivational_dynamics.MotivationalDynamics
- Internal goals, preferences, persistence, self-regulation
- Agency simulation layer
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class IntentMode(Enum):
    """System intent mode - hva er viktig nå?"""
    LEARNING = "learning"           # Bygge ny kunnskap
    RETRIEVAL = "retrieval"         # Hente eksisterende kunnskap
    CONSOLIDATION = "consolidation" # Stabilisere/organisere
    EXPLORATION = "exploration"     # Oppdage nye mønstre
    PROTECTION = "protection"       # Beskytte identitet/konsistens


class BalanceState(Enum):
    """Balance mellom bottom-up og top-down"""
    BOTTOM_UP_DOMINANT = "bottom_up_dominant"     # Data driver
    TOP_DOWN_DOMINANT = "top_down_dominant"       # Intent driver
    BALANCED = "balanced"                         # 50/50
    ADAPTIVE = "adaptive"                         # Context-dependent


class StabilityLevel(Enum):
    """System stability status"""
    STABLE = "stable"               # Alt ok
    DRIFT_DETECTED = "drift"        # Avvik fra baseline
    OSCILLATING = "oscillating"     # Ustabil switching
    DEGRADING = "degrading"         # Performance falloff
    CRITICAL = "critical"           # Krever intervensjon


@dataclass
class IntentSignal:
    """Intent signal fra meta-supervisor"""
    signal_id: str
    mode: IntentMode
    active_domains: List[str]       # Hvilke domener er aktive
    priority_keys: List[str]        # Hvilke keys er viktige
    ignore_patterns: List[str]      # Hva skal ignoreres
    timestamp: datetime
    strength: float = 1.0           # 0.0-1.0
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "mode": self.mode.value,
            "active_domains": self.active_domains,
            "priority_keys": self.priority_keys,
            "ignore_patterns": self.ignore_patterns,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength
        }


@dataclass
class BalanceMetric:
    """Balance metric - bottom-up vs top-down"""
    metric_id: str
    bottom_up_weight: float         # 0.0-1.0
    top_down_weight: float          # 0.0-1.0
    state: BalanceState
    timestamp: datetime
    reason: str
    
    def to_dict(self) -> Dict:
        return {
            "metric_id": self.metric_id,
            "bottom_up_weight": self.bottom_up_weight,
            "top_down_weight": self.top_down_weight,
            "state": self.state.value,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason
        }


@dataclass
class StabilityReport:
    """Stability report fra monitoring"""
    report_id: str
    level: StabilityLevel
    drift_score: float              # 0.0-1.0 (0=no drift)
    oscillation_rate: float         # Changes per hour
    degradation_rate: float         # Performance decline per hour
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "level": self.level.value,
            "drift_score": self.drift_score,
            "oscillation_rate": self.oscillation_rate,
            "degradation_rate": self.degradation_rate,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat()
        }


class IntentEngine:
    """
    INTENT ENGINE
    
    Bestemmer "hva er viktig nå?" basert på context + history.
    
    Top-down signal som styrer alle andre lag.
    """
    
    def __init__(self):
        self.current_intent: Optional[IntentSignal] = None
        self.intent_history: List[IntentSignal] = []
        
        # Intent detection rules
        self.intent_patterns = {
            "learning": ["hva er", "forklar", "hvordan", "læring", "ny"],
            "retrieval": ["henter", "recall", "husker", "tidligere", "forrige"],
            "consolidation": ["oppsummering", "sammendrag", "organisere", "struktur"],
            "exploration": ["hva hvis", "tenk på", "undersøk", "se på"],
            "protection": [
                "identitet", "navn", "hvem er", "critical",
                "hva heter", "mitt navn", "kall meg",  # Enhanced patterns
                "hvem er jeg", "hva er navnet", "min identitet"
            ]
        }
    
    def detect_intent(
        self,
        user_input: str,
        session_context: Dict[str, Any],
        system_state: Dict[str, Any]
    ) -> IntentSignal:
        """
        Detect intent fra user input + context.
        
        Args:
            user_input: User's message
            session_context: Current session info
            system_state: System metrics/state
        
        Returns:
            IntentSignal with detected mode + priorities
        """
        user_lower = user_input.lower()
        
        # Score each intent mode
        scores = {}
        for mode_name, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p in user_lower)
            scores[mode_name] = score
        
        # Get highest scoring mode
        if not any(scores.values()):
            detected_mode = IntentMode.RETRIEVAL  # Default
        else:
            mode_name = max(scores, key=scores.get)
            detected_mode = IntentMode(mode_name)
        
        # Extract active domains
        active_domains = self._extract_domains(user_input, session_context)
        
        # Extract priority keys
        priority_keys = self._extract_keys(user_input)
        
        # Generate ignore patterns
        ignore_patterns = self._generate_ignore_patterns(detected_mode)
        
        signal = IntentSignal(
            signal_id=f"intent_{datetime.now().timestamp()}",
            mode=detected_mode,
            active_domains=active_domains,
            priority_keys=priority_keys,
            ignore_patterns=ignore_patterns,
            timestamp=datetime.now(),
            strength=max(scores.values()) / 5.0 if scores else 0.5
        )
        
        self.current_intent = signal
        self.intent_history.append(signal)
        
        return signal
    
    def _extract_domains(self, text: str, context: Dict) -> List[str]:
        """Extract likely active domains from text"""
        domains = []
        
        # Domain keywords - EFC utvidet for bedre deteksjon
        domain_keywords = {
            "identity": ["navn", "heter", "jeg", "du", "hvem", "morten", "magnusson"],
            "efc_theory": [
                "efc", "energy-flow", "energiflyt", "grid", "higgs", "halo",
                "entropi", "kosmologi", "teori", "energy flow cosmology",
                "energi", "φ-felt", "phi", "gradient", "termodynamikk",
                "univers", "kosmisk", "formal", "spesifikasjon"
            ],
            "system_config": ["konfigurasjon", "innstilling", "parameter"],
            "health": ["helse", "status", "tilstand", "ytelse"]
        }
        
        text_lower = text.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                domains.append(domain)
        
        return domains or ["general"]
    
    def _extract_keys(self, text: str) -> List[str]:
        """Extract likely important keys from text"""
        # Simple keyword extraction
        important_words = [
            w for w in text.split()
            if len(w) > 4 and w[0].isupper()
        ]
        return important_words[:5]  # Top 5
    
    def _generate_ignore_patterns(self, mode: IntentMode) -> List[str]:
        """Generate ignore patterns based on intent mode"""
        if mode == IntentMode.PROTECTION:
            return ["test", "cli_test", "experiment"]
        elif mode == IntentMode.CONSOLIDATION:
            return ["noise", "irrelevant", "temporary"]
        else:
            return []
    
    def get_current_intent(self) -> Optional[IntentSignal]:
        """Get current intent signal"""
        return self.current_intent


class BalanceController:
    """
    BALANCE CONTROLLER
    
    Justerer bottom-up vs top-down vekting.
    
    Dette er hjertet av kognitiv isomorfi.
    """
    
    def __init__(self):
        self.current_balance: Optional[BalanceMetric] = None
        self.balance_history: List[BalanceMetric] = []
        
        # Default: balanced
        self.default_bottom_up = 0.5
        self.default_top_down = 0.5
    
    def calculate_balance(
        self,
        intent_signal: IntentSignal,
        system_metrics: Dict[str, float],
        stability_level: StabilityLevel
    ) -> BalanceMetric:
        """
        Calculate optimal bottom-up/top-down balance.
        
        Rules:
        - LEARNING mode → more bottom-up (data-driven)
        - PROTECTION mode → more top-down (intent-driven)
        - High stability → allow more bottom-up
        - Low stability → increase top-down control
        """
        # Start with defaults
        bottom_up = self.default_bottom_up
        top_down = self.default_top_down
        
        # Adjust based on intent mode
        if intent_signal.mode == IntentMode.LEARNING:
            bottom_up = 0.7
            top_down = 0.3
            state = BalanceState.BOTTOM_UP_DOMINANT
            reason = "Learning mode: data-driven"
        
        elif intent_signal.mode == IntentMode.PROTECTION:
            bottom_up = 0.3
            top_down = 0.7
            state = BalanceState.TOP_DOWN_DOMINANT
            reason = "Protection mode: intent-driven"
        
        elif intent_signal.mode == IntentMode.EXPLORATION:
            bottom_up = 0.6
            top_down = 0.4
            state = BalanceState.BOTTOM_UP_DOMINANT
            reason = "Exploration mode: pattern discovery"
        
        elif intent_signal.mode == IntentMode.CONSOLIDATION:
            bottom_up = 0.4
            top_down = 0.6
            state = BalanceState.TOP_DOWN_DOMINANT
            reason = "Consolidation mode: structure enforcement"
        
        else:  # RETRIEVAL
            bottom_up = 0.5
            top_down = 0.5
            state = BalanceState.BALANCED
            reason = "Retrieval mode: balanced"
        
        # Adjust based on stability
        if stability_level in [StabilityLevel.DEGRADING, StabilityLevel.CRITICAL]:
            # Increase top-down control for stability
            top_down += 0.2
            bottom_up -= 0.2
            reason += " + stability correction"
        
        # Normalize
        total = bottom_up + top_down
        bottom_up /= total
        top_down /= total
        
        metric = BalanceMetric(
            metric_id=f"balance_{datetime.now().timestamp()}",
            bottom_up_weight=bottom_up,
            top_down_weight=top_down,
            state=state,
            timestamp=datetime.now(),
            reason=reason
        )
        
        self.current_balance = metric
        self.balance_history.append(metric)
        
        return metric
    
    def get_current_balance(self) -> Optional[BalanceMetric]:
        """Get current balance metric"""
        return self.current_balance


class StabilityMonitor:
    """
    STABILITY MONITOR
    
    Oppdager drift, oscillering, degradering.
    
    Dette er sikkerhetslaget.
    """
    
    def __init__(self, balance_controller=None):
        self.reports: List[StabilityReport] = []
        self.baseline_metrics: Dict[str, float] = {}
        self.balance_controller = balance_controller  # For oscillation tracking
        
        # Thresholds
        self.drift_threshold = 0.3          # >30% avvik fra baseline
        self.oscillation_threshold = 5.0    # >5 changes/hour
        self.degradation_threshold = 0.1    # >10% performance drop
    
    def monitor(
        self,
        current_metrics: Dict[str, float],
        time_window_hours: int = 24
    ) -> StabilityReport:
        """
        Monitor system stability.
        
        Detects:
        - Drift from baseline
        - Oscillation (unstable switching)
        - Degradation (performance decline)
        """
        # Initialize baseline if empty
        if not self.baseline_metrics:
            self.baseline_metrics = current_metrics.copy()
        
        # Calculate drift
        drift_score = self._calculate_drift(current_metrics)
        
        # Calculate oscillation rate
        oscillation_rate = self._calculate_oscillation(time_window_hours)
        
        # Calculate degradation rate
        degradation_rate = self._calculate_degradation(current_metrics)
        
        # Determine stability level
        issues = []
        recommendations = []
        
        if drift_score > self.drift_threshold:
            level = StabilityLevel.DRIFT_DETECTED
            issues.append(f"Drift detected: {drift_score:.1%} from baseline")
            recommendations.append("Increase top-down control")
        
        if oscillation_rate > self.oscillation_threshold:
            level = StabilityLevel.OSCILLATING
            issues.append(f"Oscillation: {oscillation_rate:.1f} changes/hour")
            recommendations.append("Stabilize intent signal")
        
        if degradation_rate > self.degradation_threshold:
            level = StabilityLevel.DEGRADING
            issues.append(f"Performance degrading: {degradation_rate:.1%}/hour")
            recommendations.append("Run self-healing cycle")
        
        if len(issues) >= 2:
            level = StabilityLevel.CRITICAL
            recommendations.append("Emergency stabilization required")
        elif not issues:
            level = StabilityLevel.STABLE
        
        report = StabilityReport(
            report_id=f"stability_{datetime.now().timestamp()}",
            level=level,
            drift_score=drift_score,
            oscillation_rate=oscillation_rate,
            degradation_rate=degradation_rate,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        self.reports.append(report)
        
        return report
    
    def _calculate_drift(self, current: Dict[str, float]) -> float:
        """Calculate drift from baseline"""
        if not self.baseline_metrics:
            return 0.0
        
        drifts = []
        for key, baseline_value in self.baseline_metrics.items():
            if key in current and baseline_value != 0:
                drift = abs(current[key] - baseline_value) / baseline_value
                drifts.append(drift)
        
        return sum(drifts) / len(drifts) if drifts else 0.0
    
    def _calculate_oscillation(self, hours: int) -> float:
        """
        Calculate oscillation rate from balance history.
        
        Real implementation: Tracks balance state changes per hour.
        """
        if not self.balance_controller:
            return 0.0
        
        history = self.balance_controller.balance_history
        
        if len(history) < 2:
            return 0.0
        
        # Count state changes in time window
        now = datetime.now()
        window_start = now - timedelta(hours=hours)
        
        changes = 0
        prev_state = None
        
        for metric in history:
            if metric.timestamp < window_start:
                continue
            
            if prev_state and metric.state != prev_state:
                changes += 1
            
            prev_state = metric.state
        
        # Calculate rate per hour
        oscillation_rate = changes / hours if hours > 0 else 0.0
        
        return oscillation_rate
    
    def _calculate_degradation(self, current: Dict[str, float]) -> float:
        """Calculate performance degradation rate"""
        # Compare accuracy/quality metrics
        if "accuracy" in current and "accuracy" in self.baseline_metrics:
            baseline = self.baseline_metrics["accuracy"]
            if baseline != 0:
                return (baseline - current["accuracy"]) / baseline
        return 0.0


class MetaSupervisor:
    """
    META-SUPERVISOR LAYER
    
    Full top-down/bottom-up integration med:
    - Intent Engine (hva er viktig?)
    - Priority Gating (filtrer støy)
    - Balance Controller (bottom-up vs top-down)
    - Stability Monitor (drift/oscillation/degradation)
    - Identity Protection (kritisk sannhetsvern)
    - Value Layer (hva er VIKTIG?)
    
    Dette er kognitiv isomorfi - systemet tenker som deg.
    
    USAGE:
        supervisor = MetaSupervisor()
        
        # Process user input
        result = supervisor.process_turn(
            user_input="Hva heter jeg?",
            session_context={},
            system_metrics={}
        )
        
        # Get signals for other layers
        intent = result["intent_signal"]
        balance = result["balance_metric"]
        stability = result["stability_report"]
        value_decision = result["value_decision"]  # New in Phase 5
        
        # Optional: Use with Priority Gate and Identity Protection
        from tools.priority_gate import PriorityGate
        from tools.identity_protection import IdentityProtection
        from tools.value_layer import ValueLayer
        
        gate = PriorityGate()
        protection = IdentityProtection()
        value_layer = ValueLayer()
        
        # Filter memory chunks
        filtered_chunks = gate.filter_chunks(memory_chunks, intent)
        
        # Validate identity facts
        validation = protection.validate_fact(
            key="user.name",
            value="Morten",
            domain="identity",
            trust_score=0.95
        )
        
        # Get value-based priority
        decision = value_layer.make_decision(
            intent_signal={"mode": "protection"},
            key="user.name",
            domain="identity",
            content="Morten"
        )
    """
    
    def __init__(self, enable_value_layer: bool = True, enable_motivational_dynamics: bool = True):
        self.intent_engine = IntentEngine()
        self.balance_controller = BalanceController()
        self.stability_monitor = StabilityMonitor(
            balance_controller=self.balance_controller
        )
        
        # Phase 5: Value Layer
        self.enable_value_layer = enable_value_layer
        if enable_value_layer:
            try:
                from tools.value_layer import ValueLayer
                self.value_layer = ValueLayer()
            except ImportError:
                print("⚠️  Value Layer not available, continuing without it")
                self.value_layer = None
        else:
            self.value_layer = None
        
        # Phase 6: Motivational Dynamics
        self.enable_motivational_dynamics = enable_motivational_dynamics
        if enable_motivational_dynamics:
            try:
                from tools.motivational_dynamics import MotivationalDynamics
                self.motivational_dynamics = MotivationalDynamics()
            except ImportError:
                print("⚠️  Motivational Dynamics not available, continuing without it")
                self.motivational_dynamics = None
        else:
            self.motivational_dynamics = None
    
    def process_turn(
        self,
        user_input: str,
        session_context: Dict[str, Any],
        system_metrics: Dict[str, float],
        value_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation turn through meta-supervisor.
        
        Args:
            user_input: User's message
            session_context: Current session info
            system_metrics: System metrics
            value_context: Optional context for value layer (key, domain, content, etc.)
        
        Returns:
            {
                "intent_signal": IntentSignal,
                "balance_metric": BalanceMetric,
                "stability_report": StabilityReport,
                "value_decision": ValueDecision (if value layer enabled),
                "motivational_signal": MotivationalSignal (if phase 6 enabled),
                "recommendations": List[str]
            }
        """
        # 1. Detect intent
        intent = self.intent_engine.detect_intent(
            user_input,
            session_context,
            system_metrics
        )
        
        # 2. Monitor stability
        stability = self.stability_monitor.monitor(system_metrics)
        
        # 3. Calculate balance
        balance = self.balance_controller.calculate_balance(
            intent,
            system_metrics,
            stability.level
        )
        
        # 4. Value layer decision (Phase 5)
        value_decision = None
        if self.value_layer and value_context:
            # Add stability metrics to harm context
            if "harm_context" in value_context:
                value_context["harm_context"]["oscillation_rate"] = stability.oscillation_rate
                value_context["harm_context"]["drift_score"] = stability.drift_score
                value_context["harm_context"]["stability_level"] = stability.level.value
            
            value_decision = self.value_layer.make_decision(
                intent_signal=intent.to_dict(),
                **value_context
            )
        
        # 5. Motivational dynamics (Phase 6)
        motivational_signal = None
        if self.motivational_dynamics:
            # Build context for motivational layer
            motivation_context = {
                "intent_mode": intent.mode.value,
                "value_level": value_decision.value_level.value if value_decision else "medium",
                "harm_signals": [h.to_dict() for h in value_decision.harm_signals] if value_decision and value_decision.harm_detected else [],
                "oscillation_rate": stability.oscillation_rate,
                "drift_score": stability.drift_score,
                "stability_level": stability.level.value
            }
            
            motivational_signal = self.motivational_dynamics.generate_signal(motivation_context)
            
            # Self-regulate
            if len(self.motivational_dynamics.meta_stability_loop.history) > 5:
                self.motivational_dynamics.self_regulate(motivation_context)
        
        # 6. Generate recommendations
        recommendations = self._generate_recommendations(
            intent,
            balance,
            stability,
            value_decision,
            motivational_signal
        )
        
        result = {
            "intent_signal": intent,
            "balance_metric": balance,
            "stability_report": stability,
            "recommendations": recommendations
        }
        
        if value_decision:
            result["value_decision"] = value_decision
        
        if motivational_signal:
            result["motivational_signal"] = motivational_signal
        
        return result
    
    def _generate_recommendations(
        self,
        intent: IntentSignal,
        balance: BalanceMetric,
        stability: StabilityReport,
        value_decision: Optional[Any] = None,
        motivational_signal: Optional[Any] = None
    ) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        # From stability report
        recs.extend(stability.recommendations)
        
        # Intent-specific
        if intent.mode == IntentMode.PROTECTION:
            recs.append("Prioritize canonical memory over LLM draft")
        
        # Balance-specific
        if balance.state == BalanceState.BOTTOM_UP_DOMINANT:
            recs.append("Allow more pattern discovery from data")
        elif balance.state == BalanceState.TOP_DOWN_DOMINANT:
            recs.append("Enforce intent-based filtering")
        
        # Value-specific (Phase 5)
        if value_decision:
            if value_decision.harm_detected:
                recs.append(f"⚠️  HARM DETECTED: {len(value_decision.harm_signals)} signal(s)")
                for harm in value_decision.harm_signals:
                    recs.append(f"   → {harm.recommended_action}")
            
            if value_decision.value_level.value == "critical":
                recs.append("CRITICAL value: Maximum protection enforcement")
            
            if value_decision.final_priority >= 0.9:
                recs.append(f"High priority decision: {value_decision.final_priority:.2f}")
        
        # Motivational-specific (Phase 6)
        if motivational_signal:
            if motivational_signal.motivation_strength > 0.8:
                recs.append(f"🎯 High motivation: {motivational_signal.motivation_strength:.2f}")
            
            # Active goals
            if motivational_signal.active_goals:
                top_goal = motivational_signal.active_goals[0]
                recs.append(f"📍 Top goal: {top_goal.goal_type.value}")
            
            # Directional bias
            for domain, bias in motivational_signal.directional_bias.items():
                if bias > 0.75:
                    recs.append(f"⚡ Strong {domain} bias: {bias:.2f}")
        
        return recs
    
    def get_stats(self) -> Dict:
        """Get meta-supervisor statistics"""
        stats = {
            "total_intents": len(self.intent_engine.intent_history),
            "total_balance_metrics": len(self.balance_controller.balance_history),
            "total_stability_reports": len(self.stability_monitor.reports),
            "current_intent": self.intent_engine.current_intent.mode.value if self.intent_engine.current_intent else None,
            "current_balance": self.balance_controller.current_balance.state.value if self.balance_controller.current_balance else None,
            "current_stability": self.stability_monitor.reports[-1].level.value if self.stability_monitor.reports else "unknown"
        }
        
        # Add value layer stats if enabled
        if self.value_layer:
            stats["value_layer"] = self.value_layer.get_stats()
        
        # Add motivational dynamics stats if enabled
        if self.motivational_dynamics:
            stats["motivational_dynamics"] = self.motivational_dynamics.get_stats()
        
        return stats


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Meta-Supervisor Layer")
    print("=" * 60)
    
    supervisor = MetaSupervisor()
    
    # Test 1: Protection intent
    print("\n1️⃣ Test: Protection intent (identity question)")
    result = supervisor.process_turn(
        user_input="Hva heter jeg?",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"Intent mode: {result['intent_signal'].mode.value}")
    print(f"Active domains: {result['intent_signal'].active_domains}")
    print(f"Balance: {result['balance_metric'].state.value}")
    print(f"  Bottom-up: {result['balance_metric'].bottom_up_weight:.2f}")
    print(f"  Top-down: {result['balance_metric'].top_down_weight:.2f}")
    print(f"Stability: {result['stability_report'].level.value}")
    print(f"Recommendations: {result['recommendations']}")
    
    # Test 2: Learning intent
    print("\n2️⃣ Test: Learning intent (new information)")
    result = supervisor.process_turn(
        user_input="Forklar hva energiflyt er",
        session_context={},
        system_metrics={"accuracy": 0.85, "override_rate": 0.2}
    )
    
    print(f"Intent mode: {result['intent_signal'].mode.value}")
    print(f"Balance: {result['balance_metric'].state.value}")
    print(f"  Bottom-up: {result['balance_metric'].bottom_up_weight:.2f}")
    print(f"  Top-down: {result['balance_metric'].top_down_weight:.2f}")
    
    # Test 3: Stats
    print("\n3️⃣ System stats")
    stats = supervisor.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Meta-Supervisor Layer test complete")
