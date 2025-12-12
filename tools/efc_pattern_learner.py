#!/usr/bin/env python3
"""
efc_pattern_learner.py - Adaptive EFC Pattern Learning System
=============================================================

ADAPTIVE PATTERN DETECTION LAYER

Dette systemet:
- Lærer nye EFC-mønstre fra suksessfulle deteksjoner
- Oppdager nye domener hvor EFC er relevant
- Justerer terskler dynamisk basert på feedback
- Ekspanderer pattern-biblioteket automatisk

Eksempel:
    Økonomi får score 0.0 i dag, men etter 10 suksessfulle
    markedsanalyser med EFC-terminologi, lærer systemet at
    "likevekt", "marked", "pris" er EFC-relevante patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
import json
import os
from pathlib import Path

# Neo4j integration (optional)
try:
    from neo4j_graph_layer import Neo4jGraphLayer
    NEO4J_AVAILABLE = True
except ImportError:
    try:
        from tools.neo4j_graph_layer import Neo4jGraphLayer
        NEO4J_AVAILABLE = True
    except ImportError:
        Neo4jGraphLayer = Any
        NEO4J_AVAILABLE = False

@dataclass
class PatternObservation:
    """Én observasjon av et pattern i bruk."""
    pattern: str
    domain: str
    question: str
    was_helpful: bool  # Fikk brukeren verdi av EFC-forklaringen?
    efc_score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LearnedPattern:
    """Et pattern systemet har lært."""
    pattern: str
    pattern_type: str  # "language_cue", "logical_pattern", "domain_term"
    domains: Set[str] = field(default_factory=set)
    success_count: int = 0
    total_count: int = 0
    average_score: float = 0.0
    confidence: float = 0.0  # 0-1, hvor trygg er vi på dette patternet?
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DomainLearning:
    """Læring om et spesifikt domene."""
    domain: str
    observations: int = 0
    successful_efc_uses: int = 0
    average_efc_score: float = 0.0
    learned_patterns: List[str] = field(default_factory=list)
    threshold_adjustment: float = 0.0  # ±N poeng justering for dette domenet


@dataclass
class CrossDomainPattern:
    """Et pattern oppdaget på tvers av flere domener."""
    pattern: str
    domains: Set[str] = field(default_factory=set)
    total_occurrences: int = 0
    success_rate: float = 0.0
    is_universal: bool = False  # True hvis sett i ≥3 domener
    confidence: float = 0.0
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EFCPatternLearner:
    """
    Adaptivt læringssystem for EFC pattern detection.
    
    Dette systemet utvider seg selv når nok datapunkter foreligger:
    - Oppdager nye patterns
    - Justerer domene-spesifikke terskler
    - Ekspanderer language cues og logical patterns
    - Lagrer læring persistent
    """
    
    def __init__(
        self,
        learning_file: str = "efc_pattern_learning.json",
        graph: Optional[Any] = None
    ):
        self.learning_file = Path(learning_file)
        self.graph = graph  # Neo4j connection for symbolic grounding
        
        # Learned patterns
        self.patterns: Dict[str, LearnedPattern] = {}
        
        # Domain-specific learning
        self.domains: Dict[str, DomainLearning] = {}
        
        # Cross-domain patterns (universal EFC principles)
        self.cross_domain_patterns: Dict[str, CrossDomainPattern] = {}
        
        # Observations for learning
        self.observations: List[PatternObservation] = []
        
        # Learning parameters
        self.min_observations_to_learn = 5  # Minimum før vi lærer et nytt pattern
        self.confidence_threshold = 0.7  # Minimum confidence for å aktivere pattern
        self.success_rate_threshold = 0.6  # Minimum success rate for å beholde pattern
        self.cross_domain_threshold = 3  # Minimum domains for universal pattern
        
        # Load existing learning
        self.load_learning()
    
    def observe_pattern_use(
        self,
        question: str,
        domain: str,
        detected_patterns: List[str],
        efc_score: float,
        was_helpful: bool
    ):
        """
        Registrer at et pattern ble brukt og om det var nyttig.
        
        Dette er feedback-loopen som lar systemet lære.
        """
        # Record observation
        for pattern in detected_patterns:
            obs = PatternObservation(
                pattern=pattern,
                domain=domain,
                question=question,
                was_helpful=was_helpful,
                efc_score=efc_score
            )
            self.observations.append(obs)
            
            # Update pattern learning
            if pattern not in self.patterns:
                self.patterns[pattern] = LearnedPattern(
                    pattern=pattern,
                    pattern_type=self._infer_pattern_type(pattern)
                )
            
            learned = self.patterns[pattern]
            learned.domains.add(domain)
            learned.total_count += 1
            if was_helpful:
                learned.success_count += 1
            learned.last_seen = datetime.now().isoformat()
            
            # Update running average
            learned.average_score = (
                (learned.average_score * (learned.total_count - 1) + efc_score) 
                / learned.total_count
            )
            
            # Update confidence
            if learned.total_count >= self.min_observations_to_learn:
                learned.confidence = learned.success_count / learned.total_count
        
        # Update domain learning
        if domain not in self.domains:
            self.domains[domain] = DomainLearning(domain=domain)
        
        domain_learning = self.domains[domain]
        domain_learning.observations += 1
        if was_helpful:
            domain_learning.successful_efc_uses += 1
        
        # Update domain average score
        domain_learning.average_efc_score = (
            (domain_learning.average_efc_score * (domain_learning.observations - 1) + efc_score)
            / domain_learning.observations
        )
        
        # Discover cross-domain patterns
        self._discover_cross_domain_patterns()
        
        # Ground new universal patterns in Neo4j
        for cdp in self.get_universal_patterns():
            self.ground_cross_domain_pattern(cdp)
        
        # Collapse similar patterns periodically
        if len(self.observations) % 20 == 0:
            self._collapse_similar_patterns()
        
        # Auto-save periodically
        if len(self.observations) % 10 == 0:
            self.save_learning()
    
    def extract_new_patterns(self, question: str, domain: str) -> List[str]:
        """
        Forsøk å finne nye patterns i et spørsmål.
        
        Dette kjører når EFC var nyttig, men score var lav -
        det betyr at vi trenger nye patterns for dette domenet.
        """
        new_patterns = []
        question_lower = question.lower()
        
        # Extract potential patterns
        words = question_lower.split()
        
        # Bigrams (2-word phrases)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            # Skip common words
            if self._is_meaningful_pattern(bigram):
                new_patterns.append(bigram)
        
        # Key verbs/nouns
        key_words = [
            w for w in words 
            if len(w) > 5 and self._is_meaningful_pattern(w)
        ]
        new_patterns.extend(key_words)
        
        return new_patterns
    
    def get_learned_cues_for_domain(self, domain: str) -> List[str]:
        """
        Hent learned language cues for et spesifikt domene.
        
        Brukes til å utvide LANGUAGE_CUES dynamisk.
        """
        if domain not in self.domains:
            return []
        
        cues = []
        for pattern_name in self.domains[domain].learned_patterns:
            if pattern_name in self.patterns:
                learned = self.patterns[pattern_name]
                if (learned.confidence >= self.confidence_threshold and
                    learned.pattern_type == "language_cue"):
                    cues.append(learned.pattern)
        
        return cues
    
    def get_threshold_adjustment(self, domain: str) -> float:
        """
        Hent threshold-justering for et domene.
        
        Domener med høy success rate får lavere threshold (lettere å aktivere).
        Domener med lav success rate får høyere threshold (vanskeligere å aktivere).
        """
        if domain not in self.domains:
            return 0.0
        
        domain_learning = self.domains[domain]
        
        if domain_learning.observations < self.min_observations_to_learn:
            return 0.0
        
        success_rate = (
            domain_learning.successful_efc_uses / domain_learning.observations
        )
        
        # Beregn justering
        if success_rate >= 0.8:
            # Veldig nyttig - senk threshold med -1.5
            adjustment = -1.5
        elif success_rate >= 0.6:
            # Nyttig - senk threshold med -0.5
            adjustment = -0.5
        elif success_rate <= 0.3:
            # Ikke nyttig - øk threshold med +1.0
            adjustment = +1.0
        else:
            # Middels - ingen justering
            adjustment = 0.0
        
        domain_learning.threshold_adjustment = adjustment
        return adjustment
    
    def learn_from_feedback(
        self,
        question: str,
        domain: str,
        efc_score: float,
        was_helpful: bool,
        current_patterns: List[str]
    ):
        """
        Hoved-læringsfunksjon. Kalles etter at et spørsmål er besvart.
        
        Lærer:
        1. Om eksisterende patterns var nyttige
        2. Om vi trenger nye patterns for dette domenet
        3. Om threshold bør justeres
        """
        # Record observation
        self.observe_pattern_use(
            question=question,
            domain=domain,
            detected_patterns=current_patterns,
            efc_score=efc_score,
            was_helpful=was_helpful
        )
        
        # If EFC was helpful but score was low, try to learn new patterns
        if was_helpful and efc_score < 5.0:
            new_patterns = self.extract_new_patterns(question, domain)
            
            # Add to domain learning
            if domain in self.domains:
                for pattern in new_patterns:
                    if pattern not in self.domains[domain].learned_patterns:
                        self.domains[domain].learned_patterns.append(pattern)
                        
                        # Create learned pattern entry
                        if pattern not in self.patterns:
                            self.patterns[pattern] = LearnedPattern(
                                pattern=pattern,
                                pattern_type="language_cue",
                                domains={domain},
                                success_count=1,
                                total_count=1,
                                average_score=efc_score,
                                confidence=1.0
                            )
    
    def get_active_patterns(self) -> Dict[str, List[str]]:
        """
        Hent alle aktive patterns som har nok confidence.
        
        Returnerer:
        {
            "language_cues": [...],
            "logical_patterns": [...],
            "domain_terms": [...]
        }
        """
        active = {
            "language_cues": [],
            "logical_patterns": [],
            "domain_terms": []
        }
        
        for pattern_name, learned in self.patterns.items():
            if (learned.confidence >= self.confidence_threshold and
                learned.total_count >= self.min_observations_to_learn):
                
                if learned.pattern_type == "language_cue":
                    active["language_cues"].append(learned.pattern)
                elif learned.pattern_type == "logical_pattern":
                    active["logical_patterns"].append(learned.pattern)
                elif learned.pattern_type == "domain_term":
                    active["domain_terms"].append(learned.pattern)
        
        return active
    
    def get_stats(self) -> Dict:
        """Statistikk over læringen."""
        total_patterns = len(self.patterns)
        active_patterns = sum(
            1 for p in self.patterns.values()
            if p.confidence >= self.confidence_threshold
        )
        
        return {
            "total_observations": len(self.observations),
            "total_patterns": total_patterns,
            "active_patterns": active_patterns,
            "domains_learned": len(self.domains),
            "domain_stats": {
                domain: {
                    "observations": dl.observations,
                    "success_rate": (
                        dl.successful_efc_uses / dl.observations 
                        if dl.observations > 0 else 0
                    ),
                    "average_score": dl.average_efc_score,
                    "threshold_adjustment": dl.threshold_adjustment,
                    "learned_patterns": len(dl.learned_patterns)
                }
                for domain, dl in self.domains.items()
            }
        }
    
    # Helper methods
    
    def _infer_pattern_type(self, pattern: str) -> str:
        """Gjett pattern type basert på innhold."""
        if any(op in pattern.lower() for op in ["hvorfor", "hvordan", "hva"]):
            return "logical_pattern"
        elif len(pattern.split()) == 1:
            return "domain_term"
        else:
            return "language_cue"
    
    def _is_meaningful_pattern(self, text: str) -> bool:
        """Sjekk om et pattern er meningsfullt nok til å lære."""
        # Skip very common words
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "er", "i", "og", "på", "av", "til", "med", "en", "et", "som"
        }
        
        if text.lower() in stopwords:
            return False
        
        # Must have some substance
        if len(text) < 4:
            return False
        
        return True
    
    def _discover_cross_domain_patterns(self):
        """Oppdage patterns som gjentar seg på tvers av domener."""
        # Group patterns by their base form
        pattern_domains: Dict[str, Set[str]] = {}
        pattern_stats: Dict[str, Tuple[int, int]] = {}  # (success, total)
        
        for pattern_name, learned in self.patterns.items():
            if learned.confidence < 0.5:  # Only confident patterns
                continue
            
            # Normalize pattern for comparison
            normalized = self._normalize_pattern(pattern_name)
            
            if normalized not in pattern_domains:
                pattern_domains[normalized] = set()
                pattern_stats[normalized] = (0, 0)
            
            pattern_domains[normalized].update(learned.domains)
            
            # Accumulate stats
            success, total = pattern_stats[normalized]
            pattern_stats[normalized] = (
                success + learned.success_count,
                total + learned.total_count
            )
        
        # Identify universal patterns (≥3 domains)
        for pattern, domains in pattern_domains.items():
            if len(domains) >= self.cross_domain_threshold:
                success, total = pattern_stats[pattern]
                success_rate = success / total if total > 0 else 0.0
                
                if pattern not in self.cross_domain_patterns:
                    self.cross_domain_patterns[pattern] = CrossDomainPattern(
                        pattern=pattern,
                        domains=domains,
                        total_occurrences=total,
                        success_rate=success_rate,
                        is_universal=True,
                        confidence=success_rate
                    )
                else:
                    # Update existing
                    cdp = self.cross_domain_patterns[pattern]
                    cdp.domains.update(domains)
                    cdp.total_occurrences = total
                    cdp.success_rate = success_rate
                    cdp.confidence = success_rate
                    cdp.is_universal = len(cdp.domains) >= self.cross_domain_threshold
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Normaliser pattern for sammenligning."""
        # Extract core concept
        pattern_lower = pattern.lower()
        
        # Remove common prefixes/suffixes
        for prefix in ["language cues:", "logical:", "structural:", "matches", "hits"]:
            pattern_lower = pattern_lower.replace(prefix, "").strip()
        
        # Extract key words (length > 5)
        words = [w for w in pattern_lower.split() if len(w) > 5]
        
        if words:
            return " ".join(sorted(words))  # Sort for comparison
        return pattern_lower
    
    def _collapse_similar_patterns(self):
        """Slå sammen overlappende patterns."""
        patterns_to_merge: Dict[str, List[str]] = {}  # normalized -> [original names]
        
        for pattern_name in list(self.patterns.keys()):
            normalized = self._normalize_pattern(pattern_name)
            if normalized not in patterns_to_merge:
                patterns_to_merge[normalized] = []
            patterns_to_merge[normalized].append(pattern_name)
        
        # Merge patterns with same normalized form
        for normalized, originals in patterns_to_merge.items():
            if len(originals) <= 1:
                continue
            
            # Find best representative (highest confidence)
            best = max(originals, key=lambda p: self.patterns[p].confidence)
            best_pattern = self.patterns[best]
            
            # Merge stats from others
            for other_name in originals:
                if other_name == best:
                    continue
                
                other = self.patterns[other_name]
                best_pattern.domains.update(other.domains)
                best_pattern.success_count += other.success_count
                best_pattern.total_count += other.total_count
                best_pattern.average_score = (
                    (best_pattern.average_score * best_pattern.total_count +
                     other.average_score * other.total_count) /
                    (best_pattern.total_count + other.total_count)
                ) if (best_pattern.total_count + other.total_count) > 0 else 0.0
                
                # Remove merged pattern
                del self.patterns[other_name]
            
            # Update confidence
            best_pattern.confidence = (
                best_pattern.success_count / best_pattern.total_count
                if best_pattern.total_count > 0 else 0.0
            )
    
    def get_universal_patterns(self) -> List[CrossDomainPattern]:
        """Hent universelle EFC-patterns (≥3 domener)."""
        return [
            cdp for cdp in self.cross_domain_patterns.values()
            if cdp.is_universal and cdp.confidence >= self.confidence_threshold
        ]
    
    def ground_pattern_in_neo4j(self, pattern_name: str, pattern: LearnedPattern):
        """
        Lagre et learned pattern som node i Neo4j.
        
        Dette gjør EFC-læringen symbolsk søkbar og grafdrevet.
        """
        if not self.graph or not NEO4J_AVAILABLE:
            return
        
        try:
            with self.graph.driver.session() as session:
                # Create EFC_Pattern node
                session.run(
                    """
                    MERGE (p:EFC_Pattern {name: $name})
                    SET p.pattern_type = $pattern_type,
                        p.confidence = $confidence,
                        p.success_count = $success_count,
                        p.total_count = $total_count,
                        p.average_score = $average_score,
                        p.learned_at = $learned_at,
                        p.last_seen = $last_seen
                    """,
                    name=pattern_name,
                    pattern_type=pattern.pattern_type,
                    confidence=pattern.confidence,
                    success_count=pattern.success_count,
                    total_count=pattern.total_count,
                    average_score=pattern.average_score,
                    learned_at=pattern.learned_at,
                    last_seen=pattern.last_seen
                )
                
                # Link to domains
                for domain in pattern.domains:
                    session.run(
                        """
                        MATCH (p:EFC_Pattern {name: $pattern_name})
                        MERGE (d:Domain {name: $domain})
                        MERGE (p)-[:APPLIES_TO]->(d)
                        """,
                        pattern_name=pattern_name,
                        domain=domain
                    )
        except Exception as e:
            # Silent fail - Neo4j is optional
            pass
    
    def ground_cross_domain_pattern(self, cdp: CrossDomainPattern):
        """
        Lagre et universelt pattern i Neo4j.
        
        Dette er viktig fordi det representerer tverrgående EFC-prinsipper.
        """
        if not self.graph or not NEO4J_AVAILABLE:
            return
        
        try:
            with self.graph.driver.session() as session:
                # Create Universal_EFC_Pattern node
                session.run(
                    """
                    MERGE (p:Universal_EFC_Pattern {pattern: $pattern})
                    SET p.total_occurrences = $total_occurrences,
                        p.success_rate = $success_rate,
                        p.confidence = $confidence,
                        p.domain_count = $domain_count,
                        p.discovered_at = $discovered_at
                    """,
                    pattern=cdp.pattern,
                    total_occurrences=cdp.total_occurrences,
                    success_rate=cdp.success_rate,
                    confidence=cdp.confidence,
                    domain_count=len(cdp.domains),
                    discovered_at=cdp.discovered_at
                )
                
                # Link to all domains
                for domain in cdp.domains:
                    session.run(
                        """
                        MATCH (p:Universal_EFC_Pattern {pattern: $pattern})
                        MERGE (d:Domain {name: $domain})
                        MERGE (p)-[:VALIDATED_IN]->(d)
                        """,
                        pattern=cdp.pattern,
                        domain=domain
                    )
        except Exception as e:
            # Silent fail
            pass
    
    # Persistence
    
    def save_learning(self):
        """Lagre learned patterns til fil."""
        data = {
            "patterns": {
                name: {
                    "pattern": p.pattern,
                    "pattern_type": p.pattern_type,
                    "domains": list(p.domains),
                    "success_count": p.success_count,
                    "total_count": p.total_count,
                    "average_score": p.average_score,
                    "confidence": p.confidence,
                    "learned_at": p.learned_at,
                    "last_seen": p.last_seen
                }
                for name, p in self.patterns.items()
            },
            "domains": {
                name: {
                    "domain": d.domain,
                    "observations": d.observations,
                    "successful_efc_uses": d.successful_efc_uses,
                    "average_efc_score": d.average_efc_score,
                    "learned_patterns": d.learned_patterns,
                    "threshold_adjustment": d.threshold_adjustment
                }
                for name, d in self.domains.items()
            },
            "cross_domain_patterns": {
                pattern: {
                    "pattern": cdp.pattern,
                    "domains": list(cdp.domains),
                    "total_occurrences": cdp.total_occurrences,
                    "success_rate": cdp.success_rate,
                    "is_universal": cdp.is_universal,
                    "confidence": cdp.confidence,
                    "discovered_at": cdp.discovered_at
                }
                for pattern, cdp in self.cross_domain_patterns.items()
            }
        }
        
        with open(self.learning_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_learning(self):
        """Last learned patterns fra fil."""
        if not self.learning_file.exists():
            return
        
        try:
            with open(self.learning_file, 'r') as f:
                data = json.load(f)
            
            # Restore patterns
            for name, p_data in data.get("patterns", {}).items():
                self.patterns[name] = LearnedPattern(
                    pattern=p_data["pattern"],
                    pattern_type=p_data["pattern_type"],
                    domains=set(p_data["domains"]),
                    success_count=p_data["success_count"],
                    total_count=p_data["total_count"],
                    average_score=p_data["average_score"],
                    confidence=p_data["confidence"],
                    learned_at=p_data["learned_at"],
                    last_seen=p_data["last_seen"]
                )
            
            # Restore domains
            for name, d_data in data.get("domains", {}).items():
                self.domains[name] = DomainLearning(
                    domain=d_data["domain"],
                    observations=d_data["observations"],
                    successful_efc_uses=d_data["successful_efc_uses"],
                    average_efc_score=d_data["average_efc_score"],
                    learned_patterns=d_data["learned_patterns"],
                    threshold_adjustment=d_data["threshold_adjustment"]
                )
            
            # Restore cross-domain patterns
            for pattern, cdp_data in data.get("cross_domain_patterns", {}).items():
                self.cross_domain_patterns[pattern] = CrossDomainPattern(
                    pattern=cdp_data["pattern"],
                    domains=set(cdp_data["domains"]),
                    total_occurrences=cdp_data["total_occurrences"],
                    success_rate=cdp_data["success_rate"],
                    is_universal=cdp_data["is_universal"],
                    confidence=cdp_data["confidence"],
                    discovered_at=cdp_data["discovered_at"]
                )
        except Exception as e:
            print(f"⚠️  Could not load learning data: {e}")


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧠 Testing EFC Pattern Learner - Adaptive Learning System")
    print("=" * 80)
    
    learner = EFCPatternLearner(learning_file="/tmp/efc_pattern_learning_test.json")
    
    # Simulate learning from observations
    print("\n1️⃣ Simulating observations...\n")
    
    # Economics domain - start with low scores, improve over time
    economics_questions = [
        ("Hvorfor stabiliserer markeder seg rundt likevektspriser?", "finance", ["stabiliserer"], 4.0, True),
        ("Hva driver prisendringer i et marked?", "finance", ["driver"], 3.0, True),
        ("Hvordan oppstår markedsbalanse?", "finance", ["oppstår", "balanse"], 5.0, True),
        ("Hvorfor fluktuerer aksjekurser?", "finance", ["fluktuerer"], 2.0, False),
        ("Hva er likevekt i økonomi?", "finance", ["likevekt"], 4.0, True),
    ]
    
    print("Economics domain observations:")
    for q, domain, patterns, score, helpful in economics_questions:
        learner.learn_from_feedback(q, domain, score, helpful, patterns)
        print(f"  Q: {q[:50]}...")
        print(f"     Score: {score}, Helpful: {helpful}")
    
    # Biology domain - consistently high scores
    biology_questions = [
        ("Hvorfor organiserer celler seg i vevstrukturer?", "biology", ["organiserer", "struktur"], 6.0, True),
        ("Hva driver cellulær differensiering?", "biology", ["driver"], 7.0, True),
        ("Hvordan oppstår emergente biologiske mønstre?", "biology", ["oppstår", "emergente", "mønstre"], 8.0, True),
    ]
    
    print("\nBiology domain observations:")
    for q, domain, patterns, score, helpful in biology_questions:
        learner.learn_from_feedback(q, domain, score, helpful, patterns)
        print(f"  Q: {q[:50]}...")
        print(f"     Score: {score}, Helpful: {helpful}")
    
    # Get stats
    print("\n" + "=" * 80)
    print("2️⃣ Learning Statistics")
    print("=" * 80)
    
    stats = learner.get_stats()
    print(f"\nTotal observations: {stats['total_observations']}")
    print(f"Total patterns learned: {stats['total_patterns']}")
    print(f"Active patterns: {stats['active_patterns']}")
    print(f"Domains learned: {stats['domains_learned']}")
    
    print("\n📊 Domain-specific learning:")
    for domain, domain_stats in stats['domain_stats'].items():
        print(f"\n  {domain.upper()}:")
        print(f"    Observations: {domain_stats['observations']}")
        print(f"    Success rate: {domain_stats['success_rate']:.2%}")
        print(f"    Average score: {domain_stats['average_score']:.1f}")
        print(f"    Threshold adjustment: {domain_stats['threshold_adjustment']:+.1f}")
        print(f"    Learned patterns: {domain_stats['learned_patterns']}")
    
    # Show threshold adjustments
    print("\n" + "=" * 80)
    print("3️⃣ Threshold Adjustments (Adaptive Scoring)")
    print("=" * 80)
    
    for domain in ["finance", "biology", "unknown"]:
        adjustment = learner.get_threshold_adjustment(domain)
        print(f"\n  {domain}:")
        print(f"    Base threshold: 5.0 (EFC_ENABLED)")
        print(f"    Adjustment: {adjustment:+.1f}")
        print(f"    New threshold: {5.0 + adjustment:.1f}")
        
        if adjustment < 0:
            print(f"    → Easier to activate EFC (domain is successful)")
        elif adjustment > 0:
            print(f"    → Harder to activate EFC (domain needs more data)")
        else:
            print(f"    → No adjustment (insufficient data)")
    
    # Show active patterns
    print("\n" + "=" * 80)
    print("4️⃣ Active Learned Patterns")
    print("=" * 80)
    
    active = learner.get_active_patterns()
    for pattern_type, patterns in active.items():
        print(f"\n  {pattern_type}:")
        for p in patterns[:5]:  # Show first 5
            learned = learner.patterns[p]
            print(f"    • '{p}' (confidence: {learned.confidence:.2f}, domains: {', '.join(learned.domains)})")
    
    # Save learning
    learner.save_learning()
    
    print("\n" + "=" * 80)
    print("✅ EFC Pattern Learner operational!")
    print("🧠 System learns from feedback and adapts thresholds")
    print("📈 Domains with high success get lower thresholds")
    print("🔄 New patterns discovered automatically")
    print("💾 Learning persisted to:", learner.learning_file)
    print("=" * 80)
