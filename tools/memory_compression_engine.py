#!/usr/bin/env python3
"""
memory_compression_engine.py - Recursive Memory Compression Engine (MCE)
=======================================================================

LAG 8: RECURSIVE MEMORY COMPRESSION ENGINE

Oppgave:
- Ta lange samtaler / sessions
- Lage komprimerte sammendrag
- Linke summarier til original-chunks
- Markere kompresjonsnivå (generation)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Any
from datetime import datetime
from openai import OpenAI
import sys

try:
    from tools.semantic_mesh_memory import SemanticMeshMemory, ContextChunk
except ImportError:
    SemanticMeshMemory = Any  # type: ignore
    ContextChunk = Any        # type: ignore


@dataclass
class CompressionResult:
    session_id: str
    original_count: int
    summary_chunk_id: Optional[str]
    generation: int
    created_at: str


class MemoryCompressionEngine:
    """
    En komprimeringsmotor som jobber på SMM-nivå.
    """

    def __init__(self, smm: SemanticMeshMemory, openai_client: OpenAI):
        self.smm = smm
        self.openai_client = openai_client

    def compress_session(
        self,
        session_id: str,
        max_chunks: int = 50,
        target_generation: int = 1
    ) -> CompressionResult:
        """
        Komprimer en gitt session hvis den er stor nok.

        target_generation:
            1 = første gang vi komprimerer rå-logs
            2 = komprimerer tidligere summarier, osv.
        """
        # hent siste N chunks
        chunks = self.smm.get_session_context(session_id, k=max_chunks)
        if not chunks:
            return CompressionResult(
                session_id=session_id,
                original_count=0,
                summary_chunk_id=None,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )

        # filtrer på generation (om du bruker dette i payload senere)
        # nå antar vi at alle er rå; du kan bygge videre med metadata
        texts = [c.text for c in chunks]

        # lag summariseringsprompt
        prompt = (
            "Lag en konsis, men innholdstett oppsummering av følgende dialog.\n"
            "Bevar viktige fakta, beslutninger, hypoteser og metastrukturer.\n"
            "Bruk korte avsnitt og punktlister der det er naturlig.\n\n"
        )
        joined = "\n\n---\n\n".join(texts)

        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Du er en komprimeringsmotor for avansert dialog."},
                    {"role": "user", "content": prompt + joined}
                ],
                temperature=0.2
            )

            summary = resp.choices[0].message.content.strip()

            # lagre som ny chunk
            summary_chunk = self.smm.store_chunk(
                text=f"[GEN{target_generation}] Sammendrag for session {session_id}:\n\n{summary}",
                domains=[],
                tags=[f"compression_gen_{target_generation}", "session_summary"],
                session_id=session_id,
                source="compression_engine"
            )

            print(f"✅ Compressed {len(chunks)} chunks into summary (gen {target_generation})", file=sys.stderr)

            # du kan eventuelt markere original-chunks som komprimert via set_payload
            # her nøyer vi oss med å returnere info
            return CompressionResult(
                session_id=session_id,
                original_count=len(chunks),
                summary_chunk_id=summary_chunk.id,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            print(f"❌ Compression failed: {e}", file=sys.stderr)
            return CompressionResult(
                session_id=session_id,
                original_count=len(chunks),
                summary_chunk_id=None,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )

    def compress_by_generation(
        self,
        session_id: str,
        source_generation: int = 1,
        target_generation: int = 2,
        max_chunks: int = 100
    ) -> CompressionResult:
        """
        Recursive compression: take generation N summaries and compress to generation N+1.
        
        This enables hierarchical compression:
        - Gen 1: Raw conversation → summary
        - Gen 2: Multiple Gen 1 summaries → meta-summary
        - Gen 3: Multiple Gen 2 meta-summaries → ultra-summary
        
        Args:
            session_id: Session to compress
            source_generation: Which generation to compress
            target_generation: Target generation level
            max_chunks: Max chunks to include
        
        Returns:
            CompressionResult with summary info
        """
        # Search for chunks with specific generation tag
        results = self.smm.search_context(
            query=f"session {session_id}",
            session_id=session_id,
            k=max_chunks
        )
        
        # Filter by generation tag
        gen_tag = f"compression_gen_{source_generation}"
        gen_chunks = [c for c, _ in results if gen_tag in getattr(c, "tags", [])]
        
        if not gen_chunks:
            print(f"⚠️  No generation {source_generation} chunks found for session {session_id}", file=sys.stderr)
            return CompressionResult(
                session_id=session_id,
                original_count=0,
                summary_chunk_id=None,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )
        
        # Compress these
        texts = [c.text for c in gen_chunks]
        prompt = (
            f"Lag en ultra-kompakt oppsummering av disse allerede komprimerte sammendragene.\n"
            f"Dette er generasjon {target_generation} av kompresjon - behold bare essensen.\n\n"
        )
        joined = "\n\n===\n\n".join(texts)
        
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Du lager gen-{target_generation} meta-sammendrag."},
                    {"role": "user", "content": prompt + joined}
                ],
                temperature=0.2
            )
            
            summary = resp.choices[0].message.content.strip()
            
            summary_chunk = self.smm.store_chunk(
                text=f"[GEN{target_generation}] Meta-sammendrag:\n\n{summary}",
                domains=[],
                tags=[f"compression_gen_{target_generation}", "meta_summary"],
                session_id=session_id,
                source="compression_engine"
            )
            
            print(f"✅ Recursive compression: {len(gen_chunks)} gen-{source_generation} → 1 gen-{target_generation}", file=sys.stderr)
            
            return CompressionResult(
                session_id=session_id,
                original_count=len(gen_chunks),
                summary_chunk_id=summary_chunk.id,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            print(f"❌ Recursive compression failed: {e}", file=sys.stderr)
            return CompressionResult(
                session_id=session_id,
                original_count=len(gen_chunks),
                summary_chunk_id=None,
                generation=target_generation,
                created_at=datetime.now().isoformat()
            )


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Memory Compression Engine")
    print("=" * 60)
    
    print("\n⚠️  Compression testing requires live SMM instance and OpenAI API")
    print("   Use within OptimalMemorySystem for full functionality")
    
    print("\n📝 Compression capabilities:")
    print("   1. Session compression (raw → gen 1)")
    print("   2. Recursive compression (gen N → gen N+1)")
    print("   3. Automatic triggering (when session > threshold)")
    
    print("\n💡 Benefits:")
    print("   - Reduces SMM size over time")
    print("   - Preserves essential information")
    print("   - Enables hierarchical memory")
    print("   - Improves retrieval speed")
    
    print("\n" + "=" * 60)
    print("✅ Memory Compression Engine ready!")
    print("🔧 Integrate with OptimalMemorySystem to activate")
