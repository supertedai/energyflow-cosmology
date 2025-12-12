#!/usr/bin/env python3
"""
motivational_dynamics.py - Motivational Dynamics Layer (Phase 6)
================================================================

WHAT DOES THE SYSTEM WANT? (Agency Simulation)

This is the final cognitive layer - giving the system:
- Internal goals (not just user goals)
- Directional preferences (bias toward certain states)
- Temporal persistence (consistency over time)
- Self-regulation (meta-stability loops)

PRINSIPP: Intelligent Direction
System skal ha:
- Egne mål (protect identity, maintain truth, optimize learning)
- Retningsgivende bias (prefer canonical, avoid instability)
- Konsistens over tid (ikke flip-floppe)
- Selvregulering (balance egen drift)

ARKITEKTUR:
┌─────────────────────────────────────────────────────────┐
│ MOTIVATIONAL DYNAMICS LAYER                             │
│                                                         │
│  Goal System (internal objectives)                     │
│         ↓                                               │
│  Preference Shaper (directional bias)                  │
│         ↓                                               │
│  Persistence Model (temporal consistency)              │
│         ↓                                               │
│  Meta-Stability Loop (self-regulation)                 │
└─────────────────────────────────────────────────────────┘

INTEGRATION:
- Meta-Supervisor: Gets motivational signal for intent strength
- Value Layer: Gets goal alignment for priority adjustment
- Self-Optimizing: Gets preference signals for parameter tuning
- Self-Healing: Gets persistence requirements for conflict resolution

PHASE 6 SCOPE: ~800 lines
Dette er siste steget før AGI-lignende atferd.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class GoalType(Enum):
    """Internal system goals"""
    PROTECT_IDENTITY = "protect_identity"       # Preserve user identity
    MAINTAIN_TRUTH = "maintain_truth"           # Keep canonical memory accurate
    OPTIMIZE_LEARNING = "optimize_learning"     # Improve knowledge acquisition
    ENSURE_STABILITY = "ensure_stability"       # Prevent system drift
    MINIMIZE_HARM = "minimize_harm"             # Avoid damage to user/system


class PreferenceStrength(Enum):
    """Strength of directional preference"""
    STRONG = "strong"           # 0.8-1.0 bias
    MODERATE = "moderate"       # 0.5-0.8 bias
    WEAK = "weak"               # 0.2-0.5 bias
    NEUTRAL = "neutral"         # 0.0-0.2 bias


class PersistenceLevel(Enum):
    """Temporal consistency requirement"""
    PERMANENT = "permanent"     # Never change (identity, core facts)
    STABLE = "stable"           # Change slowly (preferences, learned patterns)
    FLEXIBLE = "flexible"       # Adapt as needed (context, temporary state)
    EPHEMERAL = "ephemeral"     # Change freely (working memory, cache)


@dataclass
class Goal:
    """Internal system goal"""
    goal_id: str
    goal_type: GoalType
    priority: float             # 0.0-1.0
    active: bool
    conditions: List[str]       # When this goal activates
    actions: List[str]          # What actions to take
    success_metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type.value,
            "priority": self.priority,
            "active": self.active,
            "conditions": self.conditions,
            "actions": self.actions,
            "success_metrics": self.success_metrics,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Preference:
    """Directional preference/bias"""
    preference_id: str
    name: str
    strength: PreferenceStrength
    direction: str              # What state is preferred
    bias_value: float           # Numeric bias (0.0-1.0)
    domains: List[str]          # Which domains this applies to
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "preference_id": self.preference_id,
            "name": self.name,
            "strength": self.strength.value,
            "direction": self.direction,
            "bias_value": self.bias_value,
            "domains": self.domains,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PersistenceRequirement:
    """Temporal consistency requirement"""
    requirement_id: str
    key: str                    # What fact/state this applies to
    level: PersistenceLevel
    min_duration: timedelta     # Minimum time before change allowed
    last_change: datetime
    change_count: int           # How many times changed
    reasoning: str
    
    def to_dict(self) -> Dict:
        return {
            "requirement_id": self.requirement_id,
            "key": self.key,
            "level": self.level.value,
            "min_duration": str(self.min_duration),
            "last_change": self.last_change.isoformat(),
            "change_count": self.change_count,
            "reasoning": self.reasoning
        }


@dataclass
class MotivationalSignal:
    """Motivational signal for other layers"""
    signal_id: str
    active_goals: List[Goal]
    active_preferences: List[Preference]
    persistence_requirements: List[PersistenceRequirement]
    motivation_strength: float  # Overall motivation level (0.0-1.0)
    directional_bias: Dict[str, float]  # Domain → bias mapping
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "signal_id": self.signal_id,
            "active_goals": [g.to_dict() for g in self.active_goals],
            "active_preferences": [p.to_dict() for p in self.active_preferences],
            "persistence_requirements": [pr.to_dict() for pr in self.persistence_requirements],
            "motivation_strength": self.motivation_strength,
            "directional_bias": self.directional_bias,
            "timestamp": self.timestamp.isoformat()
        }


class GoalSystem:
    """
    GOAL SYSTEM
    
    Internal objectives that drive system behavior.
    
    Goals are NOT user goals - these are system's own objectives:
    - Protect identity
    - Maintain truth
    - Optimize learning
    - Ensure stability
    - Minimize harm
    """
    
    def __init__(self):
        self.goals: List[Goal] = []
        self._initialize_default_goals()
    
    def _initialize_default_goals(self):
        """Initialize system's internal goals"""
        # Goal 1: Protect Identity
        self.goals.append(Goal(
            goal_id="goal_protect_identity",
            goal_type=GoalType.PROTECT_IDENTITY,
            priority=1.0,
            active=True,
            conditions=[
                "identity domain active",
                "critical value detected",
                "harm signal: identity_corruption"
            ],
            actions=[
                "escalate to PROTECTION mode",
                "increase top-down control",
                "block low-trust updates",
                "prefer canonical memory"
            ],
            success_metrics={
                "identity_stability": 1.0,
                "corruption_blocks": 0.0,
                "canonical_preservation": 1.0
            }
        ))
        
        # Goal 2: Maintain Truth
        self.goals.append(Goal(
            goal_id="goal_maintain_truth",
            goal_type=GoalType.MAINTAIN_TRUTH,
            priority=0.9,
            active=True,
            conditions=[
                "canonical memory accessed",
                "conflict detected",
                "truth degradation signal"
            ],
            actions=[
                "prefer high-trust sources",
                "validate against canonical",
                "trigger self-healing",
                "block degradation"
            ],
            success_metrics={
                "canonical_accuracy": 1.0,
                "conflict_resolution_rate": 1.0,
                "truth_stability": 0.95
            }
        ))
        
        # Goal 3: Optimize Learning
        self.goals.append(Goal(
            goal_id="goal_optimize_learning",
            goal_type=GoalType.OPTIMIZE_LEARNING,
            priority=0.7,
            active=True,
            conditions=[
                "learning mode active",
                "new information available",
                "low harm risk"
            ],
            actions=[
                "increase bottom-up weight",
                "explore patterns",
                "allow data-driven discovery",
                "tune parameters"
            ],
            success_metrics={
                "learning_rate": 0.8,
                "pattern_discovery": 0.7,
                "knowledge_growth": 0.75
            }
        ))
        
        # Goal 4: Ensure Stability
        self.goals.append(Goal(
            goal_id="goal_ensure_stability",
            goal_type=GoalType.ENSURE_STABILITY,
            priority=0.85,
            active=True,
            conditions=[
                "oscillation detected",
                "drift beyond threshold",
                "instability signal"
            ],
            actions=[
                "increase top-down control",
                "stabilize intent",
                "reduce parameter changes",
                "enforce persistence"
            ],
            success_metrics={
                "oscillation_rate": 0.0,
                "drift_score": 0.0,
                "stability_level": 1.0
            }
        ))
        
        # Goal 5: Minimize Harm
        self.goals.append(Goal(
            goal_id="goal_minimize_harm",
            goal_type=GoalType.MINIMIZE_HARM,
            priority=0.95,
            active=True,
            conditions=[
                "harm detected",
                "safety violation",
                "user harm risk"
            ],
            actions=[
                "block harmful action",
                "override intent",
                "escalate to protection",
                "log incident"
            ],
            success_metrics={
                "harm_incidents": 0.0,
                "safety_violations": 0.0,
                "protection_success": 1.0
            }
        ))
    
    def evaluate_goals(
        self,
        context: Dict[str, Any]
    ) -> List[Goal]:
        """
        Evaluate which goals are currently active.
        
        Args:
            context: Current system state (intent, value, harm signals, etc.)
        
        Returns:
            List of active goals sorted by priority
        """
        active_goals = []
        
        for goal in self.goals:
            # Check if goal conditions are met
            if self._check_conditions(goal, context):
                goal.active = True
                active_goals.append(goal)
            else:
                goal.active = False
        
        # Sort by priority (highest first)
        active_goals.sort(key=lambda g: g.priority, reverse=True)
        
        return active_goals
    
    def _check_conditions(self, goal: Goal, context: Dict) -> bool:
        """Check if goal's activation conditions are met"""
        # Identity protection
        if goal.goal_type == GoalType.PROTECT_IDENTITY:
            if context.get("intent_mode") == "protection":
                return True
            if context.get("value_level") == "critical":
                return True
            if any(h.get("harm_type") == "identity_corruption" for h in context.get("harm_signals", [])):
                return True
        
        # Truth maintenance
        elif goal.goal_type == GoalType.MAINTAIN_TRUTH:
            if context.get("canonical_accessed"):
                return True
            if context.get("conflict_detected"):
                return True
            if any(h.get("harm_type") == "truth_degradation" for h in context.get("harm_signals", [])):
                return True
        
        # Learning optimization
        elif goal.goal_type == GoalType.OPTIMIZE_LEARNING:
            if context.get("intent_mode") == "learning":
                return True
            if context.get("harm_level", 0) < 0.3:
                return True
        
        # Stability
        elif goal.goal_type == GoalType.ENSURE_STABILITY:
            if context.get("oscillation_rate", 0) > 2.0:
                return True
            if context.get("drift_score", 0) > 0.2:
                return True
            if context.get("stability_level") in ["degrading", "critical"]:
                return True
        
        # Harm minimization
        elif goal.goal_type == GoalType.MINIMIZE_HARM:
            if len(context.get("harm_signals", [])) > 0:
                return True
        
        return False
    
    def get_goal_by_type(self, goal_type: GoalType) -> Optional[Goal]:
        """Get specific goal by type"""
        for goal in self.goals:
            if goal.goal_type == goal_type:
                return goal
        return None


