#!/usr/bin/env python3
"""
memory_consistency_auditor.py - Cross-Layer Consistency Auditor (MCA)
=====================================================================

LAG 7: CROSS-LAYER CONSISTENCY AUDITOR

Oppgave:
- Sammenligne CMC-fakta med SMM-kontekst
- Finne mulige motsetninger
- Logge avvik for senere gjennomgang
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import sys

try:
    from tools.canonical_memory_core import CanonicalMemoryCore, CanonicalFact
    from tools.semantic_mesh_memory import SemanticMeshMemory, ContextChunk
except ImportError:
    CanonicalMemoryCore = Any  # type: ignore
    CanonicalFact = Any        # type: ignore
    SemanticMeshMemory = Any   # type: ignore
    ContextChunk = Any         # type: ignore


@dataclass
class ConsistencyIssue:
    fact_id: str
    fact_key: str
    fact_text: str
    chunk_id: str
    chunk_text: str
    issue_type: str
    severity: float
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoryConsistencyAuditor:
    """
    Auditor som kan kjøres periodisk (cron, bakgrunnsjobb).
    """

    def __init__(self):
        self.issues: List[ConsistencyIssue] = []

    def audit_fact_against_chunks(
        self,
        fact: CanonicalFact,
        chunks: List[ContextChunk]
    ):
        """
        Sjekk én CanonicalFact mot et sett med ContextChunks.
        Enkelt fokus: tall og navn.
        """
        fact_text = getattr(fact, "text", str(getattr(fact, "value", "")))
        fact_nums = set(re.findall(r'\b\d+\b', fact_text))
        fact_names = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', fact_text))

        for ch in chunks:
            ch_text = getattr(ch, "text", "")
            ch_nums = set(re.findall(r'\b\d+\b', ch_text))
            ch_names = set(re.findall(r'\b[A-ZÆØÅ][a-zæøå]+\b', ch_text))

            # enkel heuristikk: hvis samme key/domene, men tall/navn ikke matcher → mulig issue
            mismatch = False
            severity = 0.0

            if fact_nums and ch_nums and not (fact_nums & ch_nums):
                mismatch = True
                severity += 0.6
            if fact_names and ch_names and not (fact_names & ch_names):
                mismatch = True
                severity += 0.4

            if mismatch:
                issue = ConsistencyIssue(
                    fact_id=getattr(fact, "id", ""),
                    fact_key=getattr(fact, "key", ""),
                    fact_text=fact_text,
                    chunk_id=getattr(ch, "id", ""),
                    chunk_text=ch_text,
                    issue_type="number/name_mismatch",
                    severity=min(1.0, severity)
                )
                self.issues.append(issue)

    def run_simple_audit(
        self,
        cmc: CanonicalMemoryCore,
        smm: SemanticMeshMemory,
        max_facts: int = 50
    ):
        """
        Enkel audit:
        - hent ut domain-stats fra CMC
        - plukk de mest sentrale facts (naivt: første N du får tak i)
        - søk i SMM på key / domain og sjekk motstrid
        """
        # grovt: hent domain stats og så scroll collection
        domain_stats = cmc.get_domain_stats()
        domains = list(domain_stats.keys())

        # scroll CMC-collection (litt naivt, men ok som utgangspunkt)
        from qdrant_client import QdrantClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        offset = None
        counted = 0

        while counted < max_facts:
            batch, offset = qdrant_client.scroll(
                collection_name=cmc.collection_name,
                limit=20,
                offset=offset
            )

            if not batch:
                break

            for hit in batch:
                if counted >= max_facts:
                    break

                fact = CanonicalFact(
                    id=str(hit.id),
                    domain=hit.payload["domain"],
                    fact_type=hit.payload["fact_type"],
                    authority=hit.payload["authority"],
                    key=hit.payload["key"],
                    value=hit.payload["value"],
                    text=hit.payload["text"],
                    confidence=hit.payload.get("confidence", 0.5),
                    verification_count=hit.payload.get("verification_count", 0),
                    embedding=[]
                )

                # søk relevante chunks i SMM med samme domain
                res = smm.search_context(
                    query=fact.text,
                    domains=[fact.domain],
                    k=10
                )
                chunks = [c for (c, score) in res]

                self.audit_fact_against_chunks(fact, chunks)
                counted += 1

            if offset is None:
                break

    def export_issues(self) -> List[Dict[str, Any]]:
        """For logging til Neo4j, fil eller annet."""
        return [
            {
                "fact_id": issue.fact_id,
                "fact_key": issue.fact_key,
                "fact_text": issue.fact_text,
                "chunk_id": issue.chunk_id,
                "chunk_text": issue.chunk_text,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "detected_at": issue.detected_at
            }
            for issue in self.issues
        ]


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Memory Consistency Auditor")
    print("=" * 60)
    
    # This would need real CMC/SMM instances
    print("\n⚠️  Auditor testing requires live CMC/SMM instances")
    print("   Use audit_run.py script to run full audit")
    
    # Test basic issue detection
    print("\n1️⃣ Testing issue detection logic...")
    
    from dataclasses import dataclass
    
    @dataclass
    class MockFact:
        id: str
        key: str
        domain: str
        text: str
        value: Any
    
    @dataclass
    class MockChunk:
        id: str
        domains: List[str]
        text: str
    
    auditor = MemoryConsistencyAuditor()
    
    # Consistent case
    consistent_fact = MockFact(
        id="fact_1",
        key="user_name",
        domain="identity",
        text="Brukeren heter Morten",
        value="Morten"
    )
    
    consistent_chunk = MockChunk(
        id="chunk_1",
        domains=["identity"],
        text="Morten er en erfaren utvikler"
    )
    
    auditor.audit_fact_against_chunks(
        consistent_fact,  # type: ignore
        [consistent_chunk]  # type: ignore
    )
    
    print(f"   Issues after consistent check: {len(auditor.issues)}")
    
    # Inconsistent case
    inconsistent_chunk = MockChunk(
        id="chunk_2",
        domains=["identity"],
        text="Andreas er 35 år gammel"
    )
    
    auditor.audit_fact_against_chunks(
        consistent_fact,  # type: ignore
        [inconsistent_chunk]  # type: ignore
    )
    
    print(f"   Issues after inconsistent check: {len(auditor.issues)}")
    
    if auditor.issues:
        print("\n   Detected issues:")
        for issue in auditor.issues:
            print(f"      - {issue.issue_type} (severity: {issue.severity:.2f})")
            print(f"        Fact: {issue.fact_text[:50]}...")
            print(f"        Chunk: {issue.chunk_text[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ Memory Consistency Auditor operational!")
    print("💡 Run full audit with: python audit_run.py")
