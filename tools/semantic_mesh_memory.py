#!/usr/bin/env python3
"""
semantic_mesh_memory.py - Dynamic Context Store
===============================================

LAG 2: SEMANTIC MESH MEMORY (SMM)
"Flytsonen" - alt dynamisk og kontekstuelt

This stores:
- Raw text (conversations, explanations, reflections)
- Model resonance (what worked, what didn't)
- Complex descriptions (EFC theory, Symbiose architecture)
- Long-form analysis
- Experimental ideas
- Process documentation

This is NOT authoritative - it SUPPORTS canonical facts.

This is working memory, not truth.

Architecture:
    Input → Chunk → Embed → Store → Search → Context

Purpose:
    Handle:
    - Everything too fluid for canonical storage
    - Multi-paragraph explanations
    - Theory evolution
    - Creative exploration
    - Domain-crossing synthesis
"""

import os
import sys
import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)


@dataclass
class ContextChunk:
    """
    A chunk of dynamic, contextual memory.
    
    Unlike canonical facts, these are:
    - Mutable (can be updated)
    - Contextual (tied to specific sessions/domains)
    - Temporal (may expire)
    - Fluid (not rigid structure)
    """
    
    id: str
    text: str
    embedding: List[float]
    
    # Loose classification (not rigid like CMC)
    domains: List[str] = field(default_factory=list)  # Can span multiple domains
    tags: List[str] = field(default_factory=list)
    
    # Contextual metadata
    session_id: Optional[str] = None
    conversation_turn: Optional[int] = None
    relevance_decay: float = 1.0  # Decays over time
    
    # Provenance
    source: str = "conversation"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Relations
    related_chunks: List[str] = field(default_factory=list)
    related_facts: List[str] = field(default_factory=list)  # Links to CMC
    
    # Quality metrics
    usefulness_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[str] = None


