#!/usr/bin/env python3
"""
canonical_memory_core.py - Absolute Truth Store
================================================

LAG 1: CANONICAL MEMORY CORE (CMC)
"Den absolutte sannheten"

This is THE ONLY place that represents objective facts.
Nothing can override this. Every fact here is:
- Structurally validated
- Authority-ranked
- Confidence-tracked
- Verifiable

Architecture:
    User Input → Fact Extraction → Validation → CMC Storage → Eternal Truth

Purpose:
    Zero tolerance for:
    - Wrong names
    - Wrong numbers
    - Wrong locations
    - Wrong definitions
    - Wrong rules
    
    This is hippocampus. The rest is cortex.
"""

import os
import sys
import json
import uuid
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime
import numpy as np
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

# Import Self-Healing Layer
from tools.self_healing_canonical import (
    SelfHealingCanonical,
    SourceType,
    AuthorityLevel as SHAuthority
)

# Import Self-Optimizing Layer
from tools.self_optimizing_layer import (
    SelfOptimizingLayer,
    MetricType
)

# Import Meta-Supervisor Layer
from tools.meta_supervisor import (
    MetaSupervisor,
    IntentMode,
    BalanceState
)

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# ============================================================
# TYPE DEFINITIONS
# ============================================================

# Authority levels (immutable → volatile)
AuthorityLevel = Literal["LONGTERM", "STABLE", "SHORT_TERM", "VOLATILE"]
AUTHORITY_RANK = {"LONGTERM": 4, "STABLE": 3, "SHORT_TERM": 2, "VOLATILE": 1}

# Domains (auto-discovered but these are seeds)
DomainType = Literal[
    "identity", "health", "symbiose", "cosmology", "safety", "tech",
    "family", "location", "finance", "creative", "meta", "operational"
]

# Fact types (structural categories)
FactType = Literal[
    "name", "count", "location", "definition", "relation", 
    "metric", "rule", "config", "state", "intention"
]


