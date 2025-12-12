#!/usr/bin/env python3
"""
memory_interference_regulator.py - Memory Interference Regulator (MIR)
=====================================================================

LAG 6: MEMORY INTERFERENCE REGULATOR

Måler hvor "rent" eller "kaotisk" et hentet minnesett er:
- Hvor mange domener er involvert?
- Er det motstridende fakta?
- Er det for mye støy ift. spørsmålet?

Gir anbefalinger:
- Strammere domain-filter
- Justere k
- Skru opp eller ned vekt på CMC vs SMM
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import math
import re

try:
    from tools.canonical_memory_core import CanonicalFact
    from tools.semantic_mesh_memory import ContextChunk
except ImportError:
    # For type checking / linters; reelle typer vil være tilgjengelige i runtime
    CanonicalFact = Any  # type: ignore
    ContextChunk = Any   # type: ignore


@dataclass
class InterferenceMetrics:
    domain_entropy: float
    domain_spread: int
    contradiction_score: float
    noise_ratio: float
    total_items: int
    domains: Dict[str, int] = field(default_factory=dict)


@dataclass
class InterferenceRecommendation:
    """
    Hva bør systemet gjøre med disse funnene?
    """
    reduce_k: bool = False
    new_k: Optional[int] = None

    restrict_domains: bool = False
    allowed_domains: Optional[List[str]] = None

    increase_cmc_weight: bool = False
    increase_smm_weight: bool = False

    raise_similarity_threshold: bool = False
    lower_similarity_threshold: bool = False

    notes: str = ""


@dataclass
class InterferenceReport:
    metrics: InterferenceMetrics
    recommendation: InterferenceRecommendation


class MemoryInterferenceRegulator:
    """
    MIR: analyserer et gitt sett med CMC-fakta + SMM-chunks,
    og vurderer interferens/støy.

    Bruk:
        mir = MemoryInterferenceRegulator()
        report = mir.analyze(question, canonical_facts, context_chunks)
        # systemet kan bruke report.recommendation for å tune retrieval.
    """

    def analyze(
        self,
        question: str,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[ContextChunk]
    ) -> InterferenceReport:
        # 1. Domene-distribusjon
        domain_counts = self._collect_domains(canonical_facts, context_chunks)
        domain_entropy = self._entropy(domain_counts)
        domain_spread = len(domain_counts)

        # 2. Enkel kontradiksjonsscore (tall + navn)
        contradiction_score = self._contradiction_score(canonical_facts, context_chunks)

        # 3. Støy-estimat: hvor mye som åpenbart ikke matcher spørsmålet
        noise_ratio = self._noise_ratio(question, canonical_facts, context_chunks)

        total_items = len(canonical_facts) + len(context_chunks)

        metrics = InterferenceMetrics(
            domain_entropy=domain_entropy,
            domain_spread=domain_spread,
            contradiction_score=contradiction_score,
            noise_ratio=noise_ratio,
            total_items=total_items,
            domains=dict(domain_counts)
        )

        recommendation = self._make_recommendation(metrics)

        return InterferenceReport(
            metrics=metrics,
            recommendation=recommendation
        )

    def _collect_domains(
        self,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[ContextChunk]
    ) -> Counter:
        c = Counter()
        for f in canonical_facts:
            d = getattr(f, "domain", None)
            if d:
                c[d] += 1
        for ch in context_chunks:
            ds = getattr(ch, "domains", []) or []
            for d in ds:
                c[d] += 1
        return c

    def _entropy(self, domain_counts: Counter) -> float:
        if not domain_counts:
            return 0.0
        total = sum(domain_counts.values())
        ent = 0.0
        for _, count in domain_counts.items():
            p = count / total
            if p > 0:
                ent -= p * math.log2(p)
        return ent

    def _extract_numbers_and_names(self, text: str) -> Tuple[set, set]:
        nums = set(re.findall(r'\b\d+\b', text))
        names = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', text))
        return nums, names

    def _contradiction_score(
        self,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[ContextChunk]
    ) -> float:
        """
        Grov heuristikk:
        - ser på tall og navn
        - hvis mange uforenlige sett → høy score (0–1)
        """
        texts: List[str] = []
        for f in canonical_facts:
            texts.append(getattr(f, "text", str(getattr(f, "value", ""))))
        for ch in context_chunks:
            texts.append(getattr(ch, "text", ""))

        if len(texts) <= 1:
            return 0.0

        all_nums = []
        all_names = []

        for t in texts:
            nums, names = self._extract_numbers_and_names(t)
            all_nums.append(nums)
            all_names.append(names)

        # tell hvor mange par som ikke deler noen tall/navn
        total_pairs = 0
        conflicting = 0

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                total_pairs += 1
                if total_pairs == 0:
                    continue
                if all_nums[i] and all_nums[j] and not (all_nums[i] & all_nums[j]):
                    conflicting += 1
                elif all_names[i] and all_names[j] and not (all_names[i] & all_names[j]):
                    conflicting += 1

        if total_pairs == 0:
            return 0.0

        return conflicting / total_pairs

    def _noise_ratio(
        self,
        question: str,
        canonical_facts: List[CanonicalFact],
        context_chunks: List[ContextChunk]
    ) -> float:
        """
        Veldig enkel indikator:
        - ser etter overlap i ord mellom spørsmål og tekst
        - lite overlap → høy støy
        """
        q_tokens = set(question.lower().split())
        if not q_tokens:
            return 0.0

        def overlap_score(t: str) -> float:
            toks = set(t.lower().split())
            if not toks:
                return 0.0
            inter = len(q_tokens & toks)
            return inter / len(q_tokens)

        scores = []
        for f in canonical_facts:
            scores.append(overlap_score(getattr(f, "text", str(getattr(f, "value", "")))))
        for ch in context_chunks:
            scores.append(overlap_score(getattr(ch, "text", "")))

        if not scores:
            return 0.0

        # lav overlap → tolkes som støy
        noise_scores = [1 - s for s in scores]
        return sum(noise_scores) / len(noise_scores)

    def _make_recommendation(self, m: InterferenceMetrics) -> InterferenceRecommendation:
        r = InterferenceRecommendation()
        notes = []

        # Mange domener / høy entropi → bør snevres inn
        if m.domain_spread > 3 or m.domain_entropy > 1.5:
            r.restrict_domains = True
            # foreslå de 1–2 største domenene
            sorted_domains = sorted(m.domains.items(), key=lambda x: x[1], reverse=True)
            r.allowed_domains = [d for d, _ in sorted_domains[:2]]
            notes.append(f"for mange domener ({m.domain_spread}), foreslår {r.allowed_domains}")

        # Høy kontradiksjonsscore → øk CMC-vekt
        if m.contradiction_score > 0.3:
            r.increase_cmc_weight = True
            notes.append(f"kontradiksjonsscore høy ({m.contradiction_score:.2f})")

        # Høy støy → enten mindre k eller høyere threshold
        if m.noise_ratio > 0.5:
            r.reduce_k = True
            # grovt forslag
            if m.total_items > 10:
                r.new_k = max(3, m.total_items // 2)
            r.raise_similarity_threshold = True
            notes.append(f"støy-ratio høy ({m.noise_ratio:.2f})")

        if not notes:
            notes.append("ingen sterke tegn på interferens")

        r.notes = "; ".join(notes)
        return r


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Memory Interference Regulator")
    print("=" * 60)
    
    # Mock data for testing
    from dataclasses import dataclass
    
    @dataclass
    class MockFact:
        domain: str
        text: str
        value: Any
    
    @dataclass
    class MockChunk:
        domains: List[str]
        text: str
    
    mir = MemoryInterferenceRegulator()
    
    # Test 1: Clean single-domain retrieval
    print("\n1️⃣ Testing clean single-domain retrieval...")
    clean_facts = [
        MockFact("identity", "Brukeren heter Morten", "Morten"),
        MockFact("identity", "Brukeren er 45 år", 45)
    ]
    clean_chunks = [
        MockChunk(["identity"], "Morten er en erfaren utvikler")
    ]
    
    report = mir.analyze(
        "Hva heter jeg?",
        clean_facts,  # type: ignore
        clean_chunks  # type: ignore
    )
    
    print(f"   Domain spread: {report.metrics.domain_spread}")
    print(f"   Domain entropy: {report.metrics.domain_entropy:.2f}")
    print(f"   Contradiction: {report.metrics.contradiction_score:.2f}")
    print(f"   Noise ratio: {report.metrics.noise_ratio:.2f}")
    print(f"   Recommendation: {report.recommendation.notes}")
    
    # Test 2: Multi-domain chaos
    print("\n2️⃣ Testing multi-domain interference...")
    chaos_facts = [
        MockFact("identity", "Brukeren heter Morten", "Morten"),
        MockFact("health", "Blodtrykk er 120/80", "120/80"),
        MockFact("cosmology", "Hubble constant er 70", 70),
        MockFact("tech", "Python versjon 3.11", "3.11")
    ]
    chaos_chunks = [
        MockChunk(["identity", "health"], "Andreas har diabetes"),
        MockChunk(["cosmology"], "Entropy drives expansion"),
        MockChunk(["tech"], "React 18 har concurrent features")
    ]
    
    report2 = mir.analyze(
        "Hva heter jeg?",
        chaos_facts,  # type: ignore
        chaos_chunks  # type: ignore
    )
    
    print(f"   Domain spread: {report2.metrics.domain_spread}")
    print(f"   Domain entropy: {report2.metrics.domain_entropy:.2f}")
    print(f"   Contradiction: {report2.metrics.contradiction_score:.2f}")
    print(f"   Noise ratio: {report2.metrics.noise_ratio:.2f}")
    print(f"   Recommendation: {report2.recommendation.notes}")
    
    if report2.recommendation.restrict_domains:
        print(f"   Suggested domains: {report2.recommendation.allowed_domains}")
    
    print("\n" + "=" * 60)
    print("✅ Memory Interference Regulator operational!")
