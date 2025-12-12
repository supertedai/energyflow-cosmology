#!/usr/bin/env python3
"""
Domene-agnostisk auto-helse og sync-loop
========================================

Dette laget gir:
- LLM-basert domene-agnostisk ekstraksjon av fakta/relasjoner fra rå tekst.
- Periodisk synkronisering mot CMC, SMM og Neo4j uten manuell wiring per domene.
- Helse-rapport som viser dekning, nye/manglende domener og konsistensdrift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
import threading

try:
    from tools.canonical_memory_core import CanonicalMemoryCore, CanonicalFact
    from tools.semantic_mesh_memory import SemanticMeshMemory
except ImportError:
    CanonicalMemoryCore = Any  # type: ignore
    CanonicalFact = Any  # type: ignore
    SemanticMeshMemory = Any  # type: ignore

try:
    from tools.neo4j_graph_layer import Neo4jGraphLayer
except ImportError:
    Neo4jGraphLayer = Any  # type: ignore


@dataclass
class ExtractedFact:
    key: str
    value: Any
    text: str
    domain: str
    fact_type: str = "statement"
    authority: str = "llm_extractor"
    confidence: float = 0.5
    relations: List[Tuple[str, str, str]] = field(default_factory=list)  # (src_key, rel_type, tgt_key)


class DomainAgnosticExtractor:
    """
    Pakker en LLM/ontologi-funksjon slik at vi kan mate inn rå tekst og få ut fakta + relasjoner.
    llm_fn forventes å returnere en liste av dicts med keys: key, value, domain, fact_type?, confidence?, relations?
    """

    def __init__(self, llm_fn: Callable[[str], List[Dict[str, Any]]]):
        self.llm_fn = llm_fn

    def extract(self, text: str) -> List[ExtractedFact]:
        raw = self.llm_fn(text)
        results: List[ExtractedFact] = []
        for item in raw:
            results.append(
                ExtractedFact(
                    key=item["key"],
                    value=item["value"],
                    text=item.get("text", text),
                    domain=item.get("domain", "unknown"),
                    fact_type=item.get("fact_type", "statement"),
                    authority=item.get("authority", "llm_extractor"),
                    confidence=item.get("confidence", 0.5),
                    relations=[tuple(rel) for rel in item.get("relations", [])],
                )
            )
        return results


@dataclass
class DomainCoverage:
    domain: str
    fact_count: int
    chunk_count: int
    last_seen: Optional[str]
    missing_relations: bool = False
    drift_warning: bool = False


class MemoryHealthMonitor:
    """
    Samler dekning, leter etter nye/manglende domener og markerer drift.
    """

    def __init__(
        self,
        cmc: CanonicalMemoryCore,
        smm: SemanticMeshMemory,
        pattern_learner: Any,
        graph: Optional[Neo4jGraphLayer] = None,
    ):
        self.cmc = cmc
        self.smm = smm
        self.pattern_learner = pattern_learner
        self.graph = graph

    def compute_domain_coverage(self) -> Dict[str, DomainCoverage]:
        stats = self.cmc.get_domain_stats()
        coverage: Dict[str, DomainCoverage] = {}
        for domain, meta in stats.items():
            coverage[domain] = DomainCoverage(
                domain=domain,
                fact_count=meta.get("count", 0),
                chunk_count=self._smm_chunk_count(domain),
                last_seen=meta.get("last_seen"),
                missing_relations=False,
                drift_warning=False,
            )
        # mark missing/misaligned domains seen by learner but not in CMC
        for domain in self.pattern_learner.domains.keys():
            if domain not in coverage:
                coverage[domain] = DomainCoverage(
                    domain=domain,
                    fact_count=0,
                    chunk_count=self._smm_chunk_count(domain),
                    last_seen=None,
                    missing_relations=True,
                    drift_warning=True,
                )
        return coverage

    def _smm_chunk_count(self, domain: str) -> int:
        try:
            return self.smm.count_chunks(domain=domain)  # type: ignore[attr-defined]
        except Exception:
            return 0

    def detect_drift(self) -> List[str]:
        warnings: List[str] = []
        for cdp in self.pattern_learner.get_universal_patterns():
            for domain in self.pattern_learner.domains.keys():
                dl = self.pattern_learner.domains[domain]
                if dl.observations < self.pattern_learner.min_observations_to_learn:
                    continue
                if dl.average_efc_score < 2.5:
                    warnings.append(f"{domain}: drift vs universal pattern '{cdp.pattern}'")
        return warnings

    def generate_report(self) -> Dict[str, Any]:
        coverage = self.compute_domain_coverage()
        drift = self.detect_drift()
        return {
            "timestamp": datetime.now().isoformat(),
            "domains": {d: coverage[d].__dict__ for d in coverage},
            "drift_warnings": drift,
            "universal_patterns": [cdp.pattern for cdp in self.pattern_learner.get_universal_patterns()],
        }

    def sync_report_to_graph(self, report: Dict[str, Any]):
        if not self.graph:
            return
        try:
            with self.graph.driver.session() as session:
                for domain, meta in report["domains"].items():
                    session.run(
                        """
                        MERGE (d:Domain {name: $name})
                        SET d.fact_count = $fact_count,
                            d.chunk_count = $chunk_count,
                            d.last_seen = $last_seen,
                            d.missing_relations = $missing_relations,
                            d.drift_warning = $drift_warning,
                            d.updated_at = datetime()
                        """,
                        name=domain,
                        fact_count=meta["fact_count"],
                        chunk_count=meta["chunk_count"],
                        last_seen=meta["last_seen"],
                        missing_relations=meta["missing_relations"],
                        drift_warning=meta["drift_warning"],
                    )
        except Exception:
            pass


class MemoryAutoSync:
    """
    Periodisk loop som:
    1) Ekstraherer domene-agnostiske fakta.
    2) Upserter til CMC + SMM + Neo4j (symbolsk).
    3) Oppdaterer pattern learner og health report.
    """

    def __init__(
        self,
        extractor: DomainAgnosticExtractor,
        cmc: CanonicalMemoryCore,
        smm: SemanticMeshMemory,
        pattern_learner: Any,
        graph: Optional[Neo4jGraphLayer] = None,
        interval_seconds: int = 900,
    ):
        self.extractor = extractor
        self.cmc = cmc
        self.smm = smm
        self.pattern_learner = pattern_learner
        self.graph = graph
        self.interval_seconds = interval_seconds
        self.monitor = MemoryHealthMonitor(cmc, smm, pattern_learner, graph)
        self._timer: Optional[threading.Timer] = None

    def _upsert_facts(self, facts: Sequence[ExtractedFact]):
        for fact in facts:
            cf = CanonicalFact(
                id=None,
                domain=fact.domain,
                fact_type=fact.fact_type,
                authority=fact.authority,
                key=fact.key,
                value=fact.value,
                text=fact.text,
                confidence=fact.confidence,
                verification_count=0,
                embedding=[],
            )
            self.cmc.upsert_fact(cf)
            self.smm.add_context_chunk(
                text=fact.text,
                domains=[fact.domain],
                meta={"source": fact.authority, "fact_key": fact.key},
            )
            if self.graph:
                self._ground_fact_in_graph(fact)

    def _ground_fact_in_graph(self, fact: ExtractedFact):
        try:
            with self.graph.driver.session() as session:
                session.run(
                    """
                    MERGE (f:Fact {key: $key})
                    SET f.value = $value,
                        f.domain = $domain,
                        f.fact_type = $fact_type,
                        f.authority = $authority,
                        f.confidence = $confidence,
                        f.text = $text,
                        f.updated_at = datetime()
                    """,
                    key=fact.key,
                    value=fact.value,
                    domain=fact.domain,
                    fact_type=fact.fact_type,
                    authority=fact.authority,
                    confidence=fact.confidence,
                    text=fact.text,
                )
                for src, rel, tgt in fact.relations:
                    session.run(
                        """
                        MERGE (s:Entity {key: $src})
                        MERGE (t:Entity {key: $tgt})
                        MERGE (s)-[r:REL {type: $rel}]->(t)
                        SET r.updated_at = datetime()
                        """,
                        src=src,
                        rel=rel,
                        tgt=tgt,
                    )
        except Exception:
            pass

    def run_cycle(self, documents: Iterable[str]):
        for doc in documents:
            extracted = self.extractor.extract(doc)
            self._upsert_facts(extracted)
            # feed back into learner for auto-domain discovery
            for f in extracted:
                self.pattern_learner.learn_from_feedback(
                    question=f.text,
                    domain=f.domain,
                    efc_score=f.confidence * 10,
                    was_helpful=True,
                    current_patterns=[f.key],
                )
        report = self.monitor.generate_report()
        self.monitor.sync_report_to_graph(report)
        return report

    def start_periodic(self, document_source: Callable[[], Iterable[str]]):
        def _tick():
            docs = list(document_source())
            self.run_cycle(docs)
            self._schedule_next()

        self._timer = threading.Timer(self.interval_seconds, _tick)
        self._timer.daemon = True
        self._timer.start()

    def _schedule_next(self):
        if self._timer:
            self._timer = threading.Timer(self.interval_seconds, self._timer.function)  # type: ignore[arg-type]
            self._timer.daemon = True
            self._timer.start()

    def stop(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
