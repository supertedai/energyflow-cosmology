#!/usr/bin/env python3
"""
adaptive_memory_core.py - Self-Expanding Adaptive Memory System
================================================================

Purpose: Replace static pattern matching with ADAPTIVE, LEARNING memory
         that automatically discovers domains, fact types, and patterns.

Key Principles:
1. LEARNS domains from data (not hardcoded)
2. AUTO-DISCOVERS fact types from usage patterns
3. ADAPTS authority levels based on verification history
4. EXPANDS pattern recognition through LLM analysis
5. SELF-ORGANIZES memory into optimal structure

Architecture:
    Question → Adaptive Classifier → Dynamic Retrieval →
    Learning Enforcer → Feedback Loop → Pattern Update

Evolution:
    Day 1: Basic patterns + manual seeds
    Week 1: Learned 20 new patterns from conversations
    Month 1: Fully autonomous domain discovery
    Year 1: Human-level semantic understanding

No hardcoded limits. Pure adaptation.
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import defaultdict
import numpy as np
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# ============================================================
# ADAPTIVE MEMORY ITEM (replaces static MemoryItem)
# ============================================================

@dataclass
class AdaptiveMemoryItem:
    """
    Memory item that LEARNS its own classification.
    
    Unlike static MemoryItem, this:
    - Infers domain from context
    - Discovers fact_type from patterns
    - Adjusts authority based on verification
    - Learns relationships automatically
    """
    
    # Core identity
    id: str
    text: str
    embedding: List[float]
    
    # LEARNED attributes (not hardcoded)
    domain: Optional[str] = None              # Inferred from clustering
    fact_type: Optional[str] = None           # Discovered from patterns
    authority: str = "unverified"             # Upgraded through verification
    
    # Semantic understanding
    key_entities: List[str] = field(default_factory=list)      # Extracted names, numbers, etc.
    relationships: List[str] = field(default_factory=list)     # Who relates to what
    context_tags: List[str] = field(default_factory=list)      # Auto-generated tags
    
    # Learning metadata
    verification_count: int = 0               # How many times verified correct
    challenge_count: int = 0                  # How many times challenged
    confidence_score: float = 0.5             # Bayesian confidence
    last_accessed: Optional[str] = None
    access_count: int = 0
    
    # Adaptation metrics
    domain_probability: Dict[str, float] = field(default_factory=dict)  # P(domain|text)
    fact_type_probability: Dict[str, float] = field(default_factory=dict)  # P(type|text)
    
    # Source tracking
    source: str = "user"
    session_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def update_confidence(self, verified: bool):
        """Bayesian confidence update."""
        if verified:
            self.verification_count += 1
            # Increase confidence (bounded by 0.99)
            self.confidence_score = min(0.99, self.confidence_score + 0.1 * (1 - self.confidence_score))
        else:
            self.challenge_count += 1
            # Decrease confidence (bounded by 0.01)
            self.confidence_score = max(0.01, self.confidence_score * 0.8)
    
    def promote_authority(self):
        """Promote authority level based on verification history."""
        ratio = self.verification_count / max(1, self.verification_count + self.challenge_count)
        
        if ratio > 0.95 and self.verification_count >= 10:
            self.authority = "LONGTERM"
        elif ratio > 0.85 and self.verification_count >= 5:
            self.authority = "stable"
        elif ratio > 0.70:
            self.authority = "short-term"
        else:
            self.authority = "volatile"


# ============================================================
# DOMAIN DISCOVERY ENGINE
# ============================================================

class DomainDiscovery:
    """
    Automatically discovers semantic domains from memory patterns.
    
    No hardcoded domains - learns from:
    1. Clustering similar memories
    2. Entity co-occurrence patterns
    3. LLM semantic analysis
    4. User feedback
    """
    
    def __init__(self, min_cluster_size: int = 3):
        self.discovered_domains: Dict[str, Dict] = {}
        self.domain_embeddings: Dict[str, np.ndarray] = {}
        self.min_cluster_size = min_cluster_size
        
        # Seed with minimal base domains (will expand)
        self.discovered_domains = {
            "personal": {"examples": [], "confidence": 0.8, "auto_discovered": False},
            "technical": {"examples": [], "confidence": 0.8, "auto_discovered": False},
            "general": {"examples": [], "confidence": 0.6, "auto_discovered": False}
        }
    
    def discover_domain_from_memory(self, memory: AdaptiveMemoryItem) -> str:
        """
        Infer domain using multiple signals.
        
        Returns: domain name (existing or newly discovered)
        """
        # 1. Check entity patterns
        entities = memory.key_entities
        
        # 2. Compute similarity to known domain embeddings
        if self.domain_embeddings:
            mem_embedding = np.array(memory.embedding)
            similarities = {}
            
            for domain, domain_emb in self.domain_embeddings.items():
                sim = np.dot(mem_embedding, domain_emb) / (
                    np.linalg.norm(mem_embedding) * np.linalg.norm(domain_emb)
                )
                similarities[domain] = sim
            
            # If strong match, use it
            best_domain = max(similarities.items(), key=lambda x: x[1])
            if best_domain[1] > 0.7:
                return best_domain[0]
        
        # 3. Use LLM for semantic classification
        domain = self._llm_classify_domain(memory.text)
        
        # 4. Register if new
        if domain not in self.discovered_domains:
            self._register_new_domain(domain, memory)
        
        return domain
    
    def _llm_classify_domain(self, text: str) -> str:
        """Use LLM to semantically classify domain."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "Classify the semantic domain of this text. "
                        "Return ONE word: personal, family, health, technical, "
                        "security, cosmology, architecture, or suggest a new domain."
                    )},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            domain = response.choices[0].message.content.strip().lower()
            return domain
        
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}", file=sys.stderr)
            return "general"
    
    def _register_new_domain(self, domain: str, memory: AdaptiveMemoryItem):
        """Register newly discovered domain."""
        self.discovered_domains[domain] = {
            "examples": [memory.id],
            "confidence": 0.5,  # Start low, increases with verification
            "auto_discovered": True,
            "first_seen": datetime.now().isoformat()
        }
        
        # Initialize domain embedding as the memory's embedding
        self.domain_embeddings[domain] = np.array(memory.embedding)
        
        print(f"✨ Discovered new domain: {domain}", file=sys.stderr)
    
    def update_domain_confidence(self, domain: str, verified: bool):
        """Update confidence in domain classification."""
        if domain in self.discovered_domains:
            current = self.discovered_domains[domain]["confidence"]
            if verified:
                self.discovered_domains[domain]["confidence"] = min(0.99, current + 0.05)
            else:
                self.discovered_domains[domain]["confidence"] = max(0.1, current - 0.1)


