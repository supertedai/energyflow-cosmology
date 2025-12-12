#!/usr/bin/env python3
"""
priority_gate.py - Priority Gate for Meta-Supervisor
=====================================================

Filters irrelevant memory chunks, facts, and patterns based on intent signal.

PRINSIPP: Intent-driven noise reduction
Ikke alt minne er relevant for enhver intent.
Priority gate filtrerer basert på:
- Active domains (hvilke domener er viktige nå?)
- Priority keys (hvilke nøkkelord er kritiske?)
- Ignore patterns (hva skal ignoreres?)
- Intent strength (hvor sterk er signalet?)

Dette er top-down filtering - intensjon → fokus.

ARKITEKTUR:
1. Domain gating: Filtrer irrelevante domener
2. Key matching: Boost relevante nøkkelord
3. Pattern blocking: Blokkér støy
4. Relevance scoring: Rank chunks basert på intent

INTEGRASJON:
- Intent Engine: Mottar intent signal
- CMC: Filtrerer canonical facts
- SMM: Filtrerer working memory
- Router: Filtrerer retrieval results
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path

# Add tools to path for CLI testing
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from meta_supervisor
from tools.meta_supervisor import IntentSignal, IntentMode


@dataclass
class FilterResult:
    """Result from priority gating"""
    item_id: str
    original_score: float       # Original relevance score
    adjusted_score: float       # After intent-based adjustment
    passed: bool                # Did it pass the gate?
    boost_reason: Optional[str] = None
    block_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "original_score": self.original_score,
            "adjusted_score": self.adjusted_score,
            "passed": self.passed,
            "boost_reason": self.boost_reason,
            "block_reason": self.block_reason
        }


class PriorityGate:
    """
    PRIORITY GATE
    
    Intent-driven filtering of memory, facts, and patterns.
    
    Reduserer støy ved å:
    - Booste domene-relevante chunks
    - Blokkere ignorerte mønstre
    - Ranke basert på nøkkelord-matching
    - Justere basert på intent strength
    
    Dette er top-down kontroll over bottom-up data.
    """
    
    def __init__(
        self,
        boost_factor: float = 0.3,      # Boost for domain/key match
        block_threshold: float = 0.2,    # Min score to pass gate
        decay_factor: float = 0.1        # Penalty for ignored patterns
    ):
        self.boost_factor = boost_factor
        self.block_threshold = block_threshold
        self.decay_factor = decay_factor
        
        self.filter_stats = {
            "total_items": 0,
            "passed": 0,
            "blocked": 0,
            "boosted": 0
        }
    
    def filter_chunks(
        self,
        chunks: List[Dict[str, Any]],
        intent_signal: IntentSignal
    ) -> List[Dict[str, Any]]:
        """
        Filter memory chunks based on intent signal.
        
        Args:
            chunks: List of memory chunks with metadata
            intent_signal: Current intent signal
        
        Returns:
            Filtered and re-ranked chunks
        """
        if not chunks:
            return []
        
        results = []
        
        for chunk in chunks:
            # Extract chunk metadata
            chunk_id = chunk.get("id", "unknown")
            chunk_text = chunk.get("text", "")
            chunk_domain = chunk.get("domain", "general")
            original_score = chunk.get("score", 0.5)
            
            # Apply priority gate
            filter_result = self._score_item(
                item_id=chunk_id,
                text=chunk_text,
                domain=chunk_domain,
                original_score=original_score,
                intent_signal=intent_signal
            )
            
            # Update stats
            self.filter_stats["total_items"] += 1
            if filter_result.passed:
                self.filter_stats["passed"] += 1
                if filter_result.boost_reason:
                    self.filter_stats["boosted"] += 1
                
                # Add adjusted score to chunk
                chunk["adjusted_score"] = filter_result.adjusted_score
                chunk["filter_result"] = filter_result.to_dict()
                results.append(chunk)
            else:
                self.filter_stats["blocked"] += 1
        
        # Sort by adjusted score
        results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        
        return results
    
    def filter_facts(
        self,
        facts: List[Dict[str, Any]],
        intent_signal: IntentSignal
    ) -> List[Dict[str, Any]]:
        """
        Filter canonical facts based on intent signal.
        
        Similar to filter_chunks but for CMC facts.
        """
        if not facts:
            return []
        
        results = []
        
        for fact in facts:
            fact_id = fact.get("id", "unknown")
            fact_text = f"{fact.get('key', '')} = {fact.get('value', '')}"
            fact_domain = fact.get("domain", "general")
            original_score = fact.get("trust_score", 1.0)
            
            filter_result = self._score_item(
                item_id=fact_id,
                text=fact_text,
                domain=fact_domain,
                original_score=original_score,
                intent_signal=intent_signal
            )
            
            if filter_result.passed:
                fact["adjusted_score"] = filter_result.adjusted_score
                fact["filter_result"] = filter_result.to_dict()
                results.append(fact)
        
        results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        
        return results
    
    def _score_item(
        self,
        item_id: str,
        text: str,
        domain: str,
        original_score: float,
        intent_signal: IntentSignal
    ) -> FilterResult:
        """
        Score a single item through priority gate.
        
        Returns FilterResult with adjusted score and pass/block decision.
        """
        adjusted_score = original_score
        boost_reason = None
        block_reason = None
        
        text_lower = text.lower()
        
        # 1. Check ignore patterns (blocking)
        for pattern in intent_signal.ignore_patterns:
            if pattern.lower() in text_lower:
                adjusted_score *= (1.0 - self.decay_factor)
                block_reason = f"Contains ignored pattern: {pattern}"
        
        # 2. Check domain match (boosting)
        if domain in intent_signal.active_domains:
            adjusted_score *= (1.0 + self.boost_factor)
            boost_reason = f"Domain match: {domain}"
        
        # 3. Check priority keys (boosting)
        matched_keys = [
            key for key in intent_signal.priority_keys
            if key.lower() in text_lower
        ]
        if matched_keys:
            key_boost = len(matched_keys) * (self.boost_factor / 2)
            adjusted_score *= (1.0 + key_boost)
            if boost_reason:
                boost_reason += f" + Keys: {matched_keys}"
            else:
                boost_reason = f"Key match: {matched_keys}"
        
        # 4. Apply intent strength
        adjusted_score *= intent_signal.strength
        
        # 5. Determine pass/block
        passed = adjusted_score >= self.block_threshold
        
        # If blocked, set reason
        if not passed and not block_reason:
            block_reason = f"Score {adjusted_score:.2f} below threshold {self.block_threshold}"
        
        return FilterResult(
            item_id=item_id,
            original_score=original_score,
            adjusted_score=adjusted_score,
            passed=passed,
            boost_reason=boost_reason,
            block_reason=block_reason
        )
    
    def get_stats(self) -> Dict:
        """Get priority gate statistics"""
        return {
            **self.filter_stats,
            "pass_rate": (
                self.filter_stats["passed"] / self.filter_stats["total_items"]
                if self.filter_stats["total_items"] > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset filter statistics"""
        self.filter_stats = {
            "total_items": 0,
            "passed": 0,
            "blocked": 0,
            "boosted": 0
        }


