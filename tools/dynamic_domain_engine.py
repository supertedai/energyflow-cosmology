#!/usr/bin/env python3
"""
dynamic_domain_engine.py - Auto-Detecting Domain Router
=======================================================

LAG 3: DYNAMIC DOMAIN ENGINE (DDE)
Auto-discovers domain switches during conversation

Your cognitive style:
- You DON'T think sequentially
- You DON'T stay in one domain
- You JUMP: security → cosmology → health → intention → tech
- No existing system handles this

This engine:
1. Tracks conversation flow
2. Detects domain switches in real-time
3. Uses MULTIPLE signals (not just LLM)
4. Learns your patterns
5. Predicts next domain before you switch

Multi-signal classification:
    Question → [LLM analysis + Embedding similarity + Learned patterns + Meta-statistics] → Domain

Purpose:
    Zero friction domain hopping
    Matches your parallel thinking
    Learns your cognitive style
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque, defaultdict
import numpy as np
from openai import OpenAI

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class DomainSignal:
    """
    Multi-signal domain classification result.
    
    Combines:
    - LLM semantic analysis
    - Embedding similarity
    - Learned patterns
    - Meta-statistics (conversation flow)
    """
    domain: str
    fact_type: Optional[str]
    confidence: float
    
    # Signal breakdown
    llm_score: float = 0.0
    embedding_score: float = 0.0
    pattern_score: float = 0.0
    meta_score: float = 0.0
    
    # Reasoning
    reasoning: str = ""
    
    # Alternative domains (uncertainty handling)
    alternatives: List[Tuple[str, float]] = field(default_factory=list)


@dataclass
class DomainTransition:
    """Track a domain switch in conversation."""
    from_domain: str
    to_domain: str
    question: str
    timestamp: str
    confidence: float


class DynamicDomainEngine:
    """
    The domain detection engine.
    
    Key capabilities:
    1. Multi-signal classification (LLM + embeddings + patterns + meta)
    2. Learns user's domain hopping patterns
    3. Tracks conversation flow
    4. Predicts next domain
    5. Auto-discovers new domains
    
    This matches your cognitive style:
    - Parallel thinking
    - Cross-domain synthesis
    - Zero friction between fields
    - High-speed context switching
    """
    
    def __init__(self):
        # Domain registry (auto-expanding)
        self.domains: Dict[str, Dict] = self._init_seed_domains()
        
        # Domain embeddings (for similarity)
        self.domain_embeddings: Dict[str, np.ndarray] = {}
        
        # Learned patterns (question → domain)
        self.learned_patterns: Dict[str, Tuple[str, float]] = {}
        
        # Conversation tracking
        self.conversation_history: deque = deque(maxlen=50)
        self.domain_history: deque = deque(maxlen=20)
        
        # Transition tracking (learns your hopping patterns)
        self.transitions: List[DomainTransition] = []
        self.transition_matrix: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # Performance metrics
        self.classification_stats: Dict[str, Dict] = defaultdict(
            lambda: {"correct": 0, "wrong": 0, "confidence_sum": 0.0}
        )
        
        print("✨ Dynamic Domain Engine initialized", file=sys.stderr)
        print("🎯 Multi-signal domain detection active", file=sys.stderr)
    
    def _init_seed_domains(self) -> Dict[str, Dict]:
        """
        Initialize with minimal seed domains.
        
        These will expand automatically through learning.
        """
        return {
            "identity": {
                "description": "Personal identity, names, roles",
                "keywords": ["name", "heter", "who", "jeg", "du", "identity"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "family": {
                "description": "Family relations, children, spouse",
                "keywords": ["barn", "children", "kone", "familie", "family"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "health": {
                "description": "Physical and mental health",
                "keywords": ["helse", "health", "syk", "wellbeing"],
                "confidence": 0.8,
                "auto_discovered": False
            },
            "cosmology": {
                "description": "EFC theory, universe, scales",
                "keywords": ["EFC", "entropi", "cosmology", "universe", "scale"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "symbiose": {
                "description": "Symbiose architecture, AI systems",
                "keywords": ["symbiose", "MCP", "router", "architecture"],
                "confidence": 0.9,
                "auto_discovered": False
            },
            "security": {
                "description": "Safety, privacy, trust",
                "keywords": ["sikkerhet", "security", "privacy", "trust"],
                "confidence": 0.8,
                "auto_discovered": False
            },
            "tech": {
                "description": "Technical implementation, code",
                "keywords": ["python", "code", "API", "technical", "implementation"],
                "confidence": 0.8,
                "auto_discovered": False
            },
            "meta": {
                "description": "Meta-cognition, system design, thinking about thinking",
                "keywords": ["meta", "reflection", "cognitive", "thinking"],
                "confidence": 0.7,
                "auto_discovered": False
            }
        }
    
    def classify(self, question: str, context: Optional[List[str]] = None) -> DomainSignal:
        """
        Multi-signal domain classification.
        
        Uses 4 signals:
        1. LLM semantic analysis (40% weight)
        2. Embedding similarity to known domains (30% weight)
        3. Learned patterns (20% weight)
        4. Meta-statistics from conversation flow (10% weight)
        
        Args:
            question: The question to classify
            context: Recent conversation context
        
        Returns:
            DomainSignal with multi-signal breakdown
        """
        # Signal 1: LLM semantic analysis
        llm_result = self._llm_classify(question)
        
        # Signal 2: Embedding similarity
        embedding_result = self._embedding_classify(question)
        
        # Signal 3: Learned patterns
        pattern_result = self._pattern_classify(question)
        
        # Signal 4: Meta-statistics (conversation flow)
        meta_result = self._meta_classify(context or [])
        
        # Combine signals with weights
        weights = {
            "llm": 0.40,
            "embedding": 0.30,
            "pattern": 0.20,
            "meta": 0.10
        }
        
        # Aggregate domain scores
        domain_scores: Dict[str, float] = defaultdict(float)
        
        if llm_result:
            domain_scores[llm_result[0]] += llm_result[1] * weights["llm"]
        
        if embedding_result:
            for domain, score in embedding_result.items():
                domain_scores[domain] += score * weights["embedding"]
        
        if pattern_result:
            domain_scores[pattern_result[0]] += pattern_result[1] * weights["pattern"]
        
        if meta_result:
            domain_scores[meta_result[0]] += meta_result[1] * weights["meta"]
        
        # Sort by score
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_domains:
            # Fallback
            return DomainSignal(
                domain="general",
                fact_type=None,
                confidence=0.3,
                reasoning="No strong signal detected"
            )
        
        best_domain, best_score = sorted_domains[0]
        alternatives = sorted_domains[1:4]  # Top 3 alternatives
        
        # Build signal
        signal = DomainSignal(
            domain=best_domain,
            fact_type=llm_result[2] if llm_result else None,
            confidence=best_score,
            llm_score=llm_result[1] if llm_result else 0.0,
            embedding_score=embedding_result.get(best_domain, 0.0) if embedding_result else 0.0,
            pattern_score=pattern_result[1] if pattern_result and pattern_result[0] == best_domain else 0.0,
            meta_score=meta_result[1] if meta_result and meta_result[0] == best_domain else 0.0,
            alternatives=alternatives,
            reasoning=self._build_reasoning(llm_result, embedding_result, pattern_result, meta_result)
        )
        
        # Record in history
        self.conversation_history.append(question)
        self.domain_history.append(best_domain)
        
        # Track transition
        if len(self.domain_history) >= 2:
            prev_domain = list(self.domain_history)[-2]
            if prev_domain != best_domain:
                transition = DomainTransition(
                    from_domain=prev_domain,
                    to_domain=best_domain,
                    question=question,
                    timestamp=datetime.now().isoformat(),
                    confidence=best_score
                )
                self.transitions.append(transition)
                self.transition_matrix[(prev_domain, best_domain)] += 1
        
        return signal
    
    def _llm_classify(self, question: str) -> Optional[Tuple[str, float, Optional[str]]]:
        """
        LLM semantic analysis.
        
        Returns: (domain, confidence, fact_type)
        """
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "Classify the semantic domain and fact type of this question.\n"
                        "Return JSON:\n"
                        '{"domain": "<domain>", "fact_type": "<type>", "confidence": <0-1>}\n\n'
                        "Domains: identity, family, health, cosmology, symbiose, security, tech, meta, "
                        "finance, location, creative, operational\n\n"
                        "Fact types: name, count, location, definition, relation, metric, rule, "
                        "config, state, intention, process"
                    )},
                    {"role": "user", "content": question}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return (result["domain"], result["confidence"], result.get("fact_type"))
        
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}", file=sys.stderr)
            return None
    
    def _embedding_classify(self, question: str) -> Optional[Dict[str, float]]:
        """
        Embedding similarity to known domains.
        
        Returns: Dict of domain → similarity scores
        """
        if not self.domain_embeddings:
            # Generate domain embeddings if not exists
            self._init_domain_embeddings()
        
        try:
            # Get question embedding
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=question
            )
            question_embedding = np.array(embedding_response.data[0].embedding)
            
            # Compute similarities
            similarities = {}
            for domain, domain_emb in self.domain_embeddings.items():
                sim = np.dot(question_embedding, domain_emb) / (
                    np.linalg.norm(question_embedding) * np.linalg.norm(domain_emb)
                )
                similarities[domain] = float(sim)
            
            return similarities
        
        except Exception as e:
            print(f"⚠️ Embedding classification failed: {e}", file=sys.stderr)
            return None
    
    def _pattern_classify(self, question: str) -> Optional[Tuple[str, float]]:
        """
        Match against learned patterns.
        
        Returns: (domain, confidence)
        """
        question_lower = question.lower()
        
        # Exact pattern match
        if question_lower in self.learned_patterns:
            return self.learned_patterns[question_lower]
        
        # Fuzzy pattern match (n-grams)
        best_match = None
        best_score = 0.0
        
        for pattern, (domain, confidence) in self.learned_patterns.items():
            if pattern in question_lower or question_lower in pattern:
                # Partial match
                overlap = len(set(pattern.split()) & set(question_lower.split()))
                score = overlap / max(len(pattern.split()), len(question_lower.split()))
                
                if score > best_score and score > 0.5:
                    best_score = score * confidence
                    best_match = (domain, best_score)
        
        return best_match
    
    def _meta_classify(self, context: List[str]) -> Optional[Tuple[str, float]]:
        """
        Meta-statistics from conversation flow.
        
        Predicts domain based on recent history.
        
        Returns: (domain, confidence)
        """
        if len(self.domain_history) < 2:
            return None
        
        # Get most recent domain
        recent = list(self.domain_history)[-1]
        
        # Check transition patterns
        transitions_from_recent = {
            to_domain: count
            for (from_domain, to_domain), count in self.transition_matrix.items()
            if from_domain == recent
        }
        
        if not transitions_from_recent:
            return None
        
        # Most likely next domain
        likely_next = max(transitions_from_recent.items(), key=lambda x: x[1])
        total_transitions = sum(transitions_from_recent.values())
        
        confidence = likely_next[1] / total_transitions
        
        return (likely_next[0], confidence)
    
    def _init_domain_embeddings(self):
        """Generate embeddings for all known domains."""
        for domain, info in self.domains.items():
            text = f"{domain}: {info['description']}. Keywords: {', '.join(info['keywords'])}"
            
            try:
                embedding_response = openai_client.embeddings.create(
                    model="text-embedding-3-large",
                    input=text
                )
                self.domain_embeddings[domain] = np.array(embedding_response.data[0].embedding)
            except Exception as e:
                print(f"⚠️ Failed to generate embedding for domain {domain}: {e}", file=sys.stderr)
    
    def _build_reasoning(
        self,
        llm_result: Optional[Tuple],
        embedding_result: Optional[Dict],
        pattern_result: Optional[Tuple],
        meta_result: Optional[Tuple]
    ) -> str:
        """Build human-readable reasoning for classification."""
        parts = []
        
        if llm_result and llm_result[1] > 0.5:
            parts.append(f"LLM: {llm_result[0]} ({llm_result[1]:.2f})")
        
        if embedding_result:
            top_emb = max(embedding_result.items(), key=lambda x: x[1])
            if top_emb[1] > 0.6:
                parts.append(f"Embedding: {top_emb[0]} ({top_emb[1]:.2f})")
        
        if pattern_result and pattern_result[1] > 0.5:
            parts.append(f"Pattern: {pattern_result[0]} ({pattern_result[1]:.2f})")
        
        if meta_result and meta_result[1] > 0.3:
            parts.append(f"Flow: {meta_result[0]} ({meta_result[1]:.2f})")
        
        return " | ".join(parts) if parts else "Low confidence"
    
    def learn_pattern(self, question: str, domain: str, confidence: float = 0.9):
        """
        Learn a new pattern from successful classification.
        
        Called when user confirms a classification was correct.
        """
        question_lower = question.lower()
        self.learned_patterns[question_lower] = (domain, confidence)
        
        # Also learn n-grams
        words = question_lower.split()
        if len(words) >= 2:
            # 2-grams
            for i in range(len(words) - 1):
                pattern = f"{words[i]} {words[i+1]}"
                if pattern not in self.learned_patterns:
                    self.learned_patterns[pattern] = (domain, confidence * 0.8)
        
        print(f"✨ Learned pattern: '{question_lower}' → {domain}", file=sys.stderr)
    
    def discover_domain(self, domain_name: str, description: str, keywords: List[str]):
        """
        Discover and register a new domain.
        
        This expands the system automatically.
        """
        if domain_name in self.domains:
            return
        
        self.domains[domain_name] = {
            "description": description,
            "keywords": keywords,
            "confidence": 0.5,  # Start low
            "auto_discovered": True,
            "discovered_at": datetime.now().isoformat()
        }
        
        # Generate embedding
        text = f"{domain_name}: {description}. Keywords: {', '.join(keywords)}"
        try:
            embedding_response = openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            self.domain_embeddings[domain_name] = np.array(embedding_response.data[0].embedding)
        except:
            pass
        
        print(f"✨ Discovered new domain: {domain_name}", file=sys.stderr)
    
    def get_transition_patterns(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        Get learned transition patterns.
        
        This shows how user hops between domains.
        """
        patterns = defaultdict(list)
        
        for (from_domain, to_domain), count in self.transition_matrix.items():
            patterns[from_domain].append((to_domain, count))
        
        # Sort by frequency
        for from_domain in patterns:
            patterns[from_domain].sort(key=lambda x: x[1], reverse=True)
        
        return dict(patterns)
    
    def provide_feedback(self, question: str, actual_domain: str):
        """
        User feedback loop.
        
        Learn from corrections.
        """
        # Update stats
        signal = self.classify(question)
        predicted = signal.domain
        
        if predicted == actual_domain:
            self.classification_stats[predicted]["correct"] += 1
        else:
            self.classification_stats[predicted]["wrong"] += 1
            # Learn the correct pattern
            self.learn_pattern(question, actual_domain, confidence=0.95)
        
        self.classification_stats[predicted]["confidence_sum"] += signal.confidence


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Dynamic Domain Engine")
    print("=" * 60)
    
    # Initialize
    dde = DynamicDomainEngine()
    
    # Test 1: Basic classification
    print("\n1️⃣ Basic classification...")
    questions = [
        "Hva heter du?",
        "Hvor mange barn har jeg?",
        "Hva er entropi i EFC?",
        "Hvordan implementere MCP router?",
        "Er dataene mine sikre?"
    ]
    
    for q in questions:
        signal = dde.classify(q)
        print(f"Q: {q}")
        print(f"   → {signal.domain} (conf: {signal.confidence:.2f})")
        print(f"   Signals: LLM={signal.llm_score:.2f}, Emb={signal.embedding_score:.2f}, "
              f"Pat={signal.pattern_score:.2f}, Meta={signal.meta_score:.2f}")
        print(f"   Reasoning: {signal.reasoning}")
        print()
    
    # Test 2: Pattern learning
    print("\n2️⃣ Learning patterns...")
    dde.learn_pattern("Hva heter du?", "identity")
    dde.learn_pattern("Hvor mange barn?", "family")
    
    # Re-test with learned patterns
    signal = dde.classify("Hva heter jeg?")
    print(f"After learning: 'Hva heter jeg?' → {signal.domain} (conf: {signal.confidence:.2f})")
    print(f"   Pattern score: {signal.pattern_score:.2f}")
    
    # Test 3: Transition tracking
    print("\n3️⃣ Transition patterns...")
    patterns = dde.get_transition_patterns()
    print("Learned transitions:")
    for from_domain, transitions in patterns.items():
        print(f"   {from_domain} →")
        for to_domain, count in transitions:
            print(f"      {to_domain}: {count}x")
    
    print("\n" + "=" * 60)
    print("✅ Dynamic Domain Engine operational!")
