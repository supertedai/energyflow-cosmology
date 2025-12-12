#!/usr/bin/env python3
"""
Røyk-test av auto-sync/helse-loopen uten eksterne avhengigheter.

Bruker in-memory stubs for CMC/SMM slik at vi kan verifisere flyten:
- LLM-lignende extractor (stub) → MemoryAutoSync
- Upsert til FakeCMC/FakeSMM
- Pattern learner får feedback
- Health-report genereres

Kjør:
    python tools/test_auto_sync_stub.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Iterable
from pathlib import Path
import os
import sys

# Ensure tools imports work when run as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.efc_pattern_learner import EFCPatternLearner
from tools.memory_health_monitor import (
    DomainAgnosticExtractor,
    MemoryAutoSync,
)


# ------------------------------
# In-memory fakes for testing
# ------------------------------

@dataclass
class FakeFact:
    id: str
    domain: str
    fact_type: str
    authority: str
    key: str
    value: Any
    text: str
    confidence: float
    verification_count: int
    embedding: list


class FakeCMC:
    def __init__(self):
        self.facts: Dict[str, FakeFact] = {}
        self.collection_name = "fake_cmc"

    def upsert_fact(self, fact):
        # key-domain acts as unique
        self.facts[(fact.key, fact.domain)] = fact

    def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = {}
        for (_, domain), fact in self.facts.items():
            if domain not in stats:
                stats[domain] = {"count": 0, "last_seen": None}
            stats[domain]["count"] += 1
            stats[domain]["last_seen"] = fact.text
        return stats


class FakeSMM:
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []

    def add_context_chunk(self, text: str, domains: List[str], meta: Dict[str, Any]):
        self.chunks.append({"text": text, "domains": domains, "meta": meta})

    def count_chunks(self, domain: str) -> int:
        return sum(1 for ch in self.chunks if domain in ch.get("domains", []))


# ------------------------------
# Stub extractor / doc source
# ------------------------------

def stub_llm_extractor(text: str) -> List[Dict[str, Any]]:
    """
    Returnerer et minimalt faktsvar slik at vi kan teste flyten.
    """
    return [
        {
            "key": "demo.fact",
            "value": "demo-value",
            "domain": "demo",
            "text": text,
            "confidence": 0.7,
            "relations": [("demo.fact", "RELATES_TO", "demo.value")],
        }
    ]


def stub_document_source() -> Iterable[str]:
    return [
        "Dette er en demo-tekst som bør trigge domene demo.",
        "En annen tekst med samme domene demo.",
    ]


# ------------------------------
# Run smoke test
# ------------------------------

def main():
    # Lagrer læring midlertidig slik at vi ikke roter i hovedfilen
    learning_file = Path("/tmp/efc_pattern_learning_stub.json")
    pattern_learner = EFCPatternLearner(learning_file=str(learning_file))

    auto_sync = MemoryAutoSync(
        extractor=DomainAgnosticExtractor(stub_llm_extractor),
        cmc=FakeCMC(),
        smm=FakeSMM(),
        pattern_learner=pattern_learner,
        graph=None,
        interval_seconds=5,
    )

    report = auto_sync.run_cycle(stub_document_source())

    print("✅ Auto-sync stub-kjøring fullført.")
    print("Health report:")
    print(report)


if __name__ == "__main__":
    main()
