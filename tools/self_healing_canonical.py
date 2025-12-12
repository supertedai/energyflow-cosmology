#!/usr/bin/env python3
"""
self_healing_canonical.py - Self-Healing Canonical Memory Layer
================================================================

Generalisert selvhelbredende sannhetsmotor for ALLE domener.

PRINSIPP:
1. Observasjoner != Sannhet (før aggregering)
2. Konflikter løses via authority + support + temporal vekting
3. Testdata isoleres automatisk via source tagging
4. Alle domener behandles likt (identity, efc_theory, system_config, health, etc.)

ARKITEKTUR:
- Observation-based truth (ikke direkte assert)
- Authority-weighted aggregation
- Conflict detection + resolution
- Temporal decay for gamle fakta
- Cross-domain consistency

Dette er IKKE utopi - dette er solid systemdesign basert på:
- Conflict-free replicated data types (CRDT)
- Belief revision logic
- Multi-source truth reconciliation
- Authority-weighted aggregation

INTEGRASJON:
- CMC: Lagrer observations + canonical facts
- AME: Genererer observations fra memory enhancement
- MCA: Kjører periodic conflict detection
- Router: Bruker kun ACTIVE/STABLE facts
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class AuthorityLevel(Enum):
    """Authority levels for facts and observations"""
    TEST = 0           # CLI tests, experiments
    SHORT_TERM = 1     # Single user mention
    MEDIUM_TERM = 2    # Multiple consistent mentions
    STABLE = 3         # Verified across sessions
    LONG_TERM = 4      # Deeply established truth


class FactStatus(Enum):
    """Status of a fact in the canonical layer"""
    CANDIDATE = "candidate"       # New observation, not yet validated
    SUSPECT = "suspect"           # Conflicting with other observations
    ACTIVE = "active"             # Currently accepted truth
    STABLE = "stable"             # Well-established, high confidence
    DEPRECATED = "deprecated"     # Superseded by newer information
    TEST_ONLY = "test_only"       # Marked as test data, not real


class SourceType(Enum):
    """Source of observation"""
    CLI_TEST = "cli_test"         # CLI testing/debugging
    CHAT_USER = "chat_user"       # User statement in chat
    INGEST_DOC = "ingest_doc"     # Ingested authoritative document
    SYSTEM_DEFAULT = "system_default"  # System configuration
    MEMORY_ENHANCEMENT = "memory_enhancement"  # AME observation


@dataclass
class Observation:
    """
    Single observation of a fact.
    
    Observations are NOT truth - they are data points that get aggregated
    into canonical facts through the self-healing process.
    """
    observation_id: str
    domain: str                    # identity, efc_theory, system_config, etc.
    key: str                       # name, database, entropy_def, etc.
    value: Any
    source: SourceType
    authority: AuthorityLevel
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "observation_id": self.observation_id,
            "domain": self.domain,
            "key": self.key,
            "value": self.value,
            "source": self.source.value,
            "authority": self.authority.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class CanonicalFact:
    """
    Canonical fact - aggregated truth from multiple observations.
    
    This is what the system accepts as "true" at this moment.
    Can be promoted/demoted based on new observations.
    """
    fact_id: str
    domain: str
    key: str
    value: Any
    status: FactStatus
    authority: AuthorityLevel
    support_count: int              # Number of supporting observations
    conflict_group_id: Optional[str] = None
    supporting_observations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "fact_id": self.fact_id,
            "domain": self.domain,
            "key": self.key,
            "value": self.value,
            "status": self.status.value,
            "authority": self.authority.value,
            "support_count": self.support_count,
            "conflict_group_id": self.conflict_group_id,
            "supporting_observations": self.supporting_observations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_observed": self.last_observed.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Conflict:
    """Detected conflict between multiple facts/observations"""
    conflict_id: str
    domain: str
    key: str
    competing_facts: List[str]      # fact_ids
    competing_values: List[Any]
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "conflict_id": self.conflict_id,
            "domain": self.domain,
            "key": self.key,
            "competing_facts": self.competing_facts,
            "competing_values": self.competing_values,
            "detected_at": self.detected_at.isoformat(),
            "resolved": self.resolved,
            "resolution": self.resolution
        }


class SelfHealingCanonical:
    """
    Self-Healing Canonical Memory Layer.
    
    Manages observations → facts → truth via intelligent aggregation.
    
    WORKFLOW:
    1. register_observation() - New data comes in
    2. detect_conflicts() - Find inconsistencies
    3. resolve_conflict() - Apply authority-weighted resolution
    4. promote_fact() / demote_fact() - Update truth status
    5. get_canonical_truth() - Retrieve current accepted truth
    
    RULES:
    - TEST authority never wins over real data
    - Multiple consistent observations → promotion
    - Conflicting observations → conflict resolution
    - Temporal decay: old unused facts degrade
    - Cross-domain consistency checking
    """
    
    def __init__(self):
        self.observations: Dict[str, Observation] = {}
        self.facts: Dict[str, CanonicalFact] = {}
        self.conflicts: Dict[str, Conflict] = {}
        
        # Indexes for fast lookup
        self.domain_key_index: Dict[Tuple[str, str], List[str]] = {}  # (domain, key) → fact_ids
        self.observation_index: Dict[str, List[str]] = {}  # fact_id → observation_ids
        
        # Configuration
        self.promotion_threshold = 3      # Observations needed for promotion
        self.conflict_threshold = 2       # Different values to trigger conflict
        self.temporal_decay_days = 90     # Days before unused facts degrade
        
    def register_observation(
        self,
        domain: str,
        key: str,
        value: Any,
        source: SourceType,
        authority: AuthorityLevel = AuthorityLevel.SHORT_TERM,
        metadata: Optional[Dict] = None
    ) -> Observation:
        """
        Register a new observation.
        
        This does NOT immediately create/update canonical truth.
        It adds data to the pool that gets aggregated.
        
        Args:
            domain: Domain (identity, efc_theory, system_config, etc.)
            key: Key within domain (name, database, entropy_def, etc.)
            value: Observed value
            source: Where this came from (CLI, chat, ingest, etc.)
            authority: Initial authority level
            metadata: Optional additional metadata
        
        Returns:
            Created Observation
        """
        obs_id = f"obs_{domain}_{key}_{datetime.now().timestamp()}"
        
        obs = Observation(
            observation_id=obs_id,
            domain=domain,
            key=key,
            value=value,
            source=source,
            authority=authority,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.observations[obs_id] = obs
        
        # Trigger aggregation
        self._aggregate_observations(domain, key)
        
        return obs
    
    def _aggregate_observations(self, domain: str, key: str):
        """
        Aggregate all observations for (domain, key) into canonical fact(s).
        
        This is where the magic happens:
        - Group observations by value
        - Count support for each value
        - Apply authority weighting
        - Detect conflicts
        - Promote/demote facts
        """
        # Get all observations for this (domain, key)
        relevant_obs = [
            obs for obs in self.observations.values()
            if obs.domain == domain and obs.key == key
        ]
        
        if not relevant_obs:
            return
        
        # Group by value
        value_groups: Dict[Any, List[Observation]] = {}
        for obs in relevant_obs:
            # Convert value to hashable
            val_key = str(obs.value)
            if val_key not in value_groups:
                value_groups[val_key] = []
            value_groups[val_key].append(obs)
        
        # Find existing facts for this (domain, key)
        existing_facts = [
            fact_id for fact_id in self.facts.keys()
            if self.facts[fact_id].domain == domain 
            and self.facts[fact_id].key == key
        ]
        
        # If single value group and strong support → promote to fact
        if len(value_groups) == 1:
            val_key = list(value_groups.keys())[0]
            obs_group = value_groups[val_key]
            
            # Calculate weighted support
            weighted_support = self._calculate_weighted_support(obs_group)
            
            # Check if we should create/update fact
            if weighted_support >= self.promotion_threshold or self._has_strong_authority(obs_group):
                self._create_or_update_fact(domain, key, obs_group[0].value, obs_group)
        
        # Multiple value groups → conflict!
        elif len(value_groups) >= self.conflict_threshold:
            self._create_conflict(domain, key, value_groups)
    
    def _calculate_weighted_support(self, observations: List[Observation]) -> float:
        """
        Calculate weighted support from observations.
        
        Weighting factors:
        - Authority level (TEST=0.1, SHORT_TERM=1, STABLE=5, LONG_TERM=10)
        - Source type (CLI_TEST=0.1, CHAT_USER=1, INGEST_DOC=3)
        - Recency (newer = higher weight)
        """
        total_weight = 0.0
        
        authority_weights = {
            AuthorityLevel.TEST: 0.1,
            AuthorityLevel.SHORT_TERM: 1.0,
            AuthorityLevel.MEDIUM_TERM: 2.0,
            AuthorityLevel.STABLE: 5.0,
            AuthorityLevel.LONG_TERM: 10.0
        }
        
        source_weights = {
            SourceType.CLI_TEST: 0.1,
            SourceType.CHAT_USER: 1.0,
            SourceType.MEMORY_ENHANCEMENT: 1.5,
            SourceType.INGEST_DOC: 3.0,
            SourceType.SYSTEM_DEFAULT: 2.0
        }
        
        for obs in observations:
            # Base weight from authority
            weight = authority_weights.get(obs.authority, 1.0)
            
            # Multiply by source weight
            weight *= source_weights.get(obs.source, 1.0)
            
            # Temporal decay (newer observations worth more)
            age_days = (datetime.now() - obs.timestamp).days
            temporal_factor = max(0.1, 1.0 - (age_days / 365))
            weight *= temporal_factor
            
            total_weight += weight
        
        return total_weight
    
    def _has_strong_authority(self, observations: List[Observation]) -> bool:
        """Check if any observation has strong authority (STABLE or LONG_TERM)"""
        return any(
            obs.authority in [AuthorityLevel.STABLE, AuthorityLevel.LONG_TERM]
            for obs in observations
        )
    
    def _create_or_update_fact(
        self,
        domain: str,
        key: str,
        value: Any,
        supporting_obs: List[Observation]
    ):
        """Create new fact or update existing one"""
        # Find existing fact
        existing = None
        for fact_id, fact in self.facts.items():
            if fact.domain == domain and fact.key == key and fact.value == value:
                existing = fact
                break
        
        if existing:
            # Update existing fact
            existing.support_count = len(supporting_obs)
            existing.supporting_observations = [obs.observation_id for obs in supporting_obs]
            existing.updated_at = datetime.now()
            existing.last_observed = max(obs.timestamp for obs in supporting_obs)
            
            # Promote status if support is strong
            weighted_support = self._calculate_weighted_support(supporting_obs)
            if weighted_support >= 10 and existing.status == FactStatus.ACTIVE:
                existing.status = FactStatus.STABLE
                existing.authority = AuthorityLevel.STABLE
        else:
            # Create new fact
            fact_id = f"fact_{domain}_{key}_{datetime.now().timestamp()}"
            
            # Determine initial status
            if any(obs.source == SourceType.CLI_TEST for obs in supporting_obs):
                status = FactStatus.TEST_ONLY
            else:
                status = FactStatus.ACTIVE
            
            # Determine authority from observations
            max_authority = max(obs.authority for obs in supporting_obs)
            
            fact = CanonicalFact(
                fact_id=fact_id,
                domain=domain,
                key=key,
                value=value,
                status=status,
                authority=max_authority,
                support_count=len(supporting_obs),
                supporting_observations=[obs.observation_id for obs in supporting_obs]
            )
            
            self.facts[fact_id] = fact
            
            # Update index
            index_key = (domain, key)
            if index_key not in self.domain_key_index:
                self.domain_key_index[index_key] = []
            self.domain_key_index[index_key].append(fact_id)
    
    def _create_conflict(
        self,
        domain: str,
        key: str,
        value_groups: Dict[Any, List[Observation]]
    ):
        """Create conflict record for resolution"""
        conflict_id = f"conflict_{domain}_{key}_{datetime.now().timestamp()}"
        
        competing_values = list(value_groups.keys())
        
        conflict = Conflict(
            conflict_id=conflict_id,
            domain=domain,
            key=key,
            competing_facts=[],
            competing_values=competing_values
        )
        
        self.conflicts[conflict_id] = conflict
        
        # Auto-resolve immediately
        self._resolve_conflict(conflict_id)
    
    def detect_conflicts(self, domain: Optional[str] = None) -> List[Conflict]:
        """
        Detect all unresolved conflicts.
        
        Args:
            domain: Optional domain filter
        
        Returns:
            List of unresolved conflicts
        """
        conflicts = []
        
        for conflict in self.conflicts.values():
            if not conflict.resolved:
                if domain is None or conflict.domain == domain:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _resolve_conflict(self, conflict_id: str):
        """
        Resolve conflict using authority-weighted resolution.
        
        Resolution rules:
        1. Sort by authority (LONG_TERM > STABLE > MEDIUM_TERM > SHORT_TERM > TEST)
        2. Weight by source (INGEST_DOC > CHAT_USER > CLI_TEST)
        3. Weight by support count
        4. Weight by recency
        
        Winner → ACTIVE/STABLE
        Losers → DEPRECATED or SUSPECT
        """
        conflict = self.conflicts.get(conflict_id)
        if not conflict or conflict.resolved:
            return
        
        # Get all observations for this (domain, key)
        relevant_obs = [
            obs for obs in self.observations.values()
            if obs.domain == conflict.domain and obs.key == conflict.key
        ]
        
        # Group by value and calculate scores
        value_scores: Dict[str, float] = {}
        value_obs: Dict[str, List[Observation]] = {}
        
        for obs in relevant_obs:
            val_key = str(obs.value)
            if val_key not in value_obs:
                value_obs[val_key] = []
            value_obs[val_key].append(obs)
        
        for val_key, obs_group in value_obs.items():
            value_scores[val_key] = self._calculate_weighted_support(obs_group)
        
        # Find winner
        winner_val = max(value_scores, key=value_scores.get)
        winner_obs = value_obs[winner_val]
        
        # Create/update winning fact
        self._create_or_update_fact(
            conflict.domain,
            conflict.key,
            winner_obs[0].value,
            winner_obs
        )
        
        # Deprecate losing facts
        for val_key, obs_group in value_obs.items():
            if val_key != winner_val:
                for fact in self.facts.values():
                    if (fact.domain == conflict.domain 
                        and fact.key == conflict.key 
                        and str(fact.value) == val_key):
                        fact.status = FactStatus.DEPRECATED
        
        # Mark conflict as resolved
        conflict.resolved = True
        conflict.resolution = winner_val
    
    def get_canonical_truth(
        self,
        domain: str,
        key: str,
        include_test: bool = False
    ) -> Optional[Any]:
        """
        Get current canonical truth for (domain, key).
        
        Returns the value from the highest-authority ACTIVE/STABLE fact.
        By default excludes TEST_ONLY facts.
        
        Args:
            domain: Domain to query
            key: Key to query
            include_test: Whether to include TEST_ONLY facts
        
        Returns:
            Current canonical value or None
        """
        index_key = (domain, key)
        fact_ids = self.domain_key_index.get(index_key, [])
        
        # Filter to ACTIVE/STABLE facts
        candidates = [
            self.facts[fact_id] for fact_id in fact_ids
            if fact_id in self.facts
            and self.facts[fact_id].status in [FactStatus.ACTIVE, FactStatus.STABLE]
        ]
        
        # Filter out TEST_ONLY unless explicitly requested
        if not include_test:
            candidates = [f for f in candidates if f.status != FactStatus.TEST_ONLY]
        
        if not candidates:
            return None
        
        # Return highest authority fact
        best = max(candidates, key=lambda f: f.authority.value)
        return best.value
    
    def promote_fact(self, fact_id: str):
        """Promote fact to higher authority level"""
        fact = self.facts.get(fact_id)
        if not fact:
            return
        
        if fact.status == FactStatus.CANDIDATE:
            fact.status = FactStatus.ACTIVE
        elif fact.status == FactStatus.ACTIVE:
            fact.status = FactStatus.STABLE
            fact.authority = AuthorityLevel.STABLE
        elif fact.status == FactStatus.STABLE:
            fact.authority = AuthorityLevel.LONG_TERM
        
        fact.updated_at = datetime.now()
    
    def demote_fact(self, fact_id: str):
        """Demote fact to lower authority level"""
        fact = self.facts.get(fact_id)
        if not fact:
            return
        
        if fact.status == FactStatus.STABLE:
            fact.status = FactStatus.ACTIVE
        elif fact.status == FactStatus.ACTIVE:
            fact.status = FactStatus.SUSPECT
        elif fact.status == FactStatus.SUSPECT:
            fact.status = FactStatus.DEPRECATED
        
        fact.updated_at = datetime.now()
    
    def apply_temporal_decay(self):
        """
        Apply temporal decay to old unused facts.
        
        Facts not observed in temporal_decay_days get demoted.
        """
        cutoff = datetime.now() - timedelta(days=self.temporal_decay_days)
        
        for fact in self.facts.values():
            if fact.last_observed < cutoff and fact.status != FactStatus.DEPRECATED:
                self.demote_fact(fact.fact_id)
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        status_counts = {}
        for fact in self.facts.values():
            status = fact.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_observations": len(self.observations),
            "total_facts": len(self.facts),
            "unresolved_conflicts": len([c for c in self.conflicts.values() if not c.resolved]),
            "status_distribution": status_counts,
            "domains": len(set(f.domain for f in self.facts.values()))
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Self-Healing Canonical Layer")
    print("=" * 60)
    
    shc = SelfHealingCanonical()
    
    # Test 1: Register observations
    print("\n1️⃣ Register observations")
    
    # CLI test says "Morpheus"
    shc.register_observation(
        domain="identity",
        key="name",
        value="Morpheus",
        source=SourceType.CLI_TEST,
        authority=AuthorityLevel.TEST
    )
    
    # User says "Morten" multiple times
    for i in range(3):
        shc.register_observation(
            domain="identity",
            key="name",
            value="Morten",
            source=SourceType.CHAT_USER,
            authority=AuthorityLevel.SHORT_TERM
        )
    
    # Test 2: Get canonical truth
    print("\n2️⃣ Get canonical truth")
    truth = shc.get_canonical_truth("identity", "name")
    print(f"Canonical name: {truth}")
    print(f"Expected: Morten (TEST loses to CHAT_USER)")
    
    # Test 3: Detect conflicts
    print("\n3️⃣ Detect conflicts")
    conflicts = shc.detect_conflicts()
    print(f"Unresolved conflicts: {len(conflicts)}")
    
    # Test 4: Stats
    print("\n4️⃣ System stats")
    stats = shc.get_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Self-Healing Canonical Layer test complete")