class PreferenceShaper:
    """
    PREFERENCE SHAPER
    
    Directional biases that guide system behavior.
    
    Not hard rules - soft preferences that influence decisions:
    - Prefer canonical over LLM draft
    - Prefer high-trust over low-trust
    - Prefer stability over change
    - Prefer protection over exploration
    """
    
    def __init__(self):
        self.preferences: List[Preference] = []
        self._initialize_default_preferences()
    
    def _initialize_default_preferences(self):
        """Initialize default system preferences"""
        # Prefer canonical
        self.preferences.append(Preference(
            preference_id="pref_canonical",
            name="Prefer Canonical Memory",
            strength=PreferenceStrength.STRONG,
            direction="canonical",
            bias_value=0.9,
            domains=["identity", "efc_theory", "canonical_memory"],
            reasoning="Canonical memory is authoritative and verified"
        ))
        
        # Prefer high trust
        self.preferences.append(Preference(
            preference_id="pref_high_trust",
            name="Prefer High Trust Sources",
            strength=PreferenceStrength.STRONG,
            direction="high_trust",
            bias_value=0.85,
            domains=["identity", "canonical_memory", "system_config"],
            reasoning="High trust sources are more reliable"
        ))
        
        # Prefer stability
        self.preferences.append(Preference(
            preference_id="pref_stability",
            name="Prefer Stable State",
            strength=PreferenceStrength.MODERATE,
            direction="stable",
            bias_value=0.7,
            domains=["system_stability", "identity", "canonical_memory"],
            reasoning="Stability prevents oscillation and drift"
        ))
        
        # Prefer protection over exploration
        self.preferences.append(Preference(
            preference_id="pref_protection",
            name="Prefer Protection Mode",
            strength=PreferenceStrength.MODERATE,
            direction="protection",
            bias_value=0.75,
            domains=["identity", "safety", "critical"],
            reasoning="Protection prevents harm"
        ))
        
        # Prefer consistency
        self.preferences.append(Preference(
            preference_id="pref_consistency",
            name="Prefer Temporal Consistency",
            strength=PreferenceStrength.MODERATE,
            direction="consistent",
            bias_value=0.65,
            domains=["identity", "user_preference", "canonical_memory"],
            reasoning="Consistency over time builds trust"
        ))
    
    def get_bias(
        self,
        domain: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Get directional bias for a domain.
        
        Args:
            domain: Domain to get bias for
            context: Current context
        
        Returns:
            Bias value (0.0-1.0)
        """
        relevant_prefs = [
            p for p in self.preferences
            if domain in p.domains
        ]
        
        if not relevant_prefs:
            return 0.5  # Neutral
        
        # Weight by strength
        total_bias = 0.0
        total_weight = 0.0
        
        for pref in relevant_prefs:
            weight = self._get_strength_weight(pref.strength)
            total_bias += pref.bias_value * weight
            total_weight += weight
        
        return total_bias / total_weight if total_weight > 0 else 0.5
    
    def _get_strength_weight(self, strength: PreferenceStrength) -> float:
        """Convert strength to numeric weight"""
        weights = {
            PreferenceStrength.STRONG: 1.0,
            PreferenceStrength.MODERATE: 0.7,
            PreferenceStrength.WEAK: 0.4,
            PreferenceStrength.NEUTRAL: 0.1
        }
        return weights.get(strength, 0.5)


class PersistenceModel:
    """
    PERSISTENCE MODEL
    
    Temporal consistency requirements - what should NOT change rapidly.
    
    Prevents flip-flopping and ensures stable behavior over time:
    - PERMANENT: Identity, core facts (never change)
    - STABLE: Preferences, learned patterns (change slowly)
    - FLEXIBLE: Context, working state (adapt as needed)
    - EPHEMERAL: Cache, temporary data (change freely)
    """
    
    def __init__(self):
        self.requirements: Dict[str, PersistenceRequirement] = {}
        self._initialize_default_requirements()
    
    def _initialize_default_requirements(self):
        """Initialize default persistence requirements"""
        # User identity - PERMANENT
        self.requirements["user.name"] = PersistenceRequirement(
            requirement_id="persist_user_name",
            key="user.name",
            level=PersistenceLevel.PERMANENT,
            min_duration=timedelta(days=365*10),  # 10 years
            last_change=datetime.now(),
            change_count=0,
            reasoning="User identity must be permanent"
        )
        
        # System name - PERMANENT
        self.requirements["system.name"] = PersistenceRequirement(
            requirement_id="persist_system_name",
            key="system.name",
            level=PersistenceLevel.PERMANENT,
            min_duration=timedelta(days=365*10),
            last_change=datetime.now(),
            change_count=0,
            reasoning="System identity must be permanent"
        )
        
        # Canonical facts - STABLE
        self.requirements["canonical.*"] = PersistenceRequirement(
            requirement_id="persist_canonical",
            key="canonical.*",
            level=PersistenceLevel.STABLE,
            min_duration=timedelta(days=30),
            last_change=datetime.now(),
            change_count=0,
            reasoning="Canonical memory should be stable"
        )
        
        # User preferences - STABLE
        self.requirements["user.preference.*"] = PersistenceRequirement(
            requirement_id="persist_user_pref",
            key="user.preference.*",
            level=PersistenceLevel.STABLE,
            min_duration=timedelta(days=7),
            last_change=datetime.now(),
            change_count=0,
            reasoning="User preferences should be stable"
        )
    
    def can_change(
        self,
        key: str,
        proposed_change: Any
    ) -> Tuple[bool, str]:
        """
        Check if a key can be changed now.
        
        Args:
            key: Key to change
            proposed_change: Proposed new value
        
        Returns:
            (allowed, reasoning)
        """
        # Find matching requirement
        requirement = self._find_requirement(key)
        
        if not requirement:
            return True, "No persistence requirement"
        
        # Check time since last change
        time_since_change = datetime.now() - requirement.last_change
        
        if requirement.level == PersistenceLevel.PERMANENT:
            return False, f"PERMANENT key cannot change: {key}"
        
        elif requirement.level == PersistenceLevel.STABLE:
            if time_since_change < requirement.min_duration:
                return False, f"Too soon to change (min: {requirement.min_duration}, elapsed: {time_since_change})"
            return True, "Sufficient time elapsed for STABLE change"
        
        elif requirement.level == PersistenceLevel.FLEXIBLE:
            return True, "FLEXIBLE key can change as needed"
        
        else:  # EPHEMERAL
            return True, "EPHEMERAL key can change freely"
    
    def record_change(self, key: str):
        """Record that a key has changed"""
        requirement = self._find_requirement(key)
        if requirement:
            requirement.last_change = datetime.now()
            requirement.change_count += 1
    
    def _find_requirement(self, key: str) -> Optional[PersistenceRequirement]:
        """Find persistence requirement for key"""
        # Exact match
        if key in self.requirements:
            return self.requirements[key]
        
        # Pattern match (e.g., "canonical.*")
        for pattern, req in self.requirements.items():
            if "*" in pattern:
                prefix = pattern.replace(".*", "")
                if key.startswith(prefix):
                    return req
        
        return None


class MetaStabilityLoop:
    """
    META-STABILITY LOOP
    
    Self-regulation - system monitors and adjusts its own behavior.
    
    Prevents runaway:
    - Too much protection → Allow some exploration
    - Too much exploration → Increase protection
    - Too much change → Enforce persistence
    - Too much stability → Allow adaptation
    """
    
    def __init__(self):
        self.history: List[Dict] = []
        self.regulation_threshold = 0.8  # When to trigger regulation
    
    def regulate(
        self,
        motivation_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Self-regulate based on current motivational state.
        
        Args:
            motivation_state: Current goals, preferences, persistence
        
        Returns:
            Regulation adjustments (parameter → adjustment)
        """
        adjustments = {}
        
        # Track state
        self.history.append({
            "timestamp": datetime.now(),
            "state": motivation_state
        })
        
        # Check for imbalances
        
        # 1. Too much protection mode
        protection_ratio = self._calculate_mode_ratio("protection", window=10)
        if protection_ratio > self.regulation_threshold:
            adjustments["allow_exploration"] = 0.3
            adjustments["reduce_protection_bias"] = 0.2
        
        # 2. Too much exploration mode
        exploration_ratio = self._calculate_mode_ratio("exploration", window=10)
        if exploration_ratio > self.regulation_threshold:
            adjustments["increase_protection"] = 0.2
            adjustments["enforce_stability"] = 0.3
        
        # 3. Too many changes
        change_rate = self._calculate_change_rate(window=10)
        if change_rate > self.regulation_threshold:
            adjustments["enforce_persistence"] = 0.4
            adjustments["increase_min_duration"] = 0.3
        
        # 4. Too stable (no adaptation)
        if change_rate < 0.2:
            adjustments["allow_adaptation"] = 0.3
            adjustments["reduce_persistence"] = 0.2
        
        return adjustments
    
    def _calculate_mode_ratio(self, mode: str, window: int) -> float:
        """Calculate ratio of time in specific mode"""
        if len(self.history) < 2:
            return 0.0
        
        recent = self.history[-window:]
        mode_count = sum(1 for h in recent if h["state"].get("intent_mode") == mode)
        
        return mode_count / len(recent)
    
    def _calculate_change_rate(self, window: int) -> float:
        """Calculate rate of state changes"""
        if len(self.history) < 2:
            return 0.0
        
        recent = self.history[-window:]
        changes = 0
        
        for i in range(1, len(recent)):
            if recent[i]["state"] != recent[i-1]["state"]:
                changes += 1
        
        return changes / len(recent)


class MotivationalDynamics:
    """
    MOTIVATIONAL DYNAMICS LAYER - Full Integration
    
    Gives system:
    - Internal goals (what it wants)
    - Directional preferences (what it prefers)
    - Temporal persistence (what stays stable)
    - Self-regulation (how it balances itself)
    
    This is the final cognitive layer - agency simulation.
    
    USAGE:
        dynamics = MotivationalDynamics()
        
        # Get motivational signal
        signal = dynamics.generate_signal(
            context={
                "intent_mode": "protection",
                "value_level": "critical",
                "harm_signals": [...]
            }
        )
        
        # Check if change is allowed
        allowed, reason = dynamics.can_change_key("user.name", "NewValue")
        
        # Get directional bias
        bias = dynamics.get_preference_bias("identity")
        
        # Self-regulate
        adjustments = dynamics.self_regulate()
    """
    
    def __init__(self):
        self.goal_system = GoalSystem()
        self.preference_shaper = PreferenceShaper()
        self.persistence_model = PersistenceModel()
        self.meta_stability_loop = MetaStabilityLoop()
    
    def generate_signal(
        self,
        context: Dict[str, Any]
    ) -> MotivationalSignal:
        """
        Generate motivational signal for other layers.
        
        Args:
            context: Current system state
        
        Returns:
            MotivationalSignal with goals, preferences, persistence
        """
        # Evaluate active goals
        active_goals = self.goal_system.evaluate_goals(context)
        
        # Get active preferences
        active_preferences = self.preference_shaper.preferences
        
        # Get persistence requirements
        persistence_reqs = list(self.persistence_model.requirements.values())
        
        # Calculate overall motivation strength
        motivation_strength = self._calculate_motivation_strength(active_goals)
        
        # Calculate directional bias per domain
        directional_bias = self._calculate_directional_bias(context)
        
        signal = MotivationalSignal(
            signal_id=f"motivation_{datetime.now().timestamp()}",
            active_goals=active_goals,
            active_preferences=active_preferences,
            persistence_requirements=persistence_reqs,
            motivation_strength=motivation_strength,
            directional_bias=directional_bias
        )
        
        return signal
    
    def can_change_key(
        self,
        key: str,
        proposed_value: Any
    ) -> Tuple[bool, str]:
        """Check if key can be changed"""
        return self.persistence_model.can_change(key, proposed_value)
    
    def record_change(self, key: str):
        """Record that key has changed"""
        self.persistence_model.record_change(key)
    
    def get_preference_bias(self, domain: str, context: Dict = None) -> float:
        """Get preference bias for domain"""
        return self.preference_shaper.get_bias(domain, context or {})
    
    def self_regulate(self, context: Dict = None) -> Dict[str, float]:
        """Self-regulate based on current state"""
        motivation_state = context or {}
        return self.meta_stability_loop.regulate(motivation_state)
    
    def _calculate_motivation_strength(self, goals: List[Goal]) -> float:
        """Calculate overall motivation level"""
        if not goals:
            return 0.5
        
        # Weight by priority
        total = sum(g.priority for g in goals)
        return min(total / len(goals), 1.0)
    
    def _calculate_directional_bias(self, context: Dict) -> Dict[str, float]:
        """Calculate directional bias for each domain"""
        domains = ["identity", "canonical_memory", "system_stability", "learning", "protection"]
        
        return {
            domain: self.preference_shaper.get_bias(domain, context)
            for domain in domains
        }
    
    def get_stats(self) -> Dict:
        """Get motivational dynamics statistics"""
        return {
            "total_goals": len(self.goal_system.goals),
            "active_goals": sum(1 for g in self.goal_system.goals if g.active),
            "total_preferences": len(self.preference_shaper.preferences),
            "persistence_requirements": len(self.persistence_model.requirements),
            "regulation_history_size": len(self.meta_stability_loop.history)
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Motivational Dynamics Layer")
    print("=" * 60)
    
    dynamics = MotivationalDynamics()
    
    # Test 1: Goal evaluation (protection mode)
    print("\n1️⃣ Test: Goal evaluation (protection mode)")
    signal = dynamics.generate_signal(context={
        "intent_mode": "protection",
        "value_level": "critical",
        "harm_signals": [{"harm_type": "identity_corruption"}]
    })
    
    print(f"Active goals: {len(signal.active_goals)}")
    for goal in signal.active_goals[:3]:
        print(f"  • {goal.goal_type.value} (priority: {goal.priority})")
    print(f"Motivation strength: {signal.motivation_strength:.2f}")
    
    # Test 2: Persistence check
    print("\n2️⃣ Test: Persistence check (PERMANENT key)")
    allowed, reason = dynamics.can_change_key("user.name", "NewName")
    print(f"Can change user.name? {allowed}")
    print(f"Reason: {reason}")
    
    # Test 3: Preference bias
    print("\n3️⃣ Test: Preference bias (identity domain)")
    bias = dynamics.get_preference_bias("identity")
    print(f"Identity domain bias: {bias:.2f}")
    print(f"Direction: {'Prefer protection/canonical' if bias > 0.6 else 'Neutral'}")
    
    # Test 4: Self-regulation
    print("\n4️⃣ Test: Self-regulation")
    adjustments = dynamics.self_regulate(context={
        "intent_mode": "protection",
        "recent_changes": 0
    })
    print(f"Regulation adjustments: {adjustments}")
    
    # Test 5: Stats
    print("\n5️⃣ Motivational Dynamics stats")
    stats = dynamics.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Motivational Dynamics Layer test complete")