class SemanticMeshMemory:
    """
    The dynamic context store.
    
    Rules:
    1. Everything here is CONTEXTUAL (not absolute)
    2. Content can overlap domains
    3. Old chunks may decay or be pruned
    4. Links to canonical facts when relevant
    5. Optimized for semantic search, not structure
    
    This is the cortex - fluid, adaptive, creative.
    """
    
    def __init__(self, collection_name: str = "semantic_mesh"):
        self.collection_name = collection_name
        self._ensure_collection()
        
        # Session tracking
        self.active_sessions: Dict[str, List[str]] = {}
        
        # Decay settings
        self.decay_rate = 0.95  # Per day
        self.min_relevance = 0.1  # Prune below this
        
        print("✨ Semantic Mesh Memory initialized", file=sys.stderr)
        print("🌊 Dynamic context store active", file=sys.stderr)
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists."""
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
            
            # Create indexes
            for field in ["domains", "tags", "session_id", "source"]:
                try:
                    qdrant_client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema="keyword" if field != "domains" and field != "tags" else "keyword"
                    )
                except:
                    pass
    
    def _chunk_text(self, text: str, chunk_size: int = 700, chunk_overlap: int = 100) -> List[str]:
        """
        Chunk text into overlapping segments.
        
        Strategy:
        1. Split on paragraphs first
        2. For long paragraphs, use sliding window
        3. Preserve semantic boundaries
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        # Split on double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks: List[str] = []
        
        for para in paragraphs:
            if len(para) <= chunk_size:
                chunks.append(para)
            else:
                # Sliding window for long paragraphs
                start = 0
                while start < len(para):
                    end = min(len(para), start + chunk_size)
                    chunk = para[start:end]
                    chunks.append(chunk.strip())
                    
                    if end == len(para):
                        break
                    
                    start = end - chunk_overlap
        
        return chunks
    
    def add_document(
        self,
        text: str,
        domain: Optional[str] = None,
        doc_id: Optional[str] = None,
        source: str = "user",
        tags: Optional[List[str]] = None,
        canonical_links: Optional[List[str]] = None
    ) -> List[ContextChunk]:
        """
        Store a full document with automatic chunking.
        
        This is for:
        - Long documentation
        - Theory papers
        - Architecture descriptions
        - Meeting notes
        - Research logs
        
        Args:
            text: Full document text
            domain: Primary domain
            doc_id: Document identifier
            source: Origin
            tags: Semantic tags
            canonical_links: Links to CMC facts
        
        Returns:
            List of created ContextChunks
        """
        if tags is None:
            tags = []
        if canonical_links is None:
            canonical_links = []
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        # Chunk the text
        chunk_texts = self._chunk_text(text)
        
        # Store each chunk
        chunks: List[ContextChunk] = []
        for i, chunk_text in enumerate(chunk_texts):
            chunk = self.store_chunk(
                text=chunk_text,
                domains=[domain] if domain else [],
                tags=tags,
                source=source,
                related_facts=canonical_links
            )
            chunks.append(chunk)
        
        print(f"✅ Stored document as {len(chunks)} chunks [doc_id: {doc_id}]", file=sys.stderr)
        
        return chunks
    
    def store_chunk(
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
        Store a dynamic context chunk.
        
        Args:
            text: The actual content
            domains: Loose domain tags (can overlap)
            tags: Semantic tags
            session_id: Related session
            conversation_turn: Position in conversation
            source: Where it came from
            related_facts: Links to canonical facts
        
        Returns:
            The stored ContextChunk
        """
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        embedding = embedding_response.data[0].embedding
        
        # Create chunk
        chunk = ContextChunk(
            id=str(uuid.uuid4()),
            text=text,
            embedding=embedding,
            domains=domains or [],
            tags=tags or [],
            session_id=session_id,
            conversation_turn=conversation_turn,
            source=source,
            related_facts=related_facts or []
        )
        
        # Store in Qdrant
        point = PointStruct(
            id=chunk.id,
            vector=embedding,
            payload={
                "text": text,
                "domains": domains or [],
                "tags": tags or [],
                "session_id": session_id,
                "conversation_turn": conversation_turn,
                "source": source,
                "relevance_decay": chunk.relevance_decay,
                "usefulness_score": chunk.usefulness_score,
                "timestamp": chunk.timestamp,
                "related_facts": related_facts or []
            }
        )
        
        qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        # Track session
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = []
            self.active_sessions[session_id].append(chunk.id)
        
        print(f"✅ Stored context chunk: {text[:50]}... [domains: {domains}]", file=sys.stderr)
        
        return chunk
    
    def search_context(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        k: int = 10,
        include_decay: bool = True
    ) -> List[tuple[ContextChunk, float]]:
        """
        Semantic search for context.
        
        Returns: List of (chunk, score) tuples
        """
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # Build filter
        filter_conditions = []
        
        if domains:
            # Match any of the provided domains
            for domain in domains:
                filter_conditions.append(
                    FieldCondition(key="domains", match=MatchValue(value=domain))
                )
        
        if session_id:
            filter_conditions.append(
                FieldCondition(key="session_id", match=MatchValue(value=session_id))
            )
        
        # Search
        results = qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=k * 2  # Get more, then filter by decay
        )
        
        # Convert to chunks with adjusted scores
        chunks_with_scores = []
        for hit in results:
            chunk = ContextChunk(
                id=hit.id,
                text=hit.payload["text"],
                embedding=[],  # Don't load full embedding
                domains=hit.payload.get("domains", []),
                tags=hit.payload.get("tags", []),
                session_id=hit.payload.get("session_id"),
                conversation_turn=hit.payload.get("conversation_turn"),
                source=hit.payload.get("source", "conversation"),
                relevance_decay=hit.payload.get("relevance_decay", 1.0),
                usefulness_score=hit.payload.get("usefulness_score", 0.5),
                timestamp=hit.payload.get("timestamp")
            )
            
            # Adjust score by decay if enabled
            score = hit.score
            if include_decay:
                score *= chunk.relevance_decay
            
            chunks_with_scores.append((chunk, score))
        
        # Sort by adjusted score
        chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return chunks_with_scores[:k]
    
    def get_session_context(self, session_id: str, k: int = 20) -> List[ContextChunk]:
        """
        Get all context from a specific session.
        
        This is for conversation continuity.
        """
        if session_id not in self.active_sessions:
            return []
        
        chunk_ids = self.active_sessions[session_id][-k:]  # Last k chunks
        
        results = qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=chunk_ids
        )
        
        chunks = []
        for hit in results:
            chunk = ContextChunk(
                id=hit.id,
                text=hit.payload["text"],
                embedding=[],
                domains=hit.payload.get("domains", []),
                tags=hit.payload.get("tags", []),
                session_id=hit.payload.get("session_id"),
                conversation_turn=hit.payload.get("conversation_turn"),
                timestamp=hit.payload.get("timestamp")
            )
            chunks.append(chunk)
        
        # Sort by conversation turn
        chunks.sort(key=lambda c: c.conversation_turn or 0)
        
        return chunks
    
    def update_usefulness(self, chunk_id: str, useful: bool):
        """
        Update usefulness score (feedback loop).
        
        This affects future retrieval ranking.
        """
        # Retrieve current
        result = qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=[chunk_id]
        )
        
        if not result:
            return
        
        hit = result[0]
        current_score = hit.payload.get("usefulness_score", 0.5)
        
        # Update score
        if useful:
            new_score = min(1.0, current_score + 0.1)
        else:
            new_score = max(0.0, current_score - 0.1)
        
        # Persist
        qdrant_client.set_payload(
            collection_name=self.collection_name,
            payload={
                "usefulness_score": new_score,
                "last_accessed": datetime.now().isoformat()
            },
            points=[chunk_id]
        )
        
        print(f"✅ Updated chunk usefulness: {new_score:.2f}", file=sys.stderr)
    
    def apply_temporal_decay(self):
        """
        Apply time-based relevance decay to all chunks.
        
        This should run periodically (e.g., daily).
        """
        # Get all chunks
        offset = None
        updated = 0
        pruned = 0
        
        while True:
            batch, offset = qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset
            )
            
            if not batch:
                break
            
            for hit in batch:
                current_decay = hit.payload.get("relevance_decay", 1.0)
                new_decay = current_decay * self.decay_rate
                
                if new_decay < self.min_relevance:
                    # Prune
                    qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=[hit.id]
                    )
                    pruned += 1
                else:
                    # Update decay
                    qdrant_client.set_payload(
                        collection_name=self.collection_name,
                        payload={"relevance_decay": new_decay},
                        points=[hit.id]
                    )
                    updated += 1
            
            if offset is None:
                break
        
        print(f"🧹 Temporal decay applied: {updated} updated, {pruned} pruned", file=sys.stderr)
    
    def link_to_fact(self, chunk_id: str, fact_id: str):
        """
        Link a context chunk to a canonical fact.
        
        This creates bidirectional traceability.
        """
        result = qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=[chunk_id]
        )
        
        if not result:
            return
        
        hit = result[0]
        related_facts = hit.payload.get("related_facts", [])
        
        if fact_id not in related_facts:
            related_facts.append(fact_id)
            
            qdrant_client.set_payload(
                collection_name=self.collection_name,
                payload={"related_facts": related_facts},
                points=[chunk_id]
            )
            
            print(f"🔗 Linked chunk to fact {fact_id}", file=sys.stderr)
    
    def prune_old_conversations(self, days_threshold: int = 180) -> Dict[str, int]:
        """
        Prune conversations older than threshold.
        
        This removes entire sessions that haven't been accessed recently.
        Prevents unbounded growth of conversation history.
        
        Args:
            days_threshold: Remove conversations older than this many days
        
        Returns:
            Dict with counts of pruned chunks by session
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        cutoff_iso = cutoff_date.isoformat()
        
        print(f"🧹 Pruning conversations older than {days_threshold} days (before {cutoff_iso[:10]})", file=sys.stderr)
        
        # Get all chunks with timestamps
        offset = None
        sessions_to_prune: Dict[str, List[str]] = {}
        
        while True:
            batch, offset = qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            if not batch:
                break
            
            for hit in batch:
                timestamp = hit.payload.get("timestamp")
                session_id = hit.payload.get("session_id")
                last_accessed = hit.payload.get("last_accessed")
                
                # Use last_accessed if available, otherwise timestamp
                check_date = last_accessed or timestamp
                
                if check_date and check_date < cutoff_iso:
                    if session_id:
                        if session_id not in sessions_to_prune:
                            sessions_to_prune[session_id] = []
                        sessions_to_prune[session_id].append(hit.id)
                    else:
                        # Orphan chunk without session
                        if "orphans" not in sessions_to_prune:
                            sessions_to_prune["orphans"] = []
                        sessions_to_prune["orphans"].append(hit.id)
            
            if offset is None:
                break
        
        # Delete old chunks
        total_pruned = 0
        session_counts = {}
        
        for session_id, chunk_ids in sessions_to_prune.items():
            qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=chunk_ids
            )
            
            # Clean up active_sessions tracking
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            session_counts[session_id] = len(chunk_ids)
            total_pruned += len(chunk_ids)
            
            print(f"  🗑️  Session '{session_id}': removed {len(chunk_ids)} chunks", file=sys.stderr)
        
        print(f"✅ Pruned {total_pruned} chunks from {len(sessions_to_prune)} old sessions", file=sys.stderr)
        
        return session_counts
    
    def decay_unused_facts(self, usage_threshold: int = 30) -> Dict[str, int]:
        """
        Decay facts that haven't been accessed in threshold days.
        
        This gradually reduces relevance of unused content without immediate deletion.
        Allows natural "forgetting" of rarely-used information.
        
        Args:
            usage_threshold: Consider unused if not accessed in this many days
        
        Returns:
            Dict with counts: {'decayed': X, 'pruned': Y, 'kept': Z}
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=usage_threshold)
        cutoff_iso = cutoff_date.isoformat()
        
        print(f"📉 Decaying facts unused for {usage_threshold} days (since {cutoff_iso[:10]})", file=sys.stderr)
        
        offset = None
        counts = {"decayed": 0, "pruned": 0, "kept": 0}
        
        while True:
            batch, offset = qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            if not batch:
                break
            
            for hit in batch:
                last_accessed = hit.payload.get("last_accessed")
                timestamp = hit.payload.get("timestamp")
                current_decay = hit.payload.get("relevance_decay", 1.0)
                
                # Use last_accessed if available, otherwise timestamp
                check_date = last_accessed or timestamp
                
                if check_date and check_date < cutoff_iso:
                    # Apply aggressive decay for unused content
                    new_decay = current_decay * 0.8  # 20% reduction
                    
                    if new_decay < self.min_relevance:
                        # Prune if below threshold
                        qdrant_client.delete(
                            collection_name=self.collection_name,
                            points_selector=[hit.id]
                        )
                        counts["pruned"] += 1
                    else:
                        # Update decay
                        qdrant_client.set_payload(
                            collection_name=self.collection_name,
                            payload={"relevance_decay": new_decay},
                            points=[hit.id]
                        )
                        counts["decayed"] += 1
                else:
                    counts["kept"] += 1
            
            if offset is None:
                break
        
        print(f"✅ Decay results: {counts['decayed']} decayed, {counts['pruned']} pruned, {counts['kept']} kept", file=sys.stderr)
        
        return counts


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Semantic Mesh Memory")
    print("=" * 60)
    
    # Initialize
    smm = SemanticMeshMemory()
    
    # Test 1: Store conversation chunks
    print("\n1️⃣ Storing conversation chunks...")
    smm.store_chunk(
        text="EFC theory describes energy flow through scales in cosmology",
        domains=["cosmology", "theory"],
        tags=["EFC", "scale_invariance"],
        session_id="test_session_1",
        conversation_turn=1
    )
    
    smm.store_chunk(
        text="Symbiose architecture enables parallel multi-domain reasoning",
        domains=["tech", "meta"],
        tags=["symbiose", "architecture"],
        session_id="test_session_1",
        conversation_turn=2
    )
    
    smm.store_chunk(
        text="User prefers high precision with zero friction between domains",
        domains=["meta", "operational"],
        tags=["user_preference", "cognitive_style"],
        session_id="test_session_1",
        conversation_turn=3
    )
    
    # Test 2: Semantic search
    print("\n2️⃣ Semantic search...")
    results = smm.search_context("How does EFC work?", domains=["cosmology"])
    print(f"   Found {len(results)} chunks:")
    for chunk, score in results:
        print(f"     - [{score:.3f}] {chunk.text[:60]}...")
    
    # Test 3: Session context
    print("\n3️⃣ Session context retrieval...")
    session_chunks = smm.get_session_context("test_session_1")
    print(f"   Session has {len(session_chunks)} chunks (in order):")
    for chunk in session_chunks:
        print(f"     {chunk.conversation_turn}: {chunk.text[:50]}...")
    
    # Test 4: Usefulness feedback
    print("\n4️⃣ Testing usefulness feedback...")
    if results:
        chunk_id = results[0][0].id
        smm.update_usefulness(chunk_id, useful=True)
    
    print("\n" + "=" * 60)
    print("✅ Semantic Mesh Memory operational!")