# ============================================================
# CLI for testing
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Priority Gate")
    print("=" * 60)
    
    # Create priority gate
    gate = PriorityGate()
    
    # Create test intent signal
    intent = IntentSignal(
        signal_id="test_intent",
        mode=IntentMode.PROTECTION,
        active_domains=["identity"],
        priority_keys=["Morten", "navn"],
        ignore_patterns=["test", "Morpheus"],
        timestamp=datetime.now(),
        strength=0.8
    )
    
    # Test chunks
    test_chunks = [
        {
            "id": "chunk_1",
            "text": "Morten er brukerens navn",
            "domain": "identity",
            "score": 0.9
        },
        {
            "id": "chunk_2",
            "text": "Morpheus er test data",
            "domain": "identity",
            "score": 0.8
        },
        {
            "id": "chunk_3",
            "text": "Energiflyt teori",
            "domain": "efc_theory",
            "score": 0.7
        },
        {
            "id": "chunk_4",
            "text": "Brukerens navn er viktig",
            "domain": "identity",
            "score": 0.6
        }
    ]
    
    print("\n1️⃣ Test: Filter chunks with PROTECTION intent")
    print(f"Intent: {intent.mode.value}")
    print(f"Active domains: {intent.active_domains}")
    print(f"Priority keys: {intent.priority_keys}")
    print(f"Ignore patterns: {intent.ignore_patterns}")
    print()
    
    filtered = gate.filter_chunks(test_chunks, intent)
    
    print(f"Results: {len(filtered)}/{len(test_chunks)} passed")
    for chunk in filtered:
        result = chunk["filter_result"]
        print(f"  ✓ {chunk['id']}: {result['original_score']:.2f} → {result['adjusted_score']:.2f}")
        if result["boost_reason"]:
            print(f"    Boost: {result['boost_reason']}")
    
    print()
    print("2️⃣ Stats:")
    stats = gate.get_stats()
    print(f"  Total: {stats['total_items']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Blocked: {stats['blocked']}")
    print(f"  Boosted: {stats['boosted']}")
    print(f"  Pass rate: {stats['pass_rate']:.1%}")
    
    print("\n✅ Priority Gate test complete")
