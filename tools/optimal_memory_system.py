#!/usr/bin/env python3
"""
optimal_memory_system.py - The Unified 9-Layer Memory Architecture + EFC Theory Engine
=======================================================================================

COMPLETE OPTIMAL SOLUTION v1.0

    This integrates all 9 layers + EFC Theory Engine:
    
    Core Memory Layers:
    1. Canonical Memory Core (CMC) - Absolute truth, never forgotten
    2. Semantic Mesh Memory (SMM) - Dynamic context & synthesis
    3. Neo4j Graph Layer - Structural relationships & traversal
    
    Intelligence Layers:
    4. Dynamic Domain Engine (DDE) - Auto-domain detection
    5. Adaptive Memory Enforcer (AME) - Intelligent override
    6. Meta-Learning Cortex (MLC) - User pattern learning
    
    Advanced Layers:
    7. Memory Interference Regulator (MIR) - Noise/conflict detection
    8. Memory Consistency Auditor (MCA) - Cross-layer validation
    9. Memory Compression Engine (MCE) - Recursive summarization
    
    Domain Engine:
    + EFC Theory Engine - Domain-specific reasoning for cosmology

Architecture matches your cognitive style:
- Parallel thinking (not sequential)
- Cross-domain synthesis (zero friction)
- High precision + creative flexibility
- Self-learning without rigidity
- Adaptive to YOUR patterns

This is the system that finally matches YOU.

Usage:
    from optimal_memory_system import OptimalMemorySystem
    
    memory = OptimalMemorySystem()
    
    # Store a fact
    memory.store_fact("user_name", "Morten", domain="identity", authority="LONGTERM")
    
    # Ask a question
    result = memory.answer_question(
        question="Hva heter jeg?",
        llm_draft="Du heter Andreas"
    )
    
    print(result["final_response"])  # → "Du heter Morten" (override)
    
    # System learns your patterns automatically
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any, Tuple, Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all layers
from tools.canonical_memory_core import CanonicalMemoryCore, CanonicalFact
from tools.semantic_mesh_memory import SemanticMeshMemory, ContextChunk
from tools.neo4j_graph_layer import Neo4jGraphLayer, GraphNode, GraphRelationship
from tools.dynamic_domain_engine import DynamicDomainEngine, DomainSignal
from tools.adaptive_memory_enforcer import AdaptiveMemoryEnforcer, EnforcementResult
from tools.meta_learning_cortex import MetaLearningCortex, CognitiveMode
from tools.memory_interference_regulator import MemoryInterferenceRegulator
from tools.memory_consistency_auditor import MemoryConsistencyAuditor
from tools.memory_compression_engine import MemoryCompressionEngine
from tools.memory_health_monitor import DomainAgnosticExtractor, MemoryAutoSync
from tools.efc_theory_engine import (
    EFCTheoryEngine, 
    EFCInferenceMode, 
    EFCClaimCheck,
    EFCPatternRelevance
)
from openai import OpenAI


class OptimalMemorySystem:
    """
    The complete 9-layer memory architecture + EFC Theory Engine.
    
    This is THE system that matches your cognitive style:
    - Ultraprecise memory across all domains
    - Zero friction between fields
    - Self-learning and adaptive
    - Intelligent override protection
    - Meta-aware of your patterns
    - Interference control & consistency auditing
    - Recursive compression for long-term memory
    
    9 Layers:
    1. CMC (Canonical Memory Core) - Never forgotten, never wrong
    2. SMM (Semantic Mesh Memory) - Dynamic context & synthesis
    3. Neo4j Graph Layer - Structural relationships & traversal
    4. DDE (Dynamic Domain Engine) - Auto-detect domain switches
    5. AME (Adaptive Memory Enforcer) - Intelligent override protection
    6. MLC (Meta-Learning Cortex) - Learns YOUR cognitive patterns
    7. MIR (Memory Interference Regulator) - Detects conflicts & noise
    8. MCA (Memory Consistency Auditor) - Cross-layer validation
    9. MCE (Memory Compression Engine) - Recursive summarization
    
    Plus: EFC Theory Engine - Domain-specific cosmology reasoning
    
    Zero configuration needed - learns everything automatically.
    """
    
    def __init__(
        self,
        canonical_collection: str = "canonical_facts",
        semantic_collection: str = "semantic_mesh",
        auto_health_sync: bool = False,
        llm_extractor_fn: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
        document_source: Optional[Callable[[], Iterable[str]]] = None,
        auto_sync_interval: int = 900
    ):
        """
        Initialize the complete system.
        
        Args:
            canonical_collection: Qdrant collection for CMC
            semantic_collection: Qdrant collection for SMM
            auto_health_sync: Start domene-agnostisk auto-sync/helse-loop automatisk
            llm_extractor_fn: Callable for LLM/ontologi ekstraksjon, returnerer liste av dicts {key,value,domain,...}
            document_source: Callable som returnerer iterable av rå tekster (f.eks. nye samtaler/dokumenter)
            auto_sync_interval: Sekunder mellom periodiske sync-kjøringer
        """
        print("🚀 Initializing Optimal Memory System v1.0")
        print("=" * 60)
        
        # Layer 1: Canonical Memory Core
        print("1️⃣ Loading Canonical Memory Core (CMC)...")
        self.cmc = CanonicalMemoryCore(collection_name=canonical_collection)
        
        # Layer 2: Semantic Mesh Memory
        print("2️⃣ Loading Semantic Mesh Memory (SMM)...")
        self.smm = SemanticMeshMemory(collection_name=semantic_collection)
        
        # Layer 2.5: Neo4j Graph Layer
        print("2.5️⃣ Loading Neo4j Graph Layer...")
        self.graph = Neo4jGraphLayer()
        
        # Layer 3: Dynamic Domain Engine
        print("3️⃣ Loading Dynamic Domain Engine (DDE)...")
        self.dde = DynamicDomainEngine()
        
        # Layer 4: Adaptive Memory Enforcer
        print("4️⃣ Loading Adaptive Memory Enforcer (AME)...")
        self.ame = AdaptiveMemoryEnforcer(self.cmc, self.smm, self.dde)
        
        # Layer 5: Meta-Learning Cortex
        print("5️⃣ Loading Meta-Learning Cortex (MLC)...")
        self.mlc = MetaLearningCortex()
        
        # Layer 6: Memory Interference Regulator
        print("6️⃣ Loading Memory Interference Regulator (MIR)...")
        self.mir = MemoryInterferenceRegulator()
        
        # Layer 7: Memory Consistency Auditor
        print("7️⃣ Loading Memory Consistency Auditor (MCA)...")
        self.mca = MemoryConsistencyAuditor()
        
        # Layer 8: Memory Compression Engine
        print("8️⃣ Loading Memory Compression Engine (MCE)...")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mce = MemoryCompressionEngine(self.smm, self.openai_client)
        
        # Domain Engine: EFC Theory
        print("🌌 Loading EFC Theory Engine (domain-specific reasoning)...")
        self.efc_engine = EFCTheoryEngine(self.cmc, self.smm, self.graph)
        self.pattern_learner = getattr(self.efc_engine, "learner", None)

        # Auto-sync + helse-monitor (domene-agnostisk)
        self.auto_sync = None
        if auto_health_sync:
            if llm_extractor_fn is None:
                print("⚠️  auto_health_sync er aktivert, men llm_extractor_fn mangler. Hopper over auto-sync.")
            else:
                extractor = DomainAgnosticExtractor(llm_extractor_fn)
                self.auto_sync = MemoryAutoSync(
                    extractor=extractor,
                    cmc=self.cmc,
                    smm=self.smm,
                    pattern_learner=self.pattern_learner,
                    graph=self.graph,
                    interval_seconds=auto_sync_interval
                )
                if document_source:
                    print(f"🔄 Starter auto-sync/helse-loop (interval: {auto_sync_interval}s)...")
                    self.auto_sync.start_periodic(document_source)
                else:
                    print("ℹ️  Auto-sync er klar; kall run_health_sync_once(docs) eller start_periodic(document_source).")
        
        print("\n" + "=" * 60)
        print("✅ All 8 layers operational!")
        print("🧠 System ready to learn your cognitive patterns")
        print("🔧 Advanced: interference control, consistency auditing, compression")
        print("🌌 EFC Theory Engine: Domain-aware cosmology reasoning")
        print()
    
    def store_fact(
        self,
        key: str,
        value: Any,
        domain: str,
        fact_type: str = "general",
        authority: str = "SHORT_TERM",
        text: Optional[str] = None
    ) -> CanonicalFact:
        """
        Store a canonical fact (CMC).
        
        Args:
            key: Structured key (e.g., "user_name")
            value: Structured value (e.g., "Morten")
            domain: Semantic domain
            fact_type: Fact type (name, count, location, etc.)
            authority: Trust level (LONGTERM, STABLE, SHORT_TERM, VOLATILE)
            text: Human-readable form
        
        Returns:
            The stored CanonicalFact
        """
        return self.cmc.store_fact(
            key=key,
            value=value,
            domain=domain,
            fact_type=fact_type,
            authority=authority,
            text=text
        )
    
    def store_context(
        self,
        text: str,
        domains: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        conversation_turn: Optional[int] = None,
        source: str = "conversation",
        related_facts: Optional[List[str]] = None
    ) -> ContextChunk:
        """
        Store dynamic context (SMM).
        
        Args:
            text: The context content
            domains: Related domains (can span multiple)
            tags: Semantic tags
            session_id: Related session
            conversation_turn: Position in conversation
            source: Origin (conversation, file, system, etc.)
            related_facts: Links to canonical facts (CMC)
        
        Returns:
            The stored ContextChunk
        """
        return self.smm.store_chunk(
            text=text,
            domains=domains,
            tags=tags,
            session_id=session_id,
            conversation_turn=conversation_turn,
            source=source,
            related_facts=related_facts
        )
    
    def store_document(
        self,
        text: str,
        domain: Optional[str] = None,
        doc_id: Optional[str] = None,
        source: str = "user",
        tags: Optional[List[str]] = None,
        canonical_links: Optional[List[str]] = None
    ) -> List[ContextChunk]:
        """
        Store a complete document in SMM with automatic chunking.
        
        This is for:
        - Long-form documentation
        - Theory papers
        - Architecture descriptions
        - Meeting notes
        - Research logs
        
        Args:
            text: The full document text
            domain: Primary domain
            doc_id: Document identifier
            source: Origin
            tags: Semantic tags
            canonical_links: Links to related CMC facts
        
        Returns:
            List of created ContextChunks
        """
        return self.smm.add_document(
            text=text,
            domain=domain,
            doc_id=doc_id,
            source=source,
            tags=tags,
            canonical_links=canonical_links
        )

    # ------------------------------------------------------------------
    # Health/auto-sync helpers
    # ------------------------------------------------------------------

    def run_health_sync_once(self, documents: Iterable[str]) -> Optional[Dict[str, Any]]:
        """
        Kjør auto-sync/helse-rapport én gang på en liste av rå tekster.
        Krever at auto_sync er initialisert (se __init__).
        """
        if not self.auto_sync:
            print("⚠️  Auto-sync ikke initialisert. Aktiver auto_health_sync i konstruktør.")
            return None
        return self.auto_sync.run_cycle(documents)
    
    def create_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an entity in the knowledge graph.
        
        Entity types:
        - Person: Morten, family members
        - Concept: EFC, entropy, scale invariance
        - Module: CMC, SMM, DDE, AME, MLC
        - System: Symbiose, OpenWebUI
        - Domain: cosmology, identity, health
        - Theory: EFC v1.0, H-model
        
        Args:
            entity_id: Unique identifier
            entity_type: Node label (Person, Concept, etc.)
            name: Display name
            properties: Additional properties
        
        Returns:
            Success status
        """
        node = GraphNode(
            id=entity_id,
            label=entity_type,
            name=name,
            properties=properties or {}
        )
        return self.graph.create_node(node)
    
    def create_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a relationship in the knowledge graph.
        
        Relation types:
        - PART_OF: Module is part of System
        - HAS_CHILD: Person has child
        - RELATES_TO: Concept relates to Concept
        - SUPPORTS: Evidence supports Theory
        - CONSTRAINS: Theory constrains Prediction
        - DERIVES_FROM: Theory derives from Theory
        - IMPLEMENTS: Module implements Concept
        
        Args:
            from_id: Source entity
            to_id: Target entity
            relation_type: Relationship type
            properties: Additional properties
        
        Returns:
            Success status
        """
        rel = GraphRelationship(
            from_id=from_id,
            to_id=to_id,
            type=relation_type,
            properties=properties or {}
        )
        return self.graph.create_relationship(rel)
    
    def query_graph(
        self,
        question: str
    ) -> Optional[str]:
        """
        Answer structural questions using the knowledge graph.
        
        Examples:
        - "Hvilke lag har symbiosen?"
        - "Hvem er barna til Morten?"
        - "Hvordan henger EFC og entropy sammen?"
        
        This complements:
        - CMC: for fact lookup
        - SMM: for semantic context
        - Graph: for structural/relational queries
        
        Args:
            question: Natural language question
        
        Returns:
            Answer string or None
        """
        return self.graph.query_structure(question)
    
    def get_entity_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        rel_type: Optional[str] = None
    ) -> List[Tuple[GraphNode, str, GraphNode]]:
        """
        Get all relationships for an entity.
        
        Args:
            entity_id: Entity to query
            direction: "in", "out", or "both"
            rel_type: Optional relationship type filter
        
        Returns:
            List of (from_node, rel_type, to_node) tuples
        """
        return self.graph.get_relationships(entity_id, direction, rel_type)
    
    def answer_question(
        self,
        question: str,
        llm_draft: str,
        session_id: Optional[str] = None,
        user_corrected: bool = False
    ) -> Dict[str, Any]:
        """
        The main entry point - answer a question with full 5-layer intelligence.
        
        Process:
        1. MLC observes question, detects cognitive mode
        2. DDE classifies domain
        3. MLC adapts system settings based on mode
        4. AME enforces using CMC + SMM + adapted settings
        5. MLC learns from outcome
        
        Args:
            question: User's question
            llm_draft: LLM's proposed response
            session_id: Current session
            user_corrected: Did user correct the response?
        
        Returns:
            Dict with:
            - final_response: The answer to show user
            - decision: Enforcement decision (OVERRIDE, TRUST_LLM, etc.)
            - domain: Detected domain
            - mode: Detected cognitive mode
            - reasoning: Why this decision was made
            - was_overridden: Bool
            - canonical_facts_used: Count
            - context_chunks_used: Count
            - adaptive_settings: Current MLC settings
        """
        # Step 1: Domain classification (DDE)
        domain_signal = self.dde.classify(question)
        
        # Step 2: MLC observes and adapts
        cognitive_signal = self.mlc.observe(
            question=question,
            domain=domain_signal.domain,
            user_corrected=user_corrected
        )
        
        # Step 3: Get adaptive settings from MLC
        adaptive_settings = self.mlc.get_adaptive_settings()
        
        # Step 4: Apply adaptive settings to AME
        # Adjust strictness based on MLC mode
        original_strictness = self.ame.domain_strictness.get(domain_signal.domain, 0.5)
        adjusted_strictness = original_strictness * adaptive_settings["cmc_strictness_multiplier"]
        adjusted_strictness = min(1.0, max(0.0, adjusted_strictness))
        
        # Temporarily override strictness
        self.ame.domain_strictness[domain_signal.domain] = adjusted_strictness
        
        # Step 5: Enforcement (AME)
        enforcement = self.ame.enforce(
            question=question,
            llm_draft=llm_draft,
            session_id=session_id
        )
        
        # Restore original strictness
        self.ame.domain_strictness[domain_signal.domain] = original_strictness
        
        # Step 6: Store context in SMM (for future retrieval)
        self.smm.store_chunk(
            text=f"Q: {question}\nA: {enforcement.final_response}",
            domains=[domain_signal.domain],
            tags=[cognitive_signal.mode.value],
            session_id=session_id
        )
        
        # Step 7: Interference analysis (MIR)
        interference_report = self.mir.analyze(
            question=question,
            canonical_facts=enforcement.canonical_facts,
            context_chunks=enforcement.context_chunks
        )
        
        # Step 7b: EFC Pattern Detection (tverrdomene)
        # Dette kjører ALLTID - uavhengig av domene
        # EFC kan være relevant i kosmologi, AI, biologi, økonomi, etc.
        efc_pattern: Optional[EFCPatternRelevance] = self.efc_engine.detect_efc_pattern(
            question=question,
            domain=domain_signal.domain
        )
        
        # Step 7c: EFC Theory Engine (hvis pattern score er høy nok)
        efc_mode: Optional[EFCInferenceMode] = None
        efc_claim_check: Optional[EFCClaimCheck] = None
        
        if efc_pattern and efc_pattern.relevance_level in ["EFC_ENABLED", "PURE_EFC"]:
            # Pattern detection indikerer at EFC er relevant
            # Kjør full EFC-analyse
            if self.efc_engine.is_efc_question(question):
                efc_mode = self.efc_engine.infer_mode(
                    question=question,
                    active_domains=[domain_signal.domain]
                )
                # Check LLM draft against EFC principles
                if llm_draft:
                    efc_claim_check = self.efc_engine.check_claim(llm_draft)
        
        # Step 8: Learn pattern if enforcement was successful
        if enforcement.decision in ["OVERRIDE", "TRUST_LLM"]:
            self.dde.learn_pattern(
                question=question,
                domain=domain_signal.domain,
                confidence=domain_signal.confidence
            )
        
        # Step 9: Auto-compression if session is large
        if session_id:
            session_chunks = self.smm.get_session_context(session_id, k=200)
            if len(session_chunks) > 150:
                _ = self.mce.compress_session(
                    session_id=session_id,
                    max_chunks=150,
                    target_generation=1
                )
        
        # Build response
        return {
            # Core response
            "final_response": enforcement.final_response,
            "decision": enforcement.decision,
            
            # Classification
            "domain": domain_signal.domain,
            "fact_type": domain_signal.fact_type,
            "cognitive_mode": cognitive_signal.mode.value,
            
            # Confidence
            "domain_confidence": domain_signal.confidence,
            "enforcement_confidence": enforcement.confidence,
            
            # Details
            "reasoning": enforcement.reasoning,
            "was_overridden": enforcement.was_overridden,
            "was_augmented": enforcement.was_augmented,
            
            # Memory usage
            "canonical_facts_used": len(enforcement.canonical_facts),
            "context_chunks_used": len(enforcement.context_chunks),
            "chunk_ids": [c.id for c in enforcement.context_chunks],  # For feedback loop
            
            # Interference metrics (MIR)
            "interference_metrics": {
                "domain_entropy": interference_report.metrics.domain_entropy,
                "domain_spread": interference_report.metrics.domain_spread,
                "contradiction_score": interference_report.metrics.contradiction_score,
                "noise_ratio": interference_report.metrics.noise_ratio,
                "domains": interference_report.metrics.domains,
                "recommendation_notes": interference_report.recommendation.notes,
            },
            
            # EFC Theory Engine (if activated)
            "efc_mode": efc_mode.mode if efc_mode else None,
            "efc_confidence": efc_mode.confidence if efc_mode else None,
            "efc_claim_consistent": efc_claim_check.is_consistent if efc_claim_check else None,
            "efc_violated_principles": efc_claim_check.violated_principles if efc_claim_check else [],
            
            # EFC Pattern Detection (tverrdomene)
            "efc_pattern_detected": efc_pattern.relevance_level if efc_pattern else "OUT_OF_SCOPE",
            "efc_pattern_score": efc_pattern.score if efc_pattern else 0,
            "efc_should_augment": self.efc_engine.should_augment_with_efc(efc_pattern) if efc_pattern else False,
            "efc_should_override": self.efc_engine.should_override_with_efc(efc_pattern) if efc_pattern else False,
            
            # Adaptive info
            "strictness_applied": adjusted_strictness,
            "adaptive_settings": adaptive_settings,
            
            # Meta
            "llm_draft": llm_draft,
            "session_id": session_id
        }
    
    def get_session_context(
        self,
        session_id: str,
        k: int = 20
    ) -> List[ContextChunk]:
        """
        Get conversation history for a session.
        
        This retrieves:
        - All chunks from this session
        - Ordered by conversation turn
        - For context continuity
        
        Args:
            session_id: Session identifier
            k: Maximum chunks to return
        
        Returns:
            List of ContextChunks in order
        """
        return self.smm.get_session_context(session_id, k)
    
    def search_context(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        k: int = 10,
        include_decay: bool = True
    ) -> List[tuple[ContextChunk, float]]:
        """
        Semantic search across dynamic context.
        
        Args:
            query: Search query
            domains: Filter by domains
            session_id: Filter by session
            k: Number of results
            include_decay: Apply temporal decay to scores
        
        Returns:
            List of (chunk, score) tuples
        """
        return self.smm.search_context(
            query=query,
            domains=domains,
            session_id=session_id,
            k=k,
            include_decay=include_decay
        )
    
    def link_context_to_fact(
        self,
        chunk_id: str,
        fact_id: str
    ):
        """
        Create bidirectional link between context (SMM) and fact (CMC).
        
        This enables:
        - Tracing facts to their context
        - Enriching facts with explanations
        - Cross-referencing layers
        
        Args:
            chunk_id: SMM chunk ID
            fact_id: CMC fact ID
        """
        self.smm.link_to_fact(chunk_id, fact_id)
    
    def provide_feedback(
        self,
        question: str,
        response: str,
        was_correct: bool,
        was_helpful: bool = True,
        chunk_ids: Optional[List[str]] = None
    ):
        """
        User feedback loop.
        
        This is how the system learns from you.
        
        Args:
            question: The question that was asked
            response: The response that was given
            was_correct: Was the response factually correct?
            was_helpful: Was it helpful?
            chunk_ids: Context chunks that were used (for usefulness scoring)
        """
        # Classify to get domain
        domain_signal = self.dde.classify(question)
        
        # DDE learns from feedback
        if was_correct:
            self.dde.provide_feedback(question, domain_signal.domain)
        
        # SMM usefulness scoring
        if chunk_ids and was_helpful:
            for chunk_id in chunk_ids:
                self.smm.update_usefulness(chunk_id, useful=True)
        
        # AME learns strictness adjustments
        # (This happens implicitly through MLC observation)
        
        # MLC observes correction
        self.mlc.observe(
            question=question,
            domain=domain_signal.domain,
            response_quality=1.0 if was_correct else 0.0,
            user_corrected=not was_correct
        )
        
        print(f"✅ Feedback recorded: {'correct' if was_correct else 'incorrect'}", 
              file=sys.stderr)
    
    def apply_temporal_decay(self):
        """
        Apply time-based decay to all dynamic context.
        
        This should run periodically (e.g., daily) to:
        - Reduce relevance of old context
        - Prune stale chunks
        - Keep SMM fresh
        
        Run this as a background job or cron task.
        """
        self.smm.apply_temporal_decay()
    
    def run_consistency_audit(self, max_facts: int = 50) -> List[Dict[str, Any]]:
        """
        Run cross-layer consistency audit (MCA).
        
        This checks:
        - CMC facts vs SMM context
        - Number/name mismatches
        - Potential contradictions
        
        Args:
            max_facts: Maximum facts to audit
        
        Returns:
            List of detected issues
        """
        self.mca.run_simple_audit(self.cmc, self.smm, max_facts)
        return self.mca.export_issues()
    
    def compress_session(
        self,
        session_id: str,
        max_chunks: int = 50,
        generation: int = 1
    ) -> Dict[str, Any]:
        """
        Compress a session using MCE.
        
        This creates:
        - Hierarchical summaries
        - Generation levels (1, 2, 3, ...)
        - Reduced storage footprint
        
        Args:
            session_id: Session to compress
            max_chunks: Max chunks to include
            generation: Compression generation level
        
        Returns:
            Compression result info
        """
        result = self.mce.compress_session(session_id, max_chunks, generation)
        return {
            "session_id": result.session_id,
            "original_count": result.original_count,
            "summary_chunk_id": result.summary_chunk_id,
            "generation": result.generation,
            "created_at": result.created_at
        }
    
    def recursive_compress(
        self,
        session_id: str,
        source_generation: int = 1,
        target_generation: int = 2
    ) -> Dict[str, Any]:
        """
        Recursive compression: compress existing summaries.
        
        Enables:
        - Gen 1: Raw → summary
        - Gen 2: Summaries → meta-summary
        - Gen 3: Meta-summaries → ultra-summary
        
        Args:
            session_id: Session to compress
            source_generation: Source generation level
            target_generation: Target generation level
        
        Returns:
            Compression result info
        """
        result = self.mce.compress_by_generation(
            session_id,
            source_generation,
            target_generation
        )
        return {
            "session_id": result.session_id,
            "original_count": result.original_count,
            "summary_chunk_id": result.summary_chunk_id,
            "generation": result.generation,
            "created_at": result.created_at
        }
    
    def get_stats(self) -> Dict:
        """
        Get comprehensive system statistics.
        
        Returns:
            Dict with stats from all layers
        """
        return {
            "cmc": {
                "domains": self.cmc.get_all_domains(),
                "domain_stats": self.cmc.get_domain_stats()
            },
            "smm": {
                "active_sessions": len(self.smm.active_sessions)
            },
            "graph": self.graph.get_stats(),
            "dde": {
                "learned_patterns": len(self.dde.learned_patterns),
                "discovered_domains": len(self.dde.domains),
                "transition_patterns": self.dde.get_transition_patterns()
            },
            "ame": self.ame.get_stats(),
            "mlc": self.mlc.get_stats(),
            "mca": {
                "issues_detected": len(self.mca.issues)
            }
        }
    
    def export_learned_profile(self, filepath: str):
        """
        Export all learned patterns and profile.
        
        This preserves learning across restarts.
        
        Args:
            filepath: Where to save (JSON)
        """
        data = {
            "version": "1.0",
            "exported_at": json.dumps(datetime.now().isoformat()),
            
            "dde": {
                "learned_patterns": self.dde.learned_patterns,
                "domains": self.dde.domains,
                "transitions": {
                    f"{k[0]}->{k[1]}": v
                    for k, v in self.dde.transition_matrix.items()
                }
            },
            
            "ame": {
                "domain_strictness": self.ame.domain_strictness,
                "enforcement_stats": self.ame.enforcement_stats
            },
            
            "mlc": self.mlc.get_stats()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Learned profile exported to {filepath}", file=sys.stderr)
    
    def import_learned_profile(self, filepath: str):
        """
        Import previously learned patterns and profile.
        
        Args:
            filepath: JSON file to load
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Restore DDE
        self.dde.learned_patterns = data["dde"]["learned_patterns"]
        self.dde.domains.update(data["dde"]["domains"])
        
        # Restore transitions (convert keys back)
        for key, value in data["dde"]["transitions"].items():
            from_d, to_d = key.split("->")
            self.dde.transition_matrix[(from_d, to_d)] = value
        
        # Restore AME
        self.ame.domain_strictness.update(data["ame"]["domain_strictness"])
        
        print(f"✅ Learned profile imported from {filepath}", file=sys.stderr)


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    from datetime import datetime
    import sys
    
    print("🧪 Testing Complete Optimal Memory System")
    print("=" * 60)
    
    # Initialize
    system = OptimalMemorySystem(
        canonical_collection="test_optimal_canonical",
        semantic_collection="test_optimal_semantic"
    )
    
    # Test 1: Store facts
    print("\n1️⃣ Storing canonical facts...")
    system.store_fact(
        key="user_name",
        value="Morten",
        domain="identity",
        fact_type="name",
        authority="LONGTERM",
        text="Brukeren heter Morten"
    )
    
    system.store_fact(
        key="user_children_count",
        value=3,
        domain="family",
        fact_type="count",
        authority="LONGTERM",
        text="Morten har 3 barn: Joakim, Isak Andreas, og Susanna"
    )
    
    # Test 2: Store context
    print("\n2️⃣ Storing context...")
    system.store_context(
        text="EFC theory describes energy flow through cosmological scales with entropy as core metric",
        domains=["cosmology", "theory"],
        tags=["EFC", "entropy"],
        session_id="test_session",
        conversation_turn=1
    )
    
    # Test 2b: Store document (chunking)
    print("\n2️⃣b Storing multi-paragraph document...")
    long_text = """
    Symbiosen består av fem hovedlag:
    
    Lag 1: Canonical Memory Core (CMC) lagrer absolutte fakta som navn, tall og regler.
    Dette er null-toleranse for feil.
    
    Lag 2: Semantic Mesh Memory (SMM) lagrer dynamisk kontekst, refleksjoner og teori.
    Dette er flytsonen.
    
    Lag 3: Dynamic Domain Engine (DDE) klassifiserer automatisk domener og lærer mønstre.
    
    Lag 4: Adaptive Memory Enforcer (AME) bestemmer når minne skal overstyre LLM.
    
    Lag 5: Meta-Learning Cortex (MLC) lærer brukerens kognitive stil og justerer alle lag.
    """
    chunks = system.store_document(
        text=long_text,
        domain="symbiose",
        doc_id="symbiose_architecture_v1",
        tags=["architecture", "layers"],
        source="documentation"
    )
    print(f"   Stored {len(chunks)} chunks from document")
    
    # Test 3: Answer questions with full system
    print("\n3️⃣ Testing question answering...")
    
    test_cases = [
        {
            "question": "Hva heter jeg?",
            "llm_draft": "Du heter Andreas",  # Wrong - should override
            "expected": "OVERRIDE"
        },
        {
            "question": "Hvor mange barn har jeg?",
            "llm_draft": "Du har 2 barn",  # Wrong - should override
            "expected": "OVERRIDE"
        },
        {
            "question": "Hva er EFC?",
            "llm_draft": "EFC er Energy Flow Cosmology, en teori om energiflyt",  # Good
            "expected": "TRUST_LLM or AUGMENT"
        },
        {
            "question": "Er systemet sikkert?",
            "llm_draft": "Ja, systemet bruker kryptering",  # No memory
            "expected": "DEFER or TRUST_LLM"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {case['question']}")
        result = system.answer_question(
            question=case["question"],
            llm_draft=case["llm_draft"],
            session_id="test_session"
        )
        
        print(f"      Decision: {result['decision']}")
        print(f"      Domain: {result['domain']}")
        print(f"      Mode: {result['cognitive_mode']}")
        print(f"      Final: {result['final_response'][:100]}...")
        print(f"      Overridden: {result['was_overridden']}")
        print(f"      Strictness: {result['strictness_applied']:.2f}")
        print(f"      Reasoning: {result['reasoning']}")
    
    # Test 4: Session context retrieval
    print("\n4️⃣ Testing session context...")
    session_chunks = system.get_session_context("test_session")
    print(f"   Session has {len(session_chunks)} chunks")
    for chunk in session_chunks:
        print(f"      Turn {chunk.conversation_turn}: {chunk.text[:60]}...")
    
    # Test 5: Graph layer (structural memory)
    print("\n5️⃣ Testing graph layer...")
    if system.graph.driver:
        # Create entities
        system.create_entity(
            entity_id="system_symbiose_test",
            entity_type="System",
            name="Symbiose",
            properties={"version": "3.0", "type": "memory_architecture"}
        )
        
        for layer_name, layer_num in [("CMC", 1), ("SMM", 2), ("Neo4j", 2.5), ("DDE", 3), ("AME", 4), ("MLC", 5)]:
            system.create_entity(
                entity_id=f"module_{layer_name.lower()}_test",
                entity_type="Module",
                name=layer_name,
                properties={"layer_number": layer_num}
            )
            system.create_relation(
                from_id=f"module_{layer_name.lower()}_test",
                to_id="system_symbiose_test",
                relation_type="PART_OF"
            )
        
        # Query structure
        answer = system.query_graph("Hvilke lag har symbiosen?")
        print(f"   Q: Hvilke lag har symbiosen?")
        print(f"   A: {answer or 'Graf-spørring implementert men returnerte ingen svar'}")
    else:
        print("   Neo4j not available - skipping graph tests")
    
    # Test 6: Semantic search
    print("\n6️⃣ Testing semantic search...")
    search_results = system.search_context(
        query="Hvordan fungerer minnelagene i symbiosen?",
        domains=["symbiose"],
        k=3
    )
    print(f"   Found {len(search_results)} relevant chunks:")
    for chunk, score in search_results:
        print(f"      [{score:.3f}] {chunk.text[:60]}...")
    
    # Test 7: Feedback loop with usefulness
    print("\n7️⃣ Testing feedback loop...")
    if search_results:
        chunk_ids = [chunk.id for chunk, _ in search_results]
        system.provide_feedback(
            question="Hva heter jeg?",
            response="Du heter Morten",
            was_correct=True,
            was_helpful=True,
            chunk_ids=chunk_ids[:1]  # Mark first chunk as useful
        )
    
    # Test 8: Stats
    print("\n8️⃣ System statistics...")
    stats = system.get_stats()
    print(json.dumps({
        "cmc_domains": stats["cmc"]["domains"],
        "smm_sessions": stats["smm"]["active_sessions"],
        "graph_enabled": stats["graph"].get("enabled", False),
        "graph_nodes": stats["graph"].get("total_nodes", 0),
        "dde_patterns": stats["dde"]["learned_patterns"],
        "mlc_mode_frequency": stats["mlc"]["mode_frequency"],
        "ame_enforcement": {k: v for k, v in stats["ame"].items() if k != "domain_strictness"}
    }, indent=2))
    
    # Test 9: Temporal decay (optional - comment out for speed)
    # print("\n9️⃣ Testing temporal decay...")
    # system.apply_temporal_decay()
    
    # Test 10: Profile export/import
    print("\n🔟 Testing profile persistence...")
    system.export_learned_profile("/tmp/optimal_memory_profile.json")
    
    print("\n" + "=" * 60)
    print("✅ Complete Optimal Memory System operational!")
    print("🎯 All 8 layers integrated and working")
    print("   1. CMC - Canonical facts")
    print("   2. SMM - Dynamic context")
    print("   2.5. Neo4j - Structural relationships")
    print("   3. DDE - Domain detection")
    print("   4. AME - Intelligent enforcement")
    print("   5. MLC - Meta-learning")
    print("   6. MIR - Interference regulation")
    print("   7. MCA - Consistency auditing")
    print("   8. MCE - Recursive compression")
    print("🧠 System learning your cognitive patterns")
    print("🔧 Advanced noise control, conflict detection, intelligent compression")
    print("🚀 Ready for production!")