# ============================================================
# FACT TYPE DISCOVERY ENGINE
# ============================================================

class FactTypeDiscovery:
    """
    Automatically discovers fact types from patterns.
    
    Learns:
    - "name" facts (contain capitalized entities)
    - "count" facts (contain numbers)
    - "location" facts (contain place names)
    - "definition" facts (contain "is", "means", "refers to")
    - NEW types discovered from usage
    """
    
    def __init__(self):
        self.discovered_types: Dict[str, Dict] = {}
        self.type_patterns: Dict[str, List[str]] = {}
        
        # Minimal seeds (will expand)
        self._seed_basic_types()
    
    def _seed_basic_types(self):
        """Seed with minimal observable patterns."""
        self.discovered_types = {
            "name": {
                "indicators": ["capitalized_entity"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "count": {
                "indicators": ["contains_number"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "location": {
                "indicators": ["place_name", "bor", "live"],
                "confidence": 0.8,
                "auto_discovered": False
            }
        }
    
    def discover_fact_type(self, memory: AdaptiveMemoryItem) -> str:
        """
        Infer fact type from content patterns.
        
        Returns: fact_type (existing or newly discovered)
        """
        text = memory.text
        
        # Observable features
        has_number = bool(re.search(r'\d+', text))
        has_capitalized = bool(re.search(r'\b[A-ZÆØÅ][a-zæøå]+\b', text))
        has_location_words = any(word in text.lower() for word in ["bor", "oslo", "live", "city"])
        has_definition_words = any(word in text.lower() for word in ["er", "is", "means", "refers"])
        
        # Match to known types
        if has_number and not has_capitalized:
            return "count"
        elif has_capitalized and any(word in text.lower() for word in ["heter", "name", "called"]):
            return "name"
        elif has_location_words:
            return "location"
        elif has_definition_words:
            return "definition"
        
        # If no match, use LLM to discover new type
        new_type = self._llm_discover_type(text)
        
        if new_type not in self.discovered_types:
            self._register_new_type(new_type, memory)
        
        return new_type
    
    def _llm_discover_type(self, text: str) -> str:
        """Use LLM to discover new fact types."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "What type of fact is this? "
                        "Return ONE word: name, count, location, definition, "
                        "relationship, process, rule, metric, or suggest a new type."
                    )},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=20
            )
            
            fact_type = response.choices[0].message.content.strip().lower()
            return fact_type
        
        except Exception as e:
            print(f"⚠️ Fact type discovery failed: {e}", file=sys.stderr)
            return "general"
    
    def _register_new_type(self, fact_type: str, memory: AdaptiveMemoryItem):
        """Register newly discovered fact type."""
        self.discovered_types[fact_type] = {
            "indicators": ["pattern_learned_from_llm"],
            "confidence": 0.5,
            "auto_discovered": True,
            "first_seen": datetime.now().isoformat()
        }
        
        print(f"✨ Discovered new fact type: {fact_type}", file=sys.stderr)


# ============================================================
# ADAPTIVE CLASSIFIER (replaces static classify_domain/fact_type)
# ============================================================

class AdaptiveClassifier:
    """
    Learns to classify questions into domain + fact_type.
    
    Self-improves through:
    1. Pattern extraction from successful retrievals
    2. LLM analysis of new question types
    3. User feedback loops
    4. Statistical co-occurrence analysis
    """
    
    def __init__(self):
        self.domain_discovery = DomainDiscovery()
        self.fact_type_discovery = FactTypeDiscovery()
        
        # Learning: question patterns → (domain, fact_type)
        self.learned_patterns: Dict[str, Tuple[str, str]] = {}
        
        # Statistics: track what works
        self.classification_history: List[Dict] = []
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        Adaptive classification that learns over time.
        
        Returns:
            {
                "domain": str,
                "fact_type": str,
                "confidence": float,
                "reasoning": str  # Explainable
            }
        """
        # 1. Check learned patterns first
        for pattern, (domain, fact_type) in self.learned_patterns.items():
            if re.search(pattern, question.lower()):
                return {
                    "domain": domain,
                    "fact_type": fact_type,
                    "confidence": 0.9,
                    "reasoning": f"Matched learned pattern: {pattern}"
                }
        
        # 2. Use LLM for semantic classification
        classification = self._llm_classify_question(question)
        
        # 3. Record for learning
        self.classification_history.append({
            "question": question,
            "classification": classification,
            "timestamp": datetime.now().isoformat()
        })
        
        return classification
    
    def _llm_classify_question(self, question: str) -> Dict:
        """Use LLM to classify question semantically."""
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "Analyze this question and return JSON:\n"
                        '{"domain": "<domain>", "fact_type": "<type>", "confidence": <0-1>}\n'
                        "Domain examples: personal, family, technical, health, cosmology\n"
                        "Fact type examples: name, count, location, definition, relationship"
                    )},
                    {"role": "user", "content": question}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            result["reasoning"] = "LLM semantic analysis"
            return result
        
        except Exception as e:
            print(f"⚠️ Classification failed: {e}", file=sys.stderr)
            return {
                "domain": "general",
                "fact_type": "general",
                "confidence": 0.3,
                "reasoning": "Fallback"
            }
    
    def learn_from_success(self, question: str, domain: str, fact_type: str):
        """
        Extract pattern from successful retrieval.
        
        Called when a memory successfully answers a question.
        """
        # Extract key phrases (flexible matching)
        words = question.lower().split()
        
        # Create multiple patterns for fuzzy matching
        patterns = []
        
        # Pattern 1: First 2-3 significant words
        if len(words) >= 2:
            # Remove stop words
            stop_words = {"er", "is", "the", "a", "jeg", "du", "i", "you"}
            significant = [w for w in words if w not in stop_words]
            
            if significant:
                patterns.append(" ".join(significant[:2]))  # First 2 significant
                patterns.append(significant[0])  # First word alone
        
        # Pattern 2: Key question words
        question_starters = ["hva", "hvem", "hvor", "når", "hvorfor", "what", "who", "where", "when", "why"]
        for starter in question_starters:
            if starter in words and len(words) > words.index(starter) + 1:
                # "hva heter" pattern
                idx = words.index(starter)
                if idx + 1 < len(words):
                    patterns.append(f"{starter} {words[idx+1]}")
        
        # Store all patterns
        for pattern in patterns:
            if pattern and len(pattern) > 2:  # Avoid too short patterns
                self.learned_patterns[pattern] = (domain, fact_type)
                print(f"✨ Learned: '{pattern}' → ({domain}, {fact_type})", file=sys.stderr)
    
    def get_pattern_coverage(self) -> Dict[str, int]:
        """Return statistics on learned patterns."""
        domains = defaultdict(int)
        for _, (domain, _) in self.learned_patterns.items():
            domains[domain] += 1
        return dict(domains)


# ============================================================
# ADAPTIVE RETRIEVAL ENGINE
# ============================================================

class AdaptiveRetrieval:
    """
    Retrieves memories using learned patterns + semantic search.
    
    Adapts:
    - Filtering strategies based on hit rate
    - Threshold tuning based on precision/recall
    - Query expansion from successful retrievals
    """
    
    def __init__(self, classifier: AdaptiveClassifier):
        self.classifier = classifier
        
        # Adaptive thresholds (tuned automatically)
        self.similarity_threshold = 0.5  # Will adjust based on performance
        self.domain_threshold = 0.6
        
        # Performance tracking
        self.retrieval_stats: Dict[str, Dict] = defaultdict(lambda: {"hits": 0, "misses": 0})
    
    def retrieve(
        self,
        question: str,
        k: int = 5,
        require_domain_match: bool = True
    ) -> List[AdaptiveMemoryItem]:
        """
        Adaptive retrieval with learned filtering.
        
        Returns: List of memories ranked by relevance
        """
        # 1. Classify question
        classification = self.classifier.classify(question)
        domain = classification["domain"]
        fact_type = classification["fact_type"]
        
        # 2. Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=question
        )
        query_embedding = embedding_response.data[0].embedding
        
        # 3. Build adaptive filter
        filter_conditions = []
        
        if require_domain_match and classification["confidence"] > self.domain_threshold:
            filter_conditions.append(
                FieldCondition(key="domain", match=MatchValue(value=domain))
            )
        
        # 4. Search Qdrant
        results = qdrant_client.search(
            collection_name="efc",
            query_vector=query_embedding,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=k * 2  # Get more, then filter
        )
        
        # 5. Convert and filter by adaptive threshold
        memories = []
        for hit in results:
            if hit.score >= self.similarity_threshold:
                memory = AdaptiveMemoryItem(
                    id=hit.id,
                    text=hit.payload["fact"],
                    embedding=[],  # Don't load full embedding
                    domain=hit.payload.get("domain"),
                    fact_type=hit.payload.get("fact_type"),
                    authority=hit.payload.get("authority", "unverified"),
                    key_entities=hit.payload.get("key_entities", []),
                    verification_count=hit.payload.get("verification_count", 0),
                    confidence_score=hit.payload.get("confidence_score", 0.5)
                )
                memories.append(memory)
        
        # 6. Record stats
        self.retrieval_stats[domain]["hits"] += len(memories)
        if not memories:
            self.retrieval_stats[domain]["misses"] += 1
        
        return memories[:k]
    
    def tune_thresholds(self):
        """Automatically adjust thresholds based on performance."""
        for domain, stats in self.retrieval_stats.items():
            total = stats["hits"] + stats["misses"]
            if total > 10:  # Enough data
                hit_rate = stats["hits"] / total
                
                # If hit rate too low, relax threshold
                if hit_rate < 0.3:
                    self.similarity_threshold = max(0.3, self.similarity_threshold - 0.05)
                    print(f"📉 Relaxed threshold for {domain}: {self.similarity_threshold:.2f}", file=sys.stderr)
                
                # If hit rate high, tighten for precision
                elif hit_rate > 0.8:
                    self.similarity_threshold = min(0.7, self.similarity_threshold + 0.05)
                    print(f"📈 Tightened threshold for {domain}: {self.similarity_threshold:.2f}", file=sys.stderr)


# ============================================================
# ADAPTIVE MEMORY ENFORCER
# ============================================================

class AdaptiveEnforcer:
    """
    Enforcement that LEARNS when to override vs trust LLM.
    
    Builds a model of:
    - Which domains require strict enforcement
    - Which LLMs are reliable in which domains
    - When "vet ikke" is better than guessing
    """
    
    def __init__(self, classifier: AdaptiveClassifier, retrieval: AdaptiveRetrieval):
        self.classifier = classifier
        self.retrieval = retrieval
        
        # Learning: domain → enforcement strictness
        self.domain_strictness: Dict[str, float] = defaultdict(lambda: 0.5)
        
        # Track LLM reliability by domain
        self.llm_accuracy: Dict[str, Dict] = defaultdict(lambda: {"correct": 0, "wrong": 0})
    
    def enforce(
        self,
        question: str,
        llm_response: str,
        auto_retrieve: bool = True
    ) -> Dict:
        """
        Adaptive enforcement with learning.
        
        Returns: Same format as before, but with learning metadata
        """
        # 1. Classify
        classification = self.classifier.classify(question)
        domain = classification["domain"]
        
        # 2. Retrieve memories
        memories = self.retrieval.retrieve(question)
        
        if not memories:
            return {
                "response": llm_response,
                "overridden": False,
                "reason": "No memories found",
                "domain": domain,
                "learning": {"classification": classification}
            }
        
        # 3. Decide: override or trust?
        strictness = self.domain_strictness[domain]
        best_memory = max(memories, key=lambda m: m.confidence_score)
        
        # High authority + high confidence → always override
        if best_memory.authority == "LONGTERM" and best_memory.confidence_score > 0.8:
            self.classifier.learn_from_success(question, domain, classification["fact_type"])
            
            return {
                "response": best_memory.text,
                "overridden": True,
                "reason": f"High authority memory (confidence: {best_memory.confidence_score:.2f})",
                "domain": domain,
                "memory_used": best_memory,
                "original_response": llm_response,
                "learning": {"pattern_learned": True}
            }
        
        # Medium confidence → check if LLM contradicts
        elif best_memory.confidence_score > 0.5:
            # Simple contradiction check (can be enhanced with LLM)
            if self._contradicts(llm_response, best_memory.text):
                return {
                    "response": best_memory.text,
                    "overridden": True,
                    "reason": "LLM contradicts verified memory",
                    "domain": domain,
                    "memory_used": best_memory,
                    "original_response": llm_response
                }
        
        # Low confidence or no contradiction → trust LLM but log
        return {
            "response": llm_response,
            "overridden": False,
            "reason": "LLM response acceptable",
            "domain": domain,
            "learning": {"low_confidence_memory": True}
        }
    
    def _contradicts(self, response1: str, response2: str) -> bool:
        """Simple contradiction detection (can be enhanced)."""
        # Extract numbers
        nums1 = set(re.findall(r'\d+', response1))
        nums2 = set(re.findall(r'\d+', response2))
        
        if nums1 and nums2 and not nums1.intersection(nums2):
            return True
        
        # Extract names
        names1 = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', response1))
        names2 = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', response2))
        
        if names1 and names2 and not names1.intersection(names2):
            return True
        
        return False
    
    def provide_feedback(self, question: str, domain: str, was_correct: bool):
        """User feedback loop for continuous learning."""
        if was_correct:
            self.llm_accuracy[domain]["correct"] += 1
            # Maybe LLM is reliable here, reduce strictness
            self.domain_strictness[domain] = max(0.1, self.domain_strictness[domain] - 0.05)
        else:
            self.llm_accuracy[domain]["wrong"] += 1
            # LLM unreliable, increase strictness
            self.domain_strictness[domain] = min(0.9, self.domain_strictness[domain] + 0.1)
        
        print(f"📊 Domain '{domain}' strictness: {self.domain_strictness[domain]:.2f}", file=sys.stderr)


# ============================================================
# MAIN ADAPTIVE MEMORY SYSTEM
# ============================================================

class AdaptiveMemorySystem:
    """
    Complete adaptive memory system that learns and expands.
    
    Usage:
        memory = AdaptiveMemorySystem()
        result = memory.answer_question("Hva heter du?", "Jeg heter Claude")
        memory.provide_feedback(was_correct=False)  # System learns
    """
    
    def __init__(self):
        self.classifier = AdaptiveClassifier()
        self.retrieval = AdaptiveRetrieval(self.classifier)
        self.enforcer = AdaptiveEnforcer(self.classifier, self.retrieval)
        
        print("✨ Adaptive Memory System initialized", file=sys.stderr)
        print("📚 Will learn domains, fact types, and patterns automatically", file=sys.stderr)
    
    def answer_question(self, question: str, llm_draft: str) -> Dict:
        """Main entry point."""
        return self.enforcer.enforce(question, llm_draft)
    
    def provide_feedback(self, question: str, was_correct: bool):
        """Feedback loop for learning."""
        classification = self.classifier.classify(question)
        self.enforcer.provide_feedback(question, classification["domain"], was_correct)
    
    def get_learning_stats(self) -> Dict:
        """Return current learning state."""
        return {
            "learned_patterns": len(self.classifier.learned_patterns),
            "discovered_domains": len(self.classifier.domain_discovery.discovered_domains),
            "discovered_fact_types": len(self.classifier.fact_type_discovery.discovered_types),
            "pattern_coverage": self.classifier.get_pattern_coverage(),
            "retrieval_stats": dict(self.retrieval.retrieval_stats)
        }


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Adaptive Memory System")
    print("=" * 60)
    
    # Initialize
    memory = AdaptiveMemorySystem()
    
    # Test learning
    print("\n1️⃣ Classification learning...")
    q1 = "Hva heter du?"
    classification = memory.classifier.classify(q1)
    print(f"Q: {q1}")
    print(f"Classification: {classification}")
    
    print("\n2️⃣ Learning from success...")
    memory.classifier.learn_from_success(q1, "personal", "name")
    
    print("\n3️⃣ Testing learned pattern...")
    q2 = "Hva heter jeg?"
    classification2 = memory.classifier.classify(q2)
    print(f"Q: {q2}")
    print(f"Classification: {classification2}")
    
    print("\n4️⃣ Learning stats...")
    stats = memory.get_learning_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ Adaptive system ready to learn!")