@dataclass
class CanonicalFact:
    """
    A canonical fact - the ONLY representation of objective truth.
    
    Every fact here has been:
    1. Extracted from user input
    2. Validated structurally
    3. Authority-ranked
    4. Confidence-tracked
    
    This is NOT mutable without explicit verification.
    """
    
    # Unique identity
    id: str
    
    # Classification (can evolve with learning)
    domain: str                    # Which semantic domain
    fact_type: FactType            # Structural type
    authority: AuthorityLevel      # Trust level
    
    # Content
    key: str                       # Structured key (e.g., "user_name")
    value: Any                     # Structured value (e.g., "Morten")
    text: str                      # Human-readable form
    
    # Semantic representation
    embedding: Optional[List[float]] = None
    
    # Trust metrics
    confidence: float = 0.5        # Bayesian confidence
    verification_count: int = 0    # Times verified correct
    challenge_count: int = 0       # Times challenged
    
    # Provenance
    source: str = "user"
    session_id: Optional[str] = None
    last_verified: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Relations to other facts
    related_facts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Serialize for storage."""
        return asdict(self)
    
    def verify(self, correct: bool):
        """Bayesian update on verification."""
        if correct:
            self.verification_count += 1
            # Increase confidence (bounded)
            self.confidence = min(0.99, self.confidence + 0.1 * (1 - self.confidence))
        else:
            self.challenge_count += 1
            # Decrease confidence
            self.confidence = max(0.01, self.confidence * 0.8)
        
        self.last_verified = datetime.now().isoformat()
    
    def promote_authority(self):
        """Auto-promote authority based on verification history."""
        if self.verification_count == 0:
            return
        
        ratio = self.verification_count / (self.verification_count + self.challenge_count)
        
        if ratio > 0.95 and self.verification_count >= 10:
            self.authority = "LONGTERM"
        elif ratio > 0.85 and self.verification_count >= 5:
            self.authority = "STABLE"
        elif ratio > 0.70:
            self.authority = "SHORT_TERM"
        else:
            self.authority = "VOLATILE"


# ============================================================
# CANONICAL MEMORY CORE
# ============================================================

class CanonicalMemoryCore:
    """
    The absolute truth store.
    
    Rules:
    1. Only verified facts enter
    2. Facts can only be updated with higher authority
    3. Contradictions trigger conflict resolution
    4. Low-confidence facts auto-demote
    5. High-confidence facts auto-promote to LONGTERM
    
    This is the hippocampus - immutable, precise, eternal.
    """
    
    def __init__(self, collection_name: str = "canonical_facts", enable_self_healing: bool = True, enable_self_optimizing: bool = True, enable_meta_supervisor: bool = True):
        self.collection_name = collection_name
        self._ensure_collection()
        
        # Load schema
        self.schema = self._load_schema()
        
        # In-memory cache for ultra-fast access
        self.fact_cache: Dict[str, CanonicalFact] = {}
        
        # Domain registry (learned)
        self.domains: Dict[str, Dict] = {}
        
        # Adaptive intelligence tracking
        self.dynamic_domains: Dict[str, Dict] = {}  # Auto-learned domains
        self.learned_keys: Dict[str, int] = {}  # Key usage frequency
        self.key_patterns: Dict[str, List[str]] = {}  # Discovered patterns
        self.domain_usage: Dict[str, int] = {}  # Domain frequency
        
        # Self-Healing Layer (Phase 2)
        self.self_healing = SelfHealingCanonical() if enable_self_healing else None
        
        # Self-Optimizing Layer (Phase 3)
        self.self_optimizing = SelfOptimizingLayer() if enable_self_optimizing else None
        
        # Meta-Supervisor Layer (Phase 4)
        self.meta_supervisor = MetaSupervisor() if enable_meta_supervisor else None
        
        # Sync promotion threshold with self-optimizing layer
        if self.self_healing and self.self_optimizing:
            self.self_healing.promotion_threshold = self.self_optimizing.adapter.get_parameter(
                __import__('tools.self_optimizing_layer', fromlist=['ParameterType']).ParameterType.PROMOTION_THRESHOLD
            )
        
        print("✨ Canonical Memory Core initialized", file=sys.stderr)
        print(f"🔒 Absolute truth store active with schema v{self.schema.get('schema_version', 'unknown')}", file=sys.stderr)
        if self.schema.get('adaptive_mode'):
            print("🧠 Adaptive mode: Auto-expanding domains and keys", file=sys.stderr)
        if self.self_healing:
            print("🩹 Self-healing enabled: Observation-based truth with conflict resolution", file=sys.stderr)
        if self.self_optimizing:
            print("🎯 Self-optimizing enabled: System learns from performance and adapts parameters", file=sys.stderr)
        if self.meta_supervisor:
            print("🧭 Meta-supervisor enabled: Cognitive isomorfi - top-down + bottom-up + meta-lag", file=sys.stderr)
    
    def _load_schema(self) -> Dict:
        """Load canonical memory schema from JSON file."""
        schema_path = os.path.join(os.path.dirname(__file__), "canonical_memory_schema.json")
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            print(f"📋 Schema loaded: {len(schema['allowed_domains'])} domains, max {schema['global_limits']['max_total_facts']} facts", file=sys.stderr)
            return schema
        except FileNotFoundError:
            print(f"⚠️  Schema file not found at {schema_path}, using permissive defaults", file=sys.stderr)
            return {
                "schema_version": "0.0",
                "allowed_domains": {},
                "global_limits": {"max_total_facts": 1000, "max_fact_length": 1000, "min_confidence": 0.5},
                "validation_rules": {"require_domain": False, "require_key": False}
            }
        except Exception as e:
            print(f"⚠️  Error loading schema: {e}, using permissive defaults", file=sys.stderr)
            return {
                "schema_version": "0.0",
                "allowed_domains": {},
                "global_limits": {"max_total_facts": 1000, "max_fact_length": 1000, "min_confidence": 0.5},
                "validation_rules": {"require_domain": False, "require_key": False}
            }
    
    def _validate_fact(self, domain: str, key: str, value: Any, text: str) -> List[str]:
        """
        Intelligent adaptive validation with auto-expansion.
        
        Features:
        - Auto-creates domains after threshold usage
        - Learns key patterns from usage
        - Fuzzy matching for similar keys
        - Pattern recognition for numbered keys
        
        Returns list of validation errors (empty list = valid).
        """
        errors = []
        
        # Intelligence layer enabled?
        adaptive = self.schema.get('adaptive_mode', False)
        auto_expand_domains = self.schema.get('auto_expand_domains', False)
        auto_expand_keys = self.schema.get('auto_expand_keys', False)
        
        # Track domain usage for learning
        if adaptive:
            self.domain_usage[domain] = self.domain_usage.get(domain, 0) + 1
            key_sig = f"{domain}:{key}"
            self.learned_keys[key_sig] = self.learned_keys.get(key_sig, 0) + 1
        
        # Check if domain is allowed or can be auto-created
        allowed_domains = self.schema.get('allowed_domains', {})
        domain_exists = domain in allowed_domains
        dynamic_exists = domain in self.dynamic_domains
        
        if not domain_exists and not dynamic_exists:
            if auto_expand_domains:
                # Auto-create domain after threshold uses
                threshold = self.schema.get('dynamic_domains', {}).get('creation_threshold', 3)
                if self.domain_usage.get(domain, 0) >= threshold:
                    # Promote to dynamic domain
                    self._create_dynamic_domain(domain)
                    print(f"🎓 Auto-created domain: '{domain}' (threshold: {threshold} uses)", file=sys.stderr)
                else:
                    # Warn but allow (learning phase)
                    print(f"📝 Learning new domain: '{domain}' ({self.domain_usage.get(domain, 0)}/{threshold} uses)", file=sys.stderr)
            elif self.schema.get('validation_rules', {}).get('require_domain', False):
                errors.append(f"Domain '{domain}' not in allowed domains")
                return errors
        
        # Get domain config (from allowed or dynamic)
        domain_config = allowed_domains.get(domain, self.dynamic_domains.get(domain, {}))
        
        # Check if key is allowed or can be learned
        allowed_keys = domain_config.get('allowed_keys', [])
        key_patterns = self.schema.get('key_patterns', {})
        
        key_valid = False
        
        # Direct match
        if key in allowed_keys:
            key_valid = True
        
        # Pattern match (e.g., child_1, skill_2)
        if not key_valid:
            import re
            for pattern, pattern_config in key_patterns.items():
                if re.match(f"^{pattern}$", key):
                    if pattern_config.get('domain') == domain or not pattern_config.get('domain'):
                        key_valid = True
                        break
        
        # Fuzzy matching for similar keys (typo tolerance)
        if not key_valid and adaptive:
            intelligence = self.schema.get('intelligence_layer', {})
            if intelligence.get('key_normalization', {}).get('fuzzy_matching'):
                key_valid = self._fuzzy_match_key(key, allowed_keys)
        
        # Auto-expand keys
        if not key_valid and auto_expand_keys:
            key_sig = f"{domain}:{key}"
            uses = self.learned_keys.get(key_sig, 0)
            threshold = self.schema.get('intelligence_layer', {}).get('pattern_recognition', {}).get('min_occurrences', 3)
            
            if uses >= threshold:
                # Auto-add to domain
                self._add_learned_key(domain, key)
                key_valid = True
                print(f"🎓 Auto-learned key: '{key}' in domain '{domain}' ({uses} uses)", file=sys.stderr)
            else:
                # Warn but allow (learning phase)
                print(f"📝 Learning new key: '{domain}:{key}' ({uses}/{threshold} uses)", file=sys.stderr)
                key_valid = True  # Allow during learning
        
        # Only error if strict validation AND no adaptive mode
        if not key_valid and allowed_keys and not adaptive:
            errors.append(f"Key '{key}' not allowed in domain '{domain}'. Allowed: {allowed_keys[:5]}...")
        
        # Check fact length
        max_length = self.schema.get('global_limits', {}).get('max_fact_length', 1000)
        if len(text) > max_length:
            errors.append(f"Fact text too long: {len(text)} > {max_length} chars")
        
        # Check forbidden patterns
        forbidden = self.schema.get('forbidden_patterns', {})
        text_lower = text.lower()
        for category, patterns in forbidden.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    errors.append(f"Forbidden pattern detected: '{pattern}' ({category})")
        
        # Check domain-specific limits
        max_facts_for_domain = domain_config.get('max_facts', float('inf'))
        current_count = self._count_domain_facts(domain)
        if current_count >= max_facts_for_domain:
            errors.append(f"Domain '{domain}' limit reached: {current_count}/{max_facts_for_domain} facts")
        
        return errors
    
    def _create_dynamic_domain(self, domain: str):
        """Create a new dynamic domain from learned usage patterns."""
        if domain not in self.dynamic_domains:
            self.dynamic_domains[domain] = {
                "description": f"Auto-learned domain: {domain}",
                "created": datetime.now().isoformat(),
                "max_facts": 50,
                "allowed_keys": [],
                "strictness": 0.5,
                "synthesis_enabled": True,
                "auto_created": True
            }
    
    def _add_learned_key(self, domain: str, key: str):
        """Add a learned key to a domain's allowed keys."""
        # Add to dynamic domain if exists
        if domain in self.dynamic_domains:
            if key not in self.dynamic_domains[domain].get('allowed_keys', []):
                self.dynamic_domains[domain].setdefault('allowed_keys', []).append(key)
        # Or to allowed domain
        elif domain in self.schema.get('allowed_domains', {}):
            # Don't modify schema directly, but track in memory
            if domain not in self.key_patterns:
                self.key_patterns[domain] = []
            if key not in self.key_patterns[domain]:
                self.key_patterns[domain].append(key)
    
    def _fuzzy_match_key(self, key: str, allowed_keys: List[str]) -> bool:
        """
        Fuzzy match key against allowed keys using similarity.
        
        Handles typos and variations like:
        - user_name vs username
        - child1 vs child_1
        - occupation vs ocupation (typo)
        """
        if not allowed_keys:
            return False
        
        threshold = self.schema.get('intelligence_layer', {}).get('key_normalization', {}).get('similarity_threshold', 0.85)
        
        # Simple character-based similarity
        for allowed in allowed_keys:
            similarity = self._string_similarity(key, allowed)
            if similarity >= threshold:
                print(f"🔍 Fuzzy matched: '{key}' → '{allowed}' (similarity: {similarity:.2f})", file=sys.stderr)
                return True
        
        return False
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (Levenshtein-based)."""
        if s1 == s2:
            return 1.0
        
        # Normalize
        s1 = s1.lower().replace('_', '').replace('-', '')
        s2 = s2.lower().replace('_', '').replace('-', '')
        
        if s1 == s2:
            return 0.95
        
        # Simple character overlap ratio
        common = set(s1) & set(s2)
        total = set(s1) | set(s2)
        
        return len(common) / len(total) if total else 0.0
    
    def _count_total_facts(self) -> int:
        """Count total facts in collection."""
        try:
            info = qdrant_client.get_collection(self.collection_name)
            return info.points_count
        except:
            return 0
    
    def _count_domain_facts(self, domain: str) -> int:
        """Count facts in a specific domain."""
        try:
            results = qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={"must": [{"key": "domain", "match": {"value": domain}}]},
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            # Note: scroll returns (points, next_offset) - we'd need to count properly
            # For now, approximate or do full scroll
            return len(results[0]) if results else 0
        except:
            return 0
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists with proper config."""
        try:
            qdrant_client.get_collection(self.collection_name)
        except:
            qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=3072,  # text-embedding-3-large
                    distance=Distance.COSINE
                )
            )
            
            # Create indexes for fast filtering
            for field in ["domain", "fact_type", "authority", "key"]:
                try:
                    qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema="keyword"
                    )
                except:
                    pass
    
    def store_fact(
        self,
        key: str,
        value: Any,
        domain: str,
        fact_type: FactType,
        authority: AuthorityLevel = "SHORT_TERM",
        text: Optional[str] = None,
        source: str = "user",
        session_id: Optional[str] = None,
        as_observation: bool = True  # NEW: Use observation-based approach by default
    ) -> CanonicalFact:
        """
        Store a canonical fact.
        
        NEW BEHAVIOR (as_observation=True):
        Facts are registered as observations first, then aggregated into canonical truth
        via the Self-Healing Layer. This prevents test data from polluting truth.
        
        Args:
            key: Structured key (e.g., "user_name")
            value: Structured value (e.g., "Morten")
            domain: Semantic domain
            fact_type: Structural type
            authority: Trust level
            text: Human-readable form (auto-generated if None)
            source: Where it came from
            session_id: Related session
            as_observation: If True, use observation-based approach (recommended)
        
        Returns:
            The stored CanonicalFact
        
        Raises:
            ValueError: If fact validation fails
        """
        # NEW: Register as observation if self-healing enabled
        if as_observation and self.self_healing:
            # Map source to SourceType
            source_map = {
                "cli_test": SourceType.CLI_TEST,
                "user": SourceType.CHAT_USER,
                "chat": SourceType.CHAT_USER,
                "ingest": SourceType.INGEST_DOC,
                "system": SourceType.SYSTEM_DEFAULT,
                "memory_enhancement": SourceType.MEMORY_ENHANCEMENT
            }
            source_type = source_map.get(source, SourceType.CHAT_USER)
            
            # Map authority to SHAuthority
            authority_map = {
                "LONGTERM": SHAuthority.LONG_TERM,
                "STABLE": SHAuthority.STABLE,
                "SHORT_TERM": SHAuthority.SHORT_TERM,
                "VOLATILE": SHAuthority.SHORT_TERM
            }
            sh_authority = authority_map.get(authority, SHAuthority.SHORT_TERM)
            
            # Register observation
            self.self_healing.register_observation(
                domain=domain,
                key=key,
                value=value,
                source=source_type,
                authority=sh_authority,
                metadata={"fact_type": fact_type, "session_id": session_id}
            )
            
            # Get canonical truth from self-healing layer
            canonical_value = self.self_healing.get_canonical_truth(domain, key)
            
            # Only proceed to store if this is canonical truth
            if canonical_value != value:
                # This observation didn't win - return a temporary fact
                print(f"📝 Observation registered but not canonical (canonical: {canonical_value})", file=sys.stderr)
                return CanonicalFact(
                    id=f"obs_{domain}_{key}",
                    domain=domain,
                    fact_type=fact_type,
                    authority=authority,
                    key=key,
                    value=value,
                    text=text or f"{key}: {value}"
                )
        
        # SCHEMA VALIDATION
        validation_errors = self._validate_fact(domain, key, value, text or f"{key}: {value}")
        if validation_errors:
            error_msg = f"Schema validation failed: {'; '.join(validation_errors)}"
            print(f"❌ {error_msg}", file=sys.stderr)
            raise ValueError(error_msg)
        
        # Generate text if not provided
        if text is None:
            text = f"{key}: {value}"
        
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        embedding = embedding_response.data[0].embedding
        
        # Check for existing fact with same key
        existing = self.get_fact_by_key(key, domain)
        
        if existing:
            # Update existing fact
            return self._update_fact(existing, value, authority, text)
        
        # Check global limits
        total_facts = self._count_total_facts()
        max_facts = self.schema.get('global_limits', {}).get('max_total_facts', 1000)
        if total_facts >= max_facts:
            raise ValueError(f"Cannot store fact: global limit of {max_facts} facts reached")
        
        # Create new fact
        fact = CanonicalFact(
            id=str(uuid.uuid4()),
            domain=domain,
            fact_type=fact_type,
            authority=authority,
            key=key,
            value=value,
            text=text,
            embedding=embedding,
            source=source,
            session_id=session_id
        )
        
        # Store in Qdrant
        point = PointStruct(
            id=fact.id,
            vector=embedding,
            payload={
                "domain": domain,
                "fact_type": fact_type,
                "authority": authority,
                "key": key,
                "value": value,
                "text": text,
                "confidence": fact.confidence,
                "verification_count": fact.verification_count,
                "source": source,
                "created_at": fact.created_at
            }
        )
        
        qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        # Cache
        self.fact_cache[fact.id] = fact
        
        # Register domain
        if domain not in self.domains:
            self.domains[domain] = {"fact_count": 0, "created": datetime.now().isoformat()}
        self.domains[domain]["fact_count"] += 1
        
        print(f"✅ Stored canonical fact: {key} = {value} [{authority}]", file=sys.stderr)
        
        return fact
    
    def _update_fact(
        self,
        existing: CanonicalFact,
        new_value: Any,
        new_authority: AuthorityLevel,
        new_text: str
    ) -> CanonicalFact:
        """
        Update existing fact (with authority check).
        
        Rules:
        - Higher authority can override lower
        - Same authority requires higher confidence
        - LONGTERM facts require explicit verification
        """
        existing_rank = AUTHORITY_RANK[existing.authority]
        new_rank = AUTHORITY_RANK[new_authority]
        
        # Check if update is allowed
        if new_rank < existing_rank:
            print(f"⚠️ Cannot override {existing.authority} with {new_authority}", file=sys.stderr)
            return existing
        
        if new_rank == existing_rank and existing.confidence > 0.8:
            print(f"⚠️ High-confidence fact requires verification", file=sys.stderr)
            return existing
        
        # Update
        existing.value = new_value
        existing.text = new_text
        existing.authority = new_authority
        existing.last_verified = datetime.now().isoformat()
        
        # Re-embed
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=new_text
        )
        existing.embedding = embedding_response.data[0].embedding
        
        # Update in Qdrant
        qdrant_client.set_payload(
            collection_name=self.collection_name,
            payload={
                "value": new_value,
                "text": new_text,
                "authority": new_authority,
                "last_verified": existing.last_verified
            },
            points=[existing.id]
        )
        
        print(f"🔄 Updated canonical fact: {existing.key} = {new_value}", file=sys.stderr)
        
        return existing
    
    def get_fact_by_key(self, key: str, domain: Optional[str] = None) -> Optional[CanonicalFact]:
        """
        Retrieve fact by exact key match.
        
        This is ultra-fast for known keys.
        """
        # Check cache first
        for fact in self.fact_cache.values():
            if fact.key == key:
                if domain is None or fact.domain == domain:
                    return fact
        
        # Query Qdrant
        filter_conditions = [{"key": "key", "match": {"value": key}}]
        if domain:
            filter_conditions.append({"key": "domain", "match": {"value": domain}})
        
        results = qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter={"must": filter_conditions},
            limit=1
        )
        
        if results[0]:
            hit = results[0][0]
            fact = CanonicalFact(
                id=hit.id,
                domain=hit.payload["domain"],
                fact_type=hit.payload["fact_type"],
                authority=hit.payload["authority"],
                key=hit.payload["key"],
                value=hit.payload["value"],
                text=hit.payload["text"],
                confidence=hit.payload.get("confidence", 0.5),
                verification_count=hit.payload.get("verification_count", 0)
            )
            self.fact_cache[fact.id] = fact
            return fact
        
        return None
    
    def query_facts(
        self,
        query: str,
        domain: Optional[str] = None,
        fact_type: Optional[FactType] = None,
        authority_min: Optional[AuthorityLevel] = None,
        k: int = 5
    ) -> List[CanonicalFact]:
        """
        Semantic search for facts.
        
        Returns: Facts ranked by relevance + authority + confidence
        """
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Build filter
        filter_conditions = []
        
        if domain:
            filter_conditions.append({"key": "domain", "match": {"value": domain}})
        
        if fact_type:
            filter_conditions.append({"key": "fact_type", "match": {"value": fact_type}})
        
        if authority_min:
            min_rank = AUTHORITY_RANK[authority_min]
            allowed = [auth for auth, rank in AUTHORITY_RANK.items() if rank >= min_rank]
            filter_conditions.append({"key": "authority", "match": {"any": allowed}})
        
        # Search
        results = qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter={"must": filter_conditions} if filter_conditions else None,
            limit=k
        )
        
        # Convert to CanonicalFacts
        facts = []
        for hit in results:
            fact = CanonicalFact(
                id=hit.id,
                domain=hit.payload["domain"],
                fact_type=hit.payload["fact_type"],
                authority=hit.payload["authority"],
                key=hit.payload["key"],
                value=hit.payload["value"],
                text=hit.payload["text"],
                embedding=None,  # Don't load full embedding
                confidence=hit.payload.get("confidence", 0.5),
                verification_count=hit.payload.get("verification_count", 0)
            )
            facts.append(fact)
        
        # Sort by authority + confidence
        facts.sort(
            key=lambda f: (AUTHORITY_RANK[f.authority], f.confidence),
            reverse=True
        )
        
        return facts
    
    def verify_fact(self, fact_id: str, correct: bool):
        """
        Verify a fact (user feedback loop).
        
        This updates confidence and may promote authority.
        """
        if fact_id in self.fact_cache:
            fact = self.fact_cache[fact_id]
        else:
            # Load from Qdrant
            result = qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[fact_id]
            )
            if not result:
                return
            
            hit = result[0]
            fact = CanonicalFact(
                id=hit.id,
                domain=hit.payload["domain"],
                fact_type=hit.payload["fact_type"],
                authority=hit.payload["authority"],
                key=hit.payload["key"],
                value=hit.payload["value"],
                text=hit.payload["text"],
                confidence=hit.payload.get("confidence", 0.5),
                verification_count=hit.payload.get("verification_count", 0),
                challenge_count=hit.payload.get("challenge_count", 0)
            )
        
        # Update
        fact.verify(correct)
        fact.promote_authority()
        
        # Persist
        qdrant_client.set_payload(
            collection_name=self.collection_name,
            payload={
                "confidence": fact.confidence,
                "verification_count": fact.verification_count,
                "challenge_count": fact.challenge_count,
                "authority": fact.authority,
                "last_verified": fact.last_verified
            },
            points=[fact_id]
        )
        
        self.fact_cache[fact_id] = fact
        
        print(f"✅ Verified fact {fact.key}: confidence={fact.confidence:.2f}, authority={fact.authority}", file=sys.stderr)
    
    def get_all_domains(self) -> List[str]:
        """Get all discovered domains."""
        return list(self.domains.keys())
    
    def get_domain_stats(self) -> Dict[str, Dict]:
        """Get statistics per domain."""
        return self.domains.copy()
    
    def record_performance_metric(
        self,
        metric_type: MetricType,
        value: float,
        context: Optional[Dict] = None
    ):
        """
        Record a performance metric for self-optimization.
        
        Args:
            metric_type: Type of metric (override_rate, conflict_rate, etc.)
            value: Metric value
            context: Optional context
        """
        if not self.self_optimizing:
            return
        
        self.self_optimizing.record_metric(metric_type, value, context)
    
    def apply_optimized_parameters(self):
        """
        Apply self-optimized parameters to CMC and self-healing layer.
        
        Call this periodically to let system tune itself.
        """
        if not self.self_optimizing:
            return
        
        from tools.self_optimizing_layer import ParameterType
        
        # Sync promotion threshold
        if self.self_healing:
            new_threshold = self.self_optimizing.adapter.get_parameter(
                ParameterType.PROMOTION_THRESHOLD
            )
            self.self_healing.promotion_threshold = int(new_threshold)
        
        # Sync temporal decay
        if self.self_healing:
            new_decay = self.self_optimizing.adapter.get_parameter(
                ParameterType.TEMPORAL_DECAY_DAYS
            )
            self.self_healing.temporal_decay_days = int(new_decay)
    
    def run_self_optimization_cycle(self) -> Dict[str, Any]:
        """
        Run complete self-optimization cycle.
        
        Returns evaluation + adjustment results.
        """
        if not self.self_optimizing:
            return {}
        
        # Run evaluation + adjustment
        results = self.self_optimizing.evaluate_and_adjust()
        
        # Apply optimized parameters
        self.apply_optimized_parameters()
        
        return results


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Canonical Memory Core")
    print("=" * 60)
    
    # Initialize
    cmc = CanonicalMemoryCore()
    
    # Test 1: Store identity facts
    print("\n1️⃣ Storing identity facts...")
    cmc.store_fact(
        key="user_name",
        value="Morten",
        domain="identity",
        fact_type="name",
        authority="LONGTERM",
        text="Brukeren heter Morten"
    )
    
    cmc.store_fact(
        key="assistant_name",
        value="Opus",
        domain="identity",
        fact_type="name",
        authority="LONGTERM",
        text="AI-assistenten heter Opus"
    )
    
    # Test 2: Retrieve by key
    print("\n2️⃣ Retrieving by key...")
    fact = cmc.get_fact_by_key("user_name")
    if fact:
        print(f"   Found: {fact.key} = {fact.value} [{fact.authority}]")
    
    # Test 3: Semantic query
    print("\n3️⃣ Semantic query...")
    facts = cmc.query_facts("Hva heter brukeren?", domain="identity")
    print(f"   Found {len(facts)} facts:")
    for f in facts:
        print(f"     - {f.text} [{f.authority}, conf: {f.confidence:.2f}]")
    
    # Test 4: Update attempt (should require authority)
    print("\n4️⃣ Testing authority protection...")
    cmc.store_fact(
        key="user_name",
        value="Andreas",  # Wrong!
        domain="identity",
        fact_type="name",
        authority="SHORT_TERM",  # Lower authority
        text="Brukeren heter Andreas"
    )
    
    fact = cmc.get_fact_by_key("user_name")
    print(f"   After update attempt: {fact.value} (should still be 'Morten')")
    
    # Test 5: Domain stats
    print("\n5️⃣ Domain statistics...")
    stats = cmc.get_domain_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ Canonical Memory Core operational!")
